import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Setup
df = pd.read_csv('data/google_play_reviews.csv')
os.makedirs('eda_output', exist_ok=True)
sns.set_theme(style='whitegrid')

print("=" * 60)
print("GOOGLE PLAY STORE REVIEWS - EDA REPORT")
print("=" * 60)

# 1. Basic Overview
print("\n1. BASIC OVERVIEW")
print(f"   Total reviews       : {len(df):,}")
print(f"   Total apps          : {df['app_name'].nunique()}")
print(f"   Total categories    : {df['app_category'].nunique()}")
print(f"   Date range          : {df['at'].min()} → {df['at'].max()}")

# 2. Reviews per App 
print("\n2. REVIEWS PER APP")
app_counts = df.groupby('app_name').size().sort_values(ascending=False)
print(app_counts.to_string())

# 3. Rating Distribution
print("\n3. RATING DISTRIBUTION")
rating_counts = df['score'].value_counts().sort_index()
rating_pct = (rating_counts / len(df) * 100).round(1)
for score, count in rating_counts.items():
    print(f"   {score} star: {count:,} ({rating_pct[score]}%)")

fig = plt.figure(figsize=(16, 6))

# Left: 1/3 width
ax1 = fig.add_axes([0.05, 0.12, 0.25, 0.75])
bar_colors = ['#D4A5A5', '#c8c8c8', '#b0b0b0', '#989898', '#8B1A1A']
ax1.bar(rating_counts.index, rating_counts.values, color=bar_colors,
        width=0.5, edgecolor='white', linewidth=0.5)
ax1.set_title('Overall Rating\nDistribution', fontsize=12, fontweight='bold', pad=10)
ax1.set_xlabel('Star Rating', fontsize=10)
ax1.set_ylabel('Count', fontsize=10)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_visible(False)
ax1.grid(axis='y', color='#e0e0e0', linewidth=0.8)
ax1.grid(axis='x', visible=False)
ax1.set_axisbelow(True)

# Right: 2/3 width - top 5 categories with largest gap between 5-star and 1-star
ax2 = fig.add_axes([0.38, 0.12, 0.58, 0.75])

rating_by_cat = df.groupby(['app_category', 'score']).size().unstack(fill_value=0)
rating_by_cat['gap'] = rating_by_cat[5] - rating_by_cat[1]
top5_gap = rating_by_cat.nlargest(5, 'gap')
top5_gap = top5_gap.drop(columns='gap')
top5_gap = top5_gap[[1, 2, 3, 4, 5]]

score_colors = {
    1: '#D4A5A5',
    2: '#c8c8c8',
    3: '#b0b0b0',
    4: '#989898',
    5: '#8B1A1A'
}

x = range(len(top5_gap))
width = 0.15
offsets = [-2, -1, 0, 1, 2]

for i, score in enumerate([1, 2, 3, 4, 5]):
    if score in top5_gap.columns:
        ax2.bar([xi + offsets[i] * width for xi in x],
                top5_gap[score],
                width=width,
                color=score_colors[score],
                label=f'{score} star',
                edgecolor='white',
                linewidth=0.5)

