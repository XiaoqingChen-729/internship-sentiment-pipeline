import os
import psycopg2
from dotenv import load_dotenv
from google_play_scraper import reviews, Sort
import time

load_dotenv()

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
    seen_content = set()

    for r in result:
        review_id = r.get('reviewId', '')
        content = r.get('content') or ''

        # Check duplicate review_id
        cur.execute("SELECT review_id FROM raw_review WHERE review_id = %s", (review_id,))
        if cur.fetchone():
            duplicate += 1
            continue

        # Insert raw_review
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

        # Quality flags
        flags = get_quality_flags(content)

        # Check duplicate content
        if content in seen_content:
            flags.append(('duplicate', 'Identical content already seen in this run'))
        seen_content.add(content)

        for flag_type, reason in flags:
            cur.execute("""
                INSERT INTO quality_flag (review_id, flag_type, reason)
                VALUES (%s, %s, %s)
            """, (review_id, flag_type, reason))

        # Insert cleaned_review
        is_english = sum(1 for c in content if ord(c) < 128) / max(len(content), 1) >= 0.8
        low_signal = len(content.strip()) < 20
        is_duplicate = content in seen_content

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
            is_duplicate,
            is_english
        ))

        inserted += 1

    return inserted, duplicate

# Main pipeline (choose 5 apps for testing)
apps = [
    {'id': 'com.ubercab',               'name': 'Uber',         'category': 'Ride-hailing'},
    {'id': 'com.dd.doordash',           'name': 'DoorDash',     'category': 'Food Delivery'},
    {'id': 'com.spotify.music',         'name': 'Spotify',      'category': 'Music'},
    {'id': 'com.duolingo',              'name': 'Duolingo',      'category': 'Education'},
    {'id': 'com.zhiliaoapp.musically',  'name': 'TikTok',       'category': 'Social'},
]

conn = get_connection()
cur = conn.cursor()

for app in apps:
    print(f"Processing: {app['name']}...")

    try:
        result, _ = reviews(
            app['id'],
            lang='en',
            country='us',
            sort=Sort.NEWEST,
            count=100
        )
        status = 'success'
    except Exception as e:
        print(f"  Failed to fetch: {e}")
        status = 'failed'
        result = []

    category_id = get_or_create_category(cur, app['category'])
    app_id = get_or_create_app(cur, app['name'], app['id'], category_id)
    run_id = create_ingestion_run(cur, app_id, len(result), status)

    if result:
        inserted, duplicate = insert_reviews(cur, result, run_id)
        print(f"  Inserted: {inserted} | Duplicates skipped: {duplicate}")

    conn.commit()
    time.sleep(1)

cur.close()
conn.close()
print("\nPipeline complete.")