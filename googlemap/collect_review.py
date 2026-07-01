import csv
import os
import time
from google_play_scraper import reviews, Sort

# Create data directory of Top 20 apps
os.makedirs('data', exist_ok=True)

apps = [
    {'id': 'com.openai.chatgpt',                    'name': 'ChatGPT',          'category': 'AI'},
    {'id': 'com.instagram.android',                  'name': 'Instagram',        'category': 'Social'},
    {'id': 'com.zhiliaoapp.musically',               'name': 'TikTok',           'category': 'Short Video'},
    {'id': 'com.lemon.lvoverseas',                   'name': 'CapCut',           'category': 'Video Editing'},
    {'id': 'com.whatsapp',                           'name': 'WhatsApp',         'category': 'Communication'},
    {'id': 'com.facebook.katana',                    'name': 'Facebook',         'category': 'Social'},
    {'id': 'com.spotify.music',                      'name': 'Spotify',          'category': 'Music'},
    {'id': 'com.einnovation.temu',                   'name': 'Temu',             'category': 'Shopping'},
    {'id': 'com.snapchat.android',                   'name': 'Snapchat',         'category': 'Social'},
    {'id': 'org.telegram.messenger',                 'name': 'Telegram',         'category': 'Communication'},
    {'id': 'com.netflix.mediaclient',                'name': 'Netflix',          'category': 'Streaming'},
    {'id': 'com.duolingo',                           'name': 'Duolingo',         'category': 'Education'},
    {'id': 'com.google.android.apps.maps',           'name': 'Google Maps',      'category': 'Navigation'},
    {'id': 'com.ubercab',                            'name': 'Uber',             'category': 'Ride-hailing'},
    {'id': 'com.dd.doordash',                        'name': 'DoorDash',         'category': 'Food Delivery'},
    {'id': 'com.google.android.apps.bard',           'name': 'Google Gemini',    'category': 'AI'},
    {'id': 'com.amazon.mShop.android.shopping',      'name': 'Amazon Shopping',  'category': 'E-commerce'},
    {'id': 'com.mcdonalds.app',                      'name': 'McDonalds',        'category': 'Food & Drink'},
    {'id': 'com.linkedin.android',                   'name': 'LinkedIn',         'category': 'Professional'},
    {'id': 'com.airbnb.android',                     'name': 'Airbnb',           'category': 'Travel'},
]

fields = [
    'app_name', 'app_category', 'reviewId', 'userName',
    'content', 'score', 'at', 'appVersion',
    'thumbsUpCount', 'replyContent'
]

output_file = 'data/google_play_reviews.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for app in apps:
        print(f"Collecting: {app['name']}...")

        try:
            result, _ = reviews(
                app['id'],
                lang='en',
                country='us',
                sort=Sort.NEWEST,
                count=1000
            )

            for r in result:
                writer.writerow({
                    'app_name':      app['name'],
                    'app_category':  app['category'],
                    'reviewId':      r.get('reviewId', ''),
                    'userName':      r.get('userName', ''),
                    'content':       r.get('content', ''),
                    'score':         r.get('score', ''),
                    'at':            r.get('at', ''),
                    'appVersion':    r.get('appVersion', ''),
                    'thumbsUpCount': r.get('thumbsUpCount', ''),
                    'replyContent':  r.get('replyContent', ''),
                })

            print(f"  Done: {len(result)} reviews collected")
            time.sleep(1)

        except Exception as e:
            print(f"  Error: {e}")

print()
print(f"All done. File saved to: {output_file}")