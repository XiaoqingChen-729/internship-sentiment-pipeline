import os
import psycopg2
import csv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

# ── Keyword signals ────────────────────────────────────────────
TOPIC_SIGNALS = {
    'service_signal': ['support', 'help', 'response', 'contact', 'customer service'],
    'login_signal':   ['login', 'account', 'password', 'sign in', 'access'],
    'price_signal':   ['price', 'expensive', 'free', 'premium', 'worth'],
    'refund_signal':  ['refund', 'charge', 'billing', 'subscription', 'cancel'],
    'update_signal':  ['update', 'version', 'broke', 'after update', 'new version'],
}

SENTIMENT_SIGNALS = {
    'positive_signal': ['love', 'amazing', 'perfect', 'excellent', 'great'],
    'negative_signal': ['terrible', 'awful', 'worst', 'horrible', 'useless'],
}

def match_keywords(text, keywords):
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

def get_rating_group(score):
    if score >= 4:
        return 'positive'
    elif score == 3:
        return 'neutral'
    else:
        return 'negative'

def generate_features():
    conn = get_connection()
    cur = conn.cursor()

    print("Fetching data from database...")
    cur.execute("""
        SELECT
            cr.review_id,
            a.name AS app_name,
            cat.name AS app_category,
            cr.cleaned_content,
            rr.score,
            rr.reviewed_at,
            rr.reply_content,
            cr.low_signal,
            cr.is_duplicate,
            cr.is_english
        FROM cleaned_review cr
        JOIN raw_review rr ON cr.review_id = rr.review_id
        JOIN ingestion_run ir ON rr.ingestion_run_id = ir.id
        JOIN app a ON ir.app_id = a.id
        JOIN category cat ON a.category_id = cat.id
    """)
    rows = cur.fetchall()
    print(f"Total records fetched: {len(rows):,}")

    # ── Create features table if not exists ───────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS features (
            review_id               VARCHAR(100)  PRIMARY KEY,
            app_name                VARCHAR(100)  NOT NULL,
            app_category            VARCHAR(100)  NOT NULL,
            review_length           INT,
            rating_group            VARCHAR(20),
            review_date             DATE,
            review_weekday          VARCHAR(10),
            review_month            INT,
            has_reply               BOOLEAN,
            low_signal           BOOLEAN,
            is_duplicate            BOOLEAN,
            is_english              BOOLEAN,
            service_signal          BOOLEAN,
            login_signal            BOOLEAN,
            price_signal            BOOLEAN,
            refund_signal           BOOLEAN,
            update_signal           BOOLEAN,
            positive_signal         BOOLEAN,
            negative_signal         BOOLEAN,
            feature_generated_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES cleaned_review(review_id)
        )
    """)

    # ── Clear existing features ────────────────────────────────
    cur.execute("TRUNCATE TABLE features")

    print("Generating features...")
    feature_rows = []

    for row in rows:
        review_id, app_name, app_category, content, score, reviewed_at, \
        reply_content, low_signal, is_duplicate, is_english = row

        review_length = len(content) if content else 0
        rating_group = get_rating_group(score)
        review_date = reviewed_at.date() if reviewed_at else None
        review_weekday = reviewed_at.strftime('%A') if reviewed_at else None
        review_month = reviewed_at.month if reviewed_at else None
        has_reply = reply_content is not None and len(reply_content.strip()) > 0

        topic_flags = {
            signal: match_keywords(content, keywords)
            for signal, keywords in TOPIC_SIGNALS.items()
        }
        sentiment_flags = {
            signal: match_keywords(content, keywords)
            for signal, keywords in SENTIMENT_SIGNALS.items()
        }

        feature_rows.append((
            review_id, app_name, app_category,
            review_length, rating_group,
            review_date, review_weekday, review_month,
            has_reply, low_signal, is_duplicate, is_english,
            topic_flags['service_signal'],
            topic_flags['login_signal'],
            topic_flags['price_signal'],
            topic_flags['refund_signal'],
            topic_flags['update_signal'],
            sentiment_flags['positive_signal'],
            sentiment_flags['negative_signal'],
        ))

    # ── Insert into database ───────────────────────────────────
    print("Inserting features into database...")
    cur.executemany("""
        INSERT INTO features (
            review_id, app_name, app_category,
            review_length, rating_group,
            review_date, review_weekday, review_month,
            has_reply, low_signal, is_duplicate, is_english,
            service_signal, login_signal, price_signal,
            refund_signal, update_signal,
            positive_signal, negative_signal
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, feature_rows)
    conn.commit()
    print(f"Features inserted: {len(feature_rows):,}")

    # ── Export CSV ─────────────────────────────────────────────
    fields = [
        'review_id', 'app_name', 'app_category',
        'review_length', 'rating_group',
        'review_date', 'review_weekday', 'review_month',
        'has_reply', 'low_signal', 'is_duplicate', 'is_english',
        'service_signal', 'login_signal', 'price_signal',
        'refund_signal', 'update_signal',
        'positive_signal', 'negative_signal'
    ]

    print("Exporting CSV files...")
    with open('features.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(feature_rows)

    with open('features_sample.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(feature_rows[:100])

    print("Done.")
    print(f"  features.csv        : {len(feature_rows):,} rows")
    print(f"  features_sample.csv : 100 rows")

    cur.close()
    conn.close()

if __name__ == "__main__":
    generate_features()
    