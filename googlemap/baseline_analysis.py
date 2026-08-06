import os
import psycopg2
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score
)
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

# ── Load data ──────────────────────────────────────────────────
print("Loading data from database...")
conn = get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT
        f.review_id,
        f.review_length,
        f.has_reply,
        f.low_signal,
        f.is_duplicate,
        f.is_english,
        f.service_signal,
        f.login_signal,
        f.price_signal,
        f.refund_signal,
        f.update_signal,
        f.positive_signal,
        f.negative_signal,
        rr.score,
        cr.cleaned_content
    FROM features f
    JOIN cleaned_review cr ON f.review_id = cr.review_id
    JOIN raw_review rr ON f.review_id = rr.review_id
""")

rows = cur.fetchall()
columns = [
    'review_id', 'review_length', 'has_reply',
    'low_signal', 'is_duplicate', 'is_english',
    'service_signal', 'login_signal', 'price_signal',
    'refund_signal', 'update_signal',
    'positive_signal', 'negative_signal',
    'score', 'cleaned_content'
]

df = pd.DataFrame(rows, columns=columns)
print(f"Total records loaded: {len(df):,}")

cur.close()
conn.close()

# ── Define target ──────────────────────────────────────────────
def get_label(score):
    if score >= 4:
        return 'positive'
    elif score == 3:
        return 'neutral'
    else:
        return 'negative'

df['label'] = df['score'].apply(get_label)

# ── Class distribution ─────────────────────────────────────────
print("\nClass Distribution:")
print("-" * 40)
dist = df['label'].value_counts()
for label, count in dist.items():
    pct = count / len(df) * 100
    print(f"  {label:<10}: {count:>6,} ({pct:.1f}%)")

# ── Prepare features ───────────────────────────────────────────
feature_cols = [
    'review_length', 'has_reply',
    'low_signal', 'is_duplicate', 'is_english',
    'service_signal', 'login_signal', 'price_signal',
    'refund_signal', 'update_signal',
    'positive_signal', 'negative_signal'
]

X = df[feature_cols].astype(int)
y = df['label']

# ── Train/test split ───────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain size: {len(X_train):,}")
print(f"Test size:  {len(X_test):,}")

# ── Majority class baseline ────────────────────────────────────
from sklearn.dummy import DummyClassifier

print("\nMajority Class Baseline:")
print("-" * 40)
dummy = DummyClassifier(strategy='most_frequent', random_state=42)
dummy.fit(X_train, y_train)
y_dummy = dummy.predict(X_test)

dummy_macro_f1 = f1_score(y_test, y_dummy, average='macro')
print(classification_report(y_test, y_dummy, digits=3, zero_division=0))
print(f"Majority Class Macro F1: {dummy_macro_f1:.3f}")

# ── Train model ────────────────────────────────────────────────
print("\nTraining Logistic Regression...")
model = LogisticRegression(
    class_weight='balanced',
    max_iter=3000,
    random_state=42
)
model.fit(X_train, y_train)

# ── Evaluation ─────────────────────────────────────────────────
y_pred = model.predict(X_test)

print("\nClassification Report:")
print("-" * 40)
print(classification_report(y_test, y_pred, digits=3))

macro_f1 = f1_score(y_test, y_pred, average='macro')
print(f"Macro F1 Score: {macro_f1:.3f}")

print("\nConfusion Matrix:")
print("-" * 40)
cm = confusion_matrix(y_test, y_pred, labels=['positive', 'neutral', 'negative'])
print(f"{'':>12} {'pred_pos':>10} {'pred_neu':>10} {'pred_neg':>10}")
for i, label in enumerate(['positive', 'neutral', 'negative']):
    print(f"  {label:<10} {cm[i][0]:>10} {cm[i][1]:>10} {cm[i][2]:>10}")

# ── Feature importance ─────────────────────────────────────────
print("\nFeature Coefficients (positive class):")
print("-" * 40)
pos_idx = list(model.classes_).index('positive')
coefs = sorted(zip(feature_cols, model.coef_[pos_idx]), key=lambda x: abs(x[1]), reverse=True)
for feat, coef in coefs:
    print(f"  {feat:<25}: {coef:>8.3f}")

# ── Error analysis ─────────────────────────────────────────────
print("\nError Analysis:")
print("-" * 40)
df_test = df.iloc[X_test.index].copy()
df_test['predicted'] = y_pred
df_test['correct'] = df_test['label'] == df_test['predicted']

errors = df_test[~df_test['correct']]
print(f"Total errors: {len(errors):,} ({len(errors)/len(df_test)*100:.1f}%)")

no_signal_errors = errors[
    (~errors['positive_signal']) & (~errors['negative_signal'])
]
print(f"Errors with no keyword signals: {len(no_signal_errors):,} ({len(no_signal_errors)/len(errors)*100:.1f}%)")

print("\nError distribution by true label:")
err_dist = errors['label'].value_counts()
for label, count in err_dist.items():
    print(f"  {label:<10}: {count:>6,}")

print("\nSample errors (true=negative, predicted=positive):")
sample_errors = errors[
    (errors['label'] == 'negative') &
    (errors['predicted'] == 'positive')
][['cleaned_content', 'score', 'positive_signal', 'negative_signal']].head(3)

for _, row in sample_errors.iterrows():
    print(f"  Score: {row['score']} | pos_signal: {row['positive_signal']} | neg_signal: {row['negative_signal']}")
    print(f"  Content: {str(row['cleaned_content'])[:100]}")
    print()

print("Baseline analysis completed.")