import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cur = conn.cursor()

signals = {
    'service_signal': ['support', 'help', 'response', 'contact', 'customer service'],
    'login_signal':   ['login', 'account', 'password', 'sign in', 'access'],
    'price_signal':   ['price', 'expensive', 'free', 'premium', 'worth'],
    'refund_signal':  ['refund', 'charge', 'billing', 'subscription', 'cancel'],
    'update_signal':  ['update', 'version', 'broke', 'after update', 'new version'],
    'positive_signal': ['love', 'amazing', 'perfect', 'excellent', 'great'],
    'negative_signal': ['terrible', 'awful', 'worst', 'horrible', 'useless'],
}

for signal, keywords in signals.items():
    conditions = " OR ".join([f"LOWER(r.cleaned_content) LIKE '%%{kw}%%'" for kw in keywords])
    cur.execute(f"""
        SELECT rr.score, COUNT(*) as count
        FROM cleaned_review r
        JOIN raw_review rr ON r.review_id = rr.review_id
        WHERE {conditions}
        GROUP BY rr.score
        ORDER BY rr.score
    """)
    rows = cur.fetchall()
    total = sum(row[1] for row in rows)

    print(f"\n{signal} (total: {total:,})")
    print(f"  {'Rating':<8} {'Count':>8} {'Rate':>8}")
    print(f"  {'-'*26}")
    for score, count in rows:
        pct = count / total * 100
        print(f"  {score} star   {count:>8,} {pct:>7.1f}%")

cur.close()
conn.close()