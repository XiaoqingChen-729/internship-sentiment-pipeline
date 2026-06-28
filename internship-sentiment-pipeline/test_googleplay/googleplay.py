from google_play_scraper import reviews, Sort

apps = [
    {'id': 'com.ubercab', 'name': 'Uber'},
    {'id': 'com.dd.doordash', 'name': 'DoorDash'},
    {'id': 'com.spotify.music', 'name': 'Spotify'},
    {'id': 'com.duolingo', 'name': 'Duolingo'},
    {'id': 'com.zhiliaoapp.musically', 'name': 'TikTok'},
]

fields = ['reviewId', 'userName', 'content', 'score', 'at', 'appVersion', 'thumbsUpCount', 'replyContent']

for app in apps:
    app_id = app['id']
    app_name = app['name']

    print(f"Test: {app_name}")
    print()

    # Test 1: Fetch 100 reviews
    result, continuation_token = reviews(
        app_id,
        lang='en',
        country='us',
        sort=Sort.NEWEST,
        count=100
    )

    print(f"Test 1 - Fetch 100 reviews")
    print(f"Reviews fetched: {len(result)}")
    print()

    if result:
        sample = result[0]
        print("Sample review fields:")
        for key, value in sample.items():
            print(f"  {key}: {value}")

    print()
    print()

    # Test 2: Check metadata completeness
    print("Test 2 - Metadata completeness check")
    for field in fields:
        missing = sum(1 for r in result if not r.get(field))
        print(f"  {field}: {len(result) - missing}/{len(result)} complete")

    print()
    print()

    # Test 3: Fetch 1000 reviews to reflect recurring collection
    print("Test 3 - Fetch 1000 reviews to reflect recurring collection")
    result_1000, _ = reviews(
        app_id,
        lang='en',
        country='us',
        sort=Sort.NEWEST,
        count=1000
    )
    print(f"Reviews fetched: {len(result_1000)}")

    print()
    print()

    print("Test completed.")
    print()
    print("-"*20)
    print()