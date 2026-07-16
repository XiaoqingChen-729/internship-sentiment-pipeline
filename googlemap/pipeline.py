import os
import psycopg2
from dotenv import load_dotenv
from google_play_scraper import reviews, Sort
import time

load_dotenv()

start_time = time.time()

# Database connection
def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

# Quality flag logic
def get_quality_flags(content):
    flags = []
    if not content or len(content.strip()) < 20:
        flags.append(('low_signal', 'Review under 20 characters'))
    if content:
        ascii_count = sum(1 for c in content if ord(c) < 128)
        if len(content) > 0 and ascii_count / len(content) < 0.8:
            flags.append(('non_english', 'Less than 80% ASCII characters'))
    return flags

# Insert category
def get_or_create_category(cur, name):
    cur.execute("SELECT id FROM category WHERE name = %s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO category (name) VALUES (%s) RETURNING id", (name,))
    return cur.fetchone()[0]

# Insert app
def get_or_create_app(cur, name, app_store_id, category_id):
    cur.execute("SELECT id FROM app WHERE app_store_id = %s", (app_store_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO app (name, app_store_id, category_id) VALUES (%s, %s, %s) RETURNING id",
        (name, app_store_id, category_id)
    )
    return cur.fetchone()[0]

# Insert ingestion run
def create_ingestion_run(cur, app_id, count, status):
    cur.execute(
        "INSERT INTO ingestion_run (app_id, count, status) VALUES (%s, %s, %s) RETURNING id",
        (app_id, count, status)
    )
    return cur.fetchone()[0]

# Insert reviews
def insert_reviews(cur, result, ingestion_run_id):
    inserted = 0
    duplicate = 0
    flag_count = 0
    seen_content = set()

    for r in result:
        review_id = r.get('reviewId', '')
        content = r.get('content') or ''

        cur.execute("SELECT review_id FROM raw_review WHERE review_id = %s", (review_id,))
        if cur.fetchone():
            duplicate += 1
            continue

        cur.execute("""
            INSERT INTO raw_review (
                review_id, ingestion_run_id, user_name, content,
                score, reviewed_at, app_version, thumbs_up_count, reply_content
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            review_id,
            ingestion_run_id,
            r.get('userName', ''),
            content,
            r.get('score'),
            r.get('at'),
            r.get('appVersion'),
            r.get('thumbsUpCount', 0),
            r.get('replyContent')
        ))

        flags = get_quality_flags(content)

        is_content_duplicate = content in seen_content
        if is_content_duplicate:
            flags.append(('duplicate', 'Identical content already seen in this run'))

        seen_content.add(content)

        for flag_type, reason in flags:
            cur.execute("""
                INSERT INTO quality_flag (review_id, flag_type, reason)
                VALUES (%s, %s, %s)
            """, (review_id, flag_type, reason))
            flag_count += 1

        is_english = sum(1 for c in content if ord(c) < 128) / max(len(content), 1) >= 0.8
        low_signal = len(content.strip()) < 20

        cur.execute("""
            INSERT INTO cleaned_review (
                review_id, cleaned_content, language,
                low_signal, is_duplicate, is_english
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            review_id,
            content.strip(),
            'en' if is_english else 'other',
            low_signal,
            is_content_duplicate,
            is_english
        ))

        inserted += 1

    return inserted, duplicate, flag_count

# Main pipeline
apps = [
    {'id': 'com.openai.chatgpt',                'name': 'ChatGPT',          'category': 'AI'},
    {'id': 'com.instagram.android',             'name': 'Instagram',        'category': 'Social'},
    {'id': 'com.zhiliaoapp.musically',          'name': 'TikTok',           'category': 'Short Video'},
    {'id': 'com.lemon.lvoverseas',              'name': 'CapCut',           'category': 'Video Editing'},
    {'id': 'com.whatsapp',                      'name': 'WhatsApp',         'category': 'Communication'},
    {'id': 'com.facebook.katana',               'name': 'Facebook',         'category': 'Social'},
    {'id': 'com.spotify.music',                 'name': 'Spotify',          'category': 'Music'},
    {'id': 'com.einnovation.temu',              'name': 'Temu',             'category': 'Shopping'},
    {'id': 'com.snapchat.android',              'name': 'Snapchat',         'category': 'Social'},
    {'id': 'org.telegram.messenger',            'name': 'Telegram',         'category': 'Communication'},
    {'id': 'com.netflix.mediaclient',           'name': 'Netflix',          'category': 'Streaming'},
    {'id': 'com.duolingo',                      'name': 'Duolingo',         'category': 'Education'},
    {'id': 'com.google.android.apps.maps',      'name': 'Google Maps',      'category': 'Navigation'},
    {'id': 'com.ubercab',                       'name': 'Uber',             'category': 'Ride-hailing'},
    {'id': 'com.dd.doordash',                   'name': 'DoorDash',         'category': 'Food Delivery'},
    {'id': 'com.google.android.apps.bard',      'name': 'Google Gemini',    'category': 'AI'},
    {'id': 'com.amazon.mShop.android.shopping', 'name': 'Amazon Shopping',  'category': 'E-commerce'},
    {'id': 'com.mcdonalds.app',                 'name': 'McDonalds',        'category': 'Food & Drink'},
    {'id': 'com.linkedin.android',              'name': 'LinkedIn',         'category': 'Professional'},
    {'id': 'com.airbnb.android',                'name': 'Airbnb',           'category': 'Travel'},
]

conn = get_connection()
cur = conn.cursor()

app_report = []
total_inserted = 0
total_skipped = 0
total_flags = 0

for app in apps:
    print(f"Processing: {app['name']}...")
    report = {
        'app': app['name'],
        'fetched': 0,
        'inserted': 0,
        'skipped': 0,
        'flags': 0,
        'status': 'success'
    }

    try:
        result, _ = reviews(
            app['id'],
            lang='en',
            country='us',
            sort=Sort.NEWEST,
            count=1000
        )
        report['fetched'] = len(result)
        report['status'] = 'success'
    except Exception as e:
        print(f"  Failed to fetch: {e}")
        report['status'] = 'failed'
        result = []

    category_id = get_or_create_category(cur, app['category'])
    app_id = get_or_create_app(cur, app['name'], app['id'], category_id)
    run_start = time.time()
    run_id = create_ingestion_run(cur, app_id, len(result), report['status'])

    if result:
        inserted, skipped, flags = insert_reviews(cur, result, run_id)
        report['inserted'] = inserted
        report['skipped'] = skipped
        report['flags'] = flags
        total_inserted += inserted
        total_skipped += skipped
        total_flags += flags
        print(f"  Fetched: {report['fetched']} | Inserted: {inserted} | Skipped: {skipped} | Flags: {flags}")

    run_end = time.time()
    cur.execute("""
        UPDATE ingestion_run 
        SET finished_at = run_at + interval '1 second' * %s
        WHERE id = %s
    """, (round(run_end - run_start), run_id))
    conn.commit()
    app_report.append(report)
    time.sleep(1)
    conn.commit()
    app_report.append(report)
    time.sleep(1)

# Summary report
elapsed = time.time() - start_time

print("\n" + "=" * 60)
print("PIPELINE SUMMARY")
print("=" * 60)
print(f"Total fetched  : {sum(r['fetched'] for r in app_report):,}")
print(f"Total inserted : {total_inserted:,}")
print(f"Total skipped  : {total_skipped:,}")
print(f"Total flags    : {total_flags:,}")
print(f"Runtime        : {elapsed:.1f} seconds")

print("\nQuality flags by type:")
cur.execute("""
    SELECT flag_type, COUNT(*) 
    FROM quality_flag 
    GROUP BY flag_type 
    ORDER BY COUNT(*) DESC
""")
for flag_type, count in cur.fetchall():
    print(f"  {flag_type}: {count:,}")

print("\nFailed apps:")
failed = [r for r in app_report if r['status'] == 'failed']
if failed:
    for r in failed:
        print(f"  {r['app']}")
else:
    print("  None")

print("\nTable validation:")
cur.execute("SELECT COUNT(*) FROM raw_review")
raw_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM cleaned_review")
cleaned_count = cur.fetchone()[0]
cur.execute("""
    SELECT COUNT(*) FROM raw_review r
    LEFT JOIN ingestion_run i ON r.ingestion_run_id = i.id
    WHERE i.id IS NULL
""")
orphan_count = cur.fetchone()[0]
print(f"  raw_review count     : {raw_count:,}")
print(f"  cleaned_review count : {cleaned_count:,}")
print(f"  raw == cleaned       : {raw_count == cleaned_count}")
print(f"  orphan reviews       : {orphan_count}")

print("\nPer-app report:")
print(f"  {'App':<20} {'Fetched':>8} {'Inserted':>9} {'Skipped':>8} {'Flags':>6} {'Status':>8}")
print(f"  {'-'*20} {'-'*8} {'-'*9} {'-'*8} {'-'*6} {'-'*8}")
for r in app_report:
    print(f"  {r['app']:<20} {r['fetched']:>8} {r['inserted']:>9} {r['skipped']:>8} {r['flags']:>6} {r['status']:>8}")

cur.close()
conn.close()
print("\nPipeline completed.")