ax2.set_title('Rating Distribution — Top 5 Categories\nby Gap between 5-Star and 1-Star Reviews',
              fontsize=12, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(top5_gap.index, rotation=20, ha='right', fontsize=9)
ax2.set_ylabel('Count', fontsize=10)
ax2.legend(title='Score', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.grid(axis='y', color='#e0e0e0', linewidth=0.8)
ax2.grid(axis='x', visible=False)
ax2.set_axisbelow(True)

plt.savefig('eda_output/rating_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("   Chart saved: eda_output/rating_distribution.png")

# 4. Review Length
print("\n4. REVIEW LENGTH ANALYSIS")
df['review_length'] = df['content'].fillna('').apply(len)
print(f"   Mean length   : {df['review_length'].mean():.1f} chars")
print(f"   Median length : {df['review_length'].median():.1f} chars")
print(f"   Max length    : {df['review_length'].max()} chars")
print(f"   Min length    : {df['review_length'].min()} chars")

length_by_app = df.groupby('app_name')['review_length'].mean().sort_values(ascending=True)
print("\n   Average review length by app:")
for app, length in length_by_app.items():
    print(f"   {app:<20}: {length:.1f} chars")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: histogram
axes[0].hist(df['review_length'].clip(upper=500), bins=50, color='#D4A5A5', edgecolor='white', linewidth=0.5)
axes[0].set_title('Review Length Distribution (capped at 500 chars)', fontsize=13, fontweight='bold', pad=15)
axes[0].set_xlabel('Character Count', fontsize=11)
axes[0].set_ylabel('Frequency', fontsize=11)
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].grid(axis='y', color='#e0e0e0', linewidth=0.8)
axes[0].grid(axis='x', visible=False)
axes[0].set_axisbelow(True)

# Right: horizontal bar
length_by_app_desc = length_by_app.sort_values(ascending=True)
top5_apps = length_by_app.sort_values(ascending=False).head(5).index
colors = ['#8B1A1A' if app in top5_apps else '#D4A5A5' for app in length_by_app_desc.index]

axes[1].barh(length_by_app_desc.index, length_by_app_desc.values, color=colors, edgecolor='white', linewidth=0.5)
axes[1].set_title('Average Review Length by App', fontsize=13, fontweight='bold', pad=15)
axes[1].set_xlabel('Average Characters', fontsize=11)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[1].grid(axis='x', visible=False)
axes[1].grid(axis='y', color='#e0e0e0', linewidth=0.8)
axes[1].set_axisbelow(True)

plt.tight_layout()
plt.savefig('eda_output/review_length.png', dpi=150, bbox_inches='tight')
plt.close()
print("   Chart saved: eda_output/review_length.png")

# 5. Timestamp Coverage
print("\n5. TIMESTAMP COVERAGE")
df['at'] = pd.to_datetime(df['at'])
df['date'] = df['at'].dt.date
print(f"   Earliest review : {df['at'].min()}")
print(f"   Latest review   : {df['at'].max()}")

daily_counts = df.groupby('date').size()

fig, ax = plt.subplots(figsize=(14, 5))

# Color: top 5 days deep red, rest light red
top5_dates = daily_counts.nlargest(5).index
colors = ['#8B1A1A' if d in top5_dates else '#D4A5A5' for d in daily_counts.index]

ax.bar(range(len(daily_counts)), daily_counts.values, color=colors, edgecolor='white', linewidth=0.5)
ax.set_xticks(range(len(daily_counts)))
ax.set_xticklabels([str(d) for d in daily_counts.index], rotation=45, ha='right', fontsize=8)

ax.set_title('Reviews by Day', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Date', fontsize=11)
ax.set_ylabel('Count', fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', color='#e0e0e0', linewidth=0.8)
ax.grid(axis='x', visible=False)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('eda_output/timestamp_coverage.png', dpi=150, bbox_inches='tight')
plt.close()
print("   Chart saved: eda_output/timestamp_coverage.png")

# 6. Missing Fields
print("\n6. MISSING FIELDS")
fields = ['reviewId', 'userName', 'content', 'score', 'at', 'appVersion', 'thumbsUpCount', 'replyContent']
for field in fields:
    missing = df[field].isna().sum()
    pct = missing / len(df) * 100
    print(f"   {field:<20}: {missing:,} missing ({pct:.1f}%)")

missing_data = pd.DataFrame({
    'field': fields,
    'missing_pct': [df[f].isna().sum() / len(df) * 100 for f in fields]
})

# Color: deep red for highest, light red for second, light gray for zeros
max_val = missing_data['missing_pct'].max()
second_val = missing_data['missing_pct'].nlargest(2).iloc[1]

def get_color(val):
    if val == max_val:
        return '#8B1A1A'
    elif val == second_val and val > 0:
        return '#D4A5A5'
    else:
        return '#e8e8e8'

colors = missing_data['missing_pct'].apply(get_color)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(missing_data['field'], missing_data['missing_pct'], color=colors, edgecolor='white')

# Add value labels
for bar, val in zip(bars, missing_data['missing_pct']):
    if val > 0:
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', fontsize=9,
                color='#8B1A1A' if val == max_val else '#999999')

ax.set_title('Missing Data by Field (%)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Missing (%)', fontsize=11)
ax.spines['bottom'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.xaxis.set_label_position('top')
ax.xaxis.tick_top()
ax.grid(axis='y', visible=False)
ax.grid(axis='x', color='#e0e0e0', linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('eda_output/missing_fields.png', dpi=150, bbox_inches='tight')
plt.close()
print("   Chart saved: eda_output/missing_fields.png")

# 7. Duplicates
print("\n7. DUPLICATE ANALYSIS")
dup_id = df['reviewId'].duplicated().sum()
dup_content = df['content'].duplicated().sum()
print(f"   Duplicate reviewIds : {dup_id:,}")
print(f"   Duplicate content   : {dup_content:,}")

# 8. Language Issues
print("\n8. LANGUAGE ANALYSIS")
def is_english(text):
    if not isinstance(text, str) or len(text) == 0:
        return False
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / len(text) > 0.8

df['is_english'] = df['content'].apply(is_english)
english_count = df['is_english'].sum()
non_english = len(df) - english_count
print(f"   Likely English     : {english_count:,} ({english_count/len(df)*100:.1f}%)")
print(f"   Likely non-English : {non_english:,} ({non_english/len(df)*100:.1f}%)")

lang_by_app = df.groupby('app_name')['is_english'].mean() * 100
print("\n   English rate by app:")
for app, rate in lang_by_app.sort_values().items():
    print(f"   {app:<20}: {rate:.1f}%")

# 9. Low-signal Reviews
print("\n9. LOW-SIGNAL REVIEWS")
df['is_low_signal'] = df['review_length'] < 20
low_signal = df['is_low_signal'].sum()
print(f"   Reviews under 20 chars : {low_signal:,} ({low_signal/len(df)*100:.1f}%)")

print("\n   Sample low-signal reviews:")
samples = df[df['is_low_signal']]['content'].dropna().sample(min(5, low_signal), random_state=42)
for i, s in enumerate(samples, 1):
    print(f"   {i}. '{s}'")

low_by_app = df.groupby('app_name')['is_low_signal'].mean() * 100
low_by_app_sorted = low_by_app.sort_values(ascending=False)

colors = ['#8B1A1A' if i < 5 else '#D4A5A5' for i in range(len(low_by_app_sorted))]

fig, ax = plt.subplots(figsize=(14, 6))
bars = ax.bar(low_by_app_sorted.index, low_by_app_sorted.values, color=colors, edgecolor='white', linewidth=0.5)

for bar, val in zip(bars, low_by_app_sorted.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8,
            color='#8B1A1A' if val >= low_by_app_sorted.iloc[4] else '#999999')

ax.set_title('Low-Signal Review Rate by App (< 20 chars)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('App', fontsize=11)
ax.set_ylabel('Percentage (%)', fontsize=11)
ax.tick_params(axis='x', rotation=45)
ax.set_ylim(0, low_by_app_sorted.max() * 1.12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='y', color='#e0e0e0', linewidth=0.8)
ax.grid(axis='x', visible=False)

plt.tight_layout()
plt.savefig('eda_output/low_signal_reviews.png', dpi=150, bbox_inches='tight')
plt.close()
print("   Chart saved: eda_output/low_signal_reviews.png")

# 10. App/Category Differences
print("\n10. APP & CATEGORY DIFFERENCES")
avg_rating = df.groupby('app_name')['score'].mean().sort_values(ascending=True)
print("   Average rating by app:")
for app, rating in avg_rating.items():
    print(f"   {app:<20}: {rating:.2f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: by app
top5_apps = avg_rating.nlargest(5).index
colors_app = ['#8B1A1A' if app in top5_apps else '#D4A5A5' for app in avg_rating.index]

axes[0].barh(avg_rating.index, avg_rating.values, color=colors_app, edgecolor='white', linewidth=0.5)
axes[0].set_title('Average Rating by App', fontsize=13, fontweight='bold', pad=15)
axes[0].set_xlabel('Average Score', fontsize=11)
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].grid(axis='x', visible=False)
axes[0].grid(axis='y', visible=False)
axes[0].set_axisbelow(True)

# Right: by category
avg_rating_cat = df.groupby('app_category')['score'].mean().sort_values(ascending=True)
top5_cats = avg_rating_cat.nlargest(5).index
colors_cat = ['#8B1A1A' if cat in top5_cats else '#D4A5A5' for cat in avg_rating_cat.index]

axes[1].barh(avg_rating_cat.index, avg_rating_cat.values, color=colors_cat, edgecolor='white', linewidth=0.5)
axes[1].set_title('Average Rating by Category', fontsize=13, fontweight='bold', pad=15)
axes[1].set_xlabel('Average Score', fontsize=11)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
axes[1].grid(axis='x', visible=False)
axes[1].grid(axis='y', visible=False)
axes[1].set_axisbelow(True)

plt.tight_layout()
plt.savefig('eda_output/ratings_by_app_category.png', dpi=150, bbox_inches='tight')
plt.close()
print("   Chart saved: eda_output/ratings_by_app_category.png")

print("\n" + "=" * 60)
print("EDA COMPLETED")
print(f"All charts saved to: eda_output/")
print("=" * 60)