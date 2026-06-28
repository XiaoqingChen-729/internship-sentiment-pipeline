import requests
import json

product_name = 'Apple AirPods 4'
asin = 'B0DGHMNQ5Z'

url = 'https://www.amazon.com/acp/cr-media-carousel/cr-media-carousel-89385885-b8b5-4d07-a554-043671389e32-1781094729173/getGroupedMediaReviews?page-type=Detail&stamp=1782688168980'

headers = {
    'accept': 'text/html, application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://www.amazon.com',
    'referer': f'https://www.amazon.com/dp/{asin}',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'x-amz-amabot-click-attributes': 'disable',
}

cookies = {
    'session-id': '139-7720361-2317444',
    'ubid-main': '135-6246251-3074918',
    'session-token': 'BCdjNeg9wxVmkbvM6PInNU3EC/iPrTUqbBOB2pUXUF57YKik4zOLhnlVdp0VnD3i+lXzNLm/cZ7WsIvBFkHDyRzy0S68jmusZE3kDqnehTB3RQZxyDEcu3ZFDUqd+ERDq/3ryzhrKiCsinr3TkniLSS8uhoMXUCuR36+AvhJJKRkBLKGBG9C3/pC4SBPhBqxwuhs5nKeNZf0sZfNii5PYvlmlborsGj1',
    'lc-main': 'en_US',
    'i18n-prefs': 'USD',
}

payload = {
    'asin': asin,
    'mediaType': 'IMAGE',
    'limit': 25
}

print(f"Target product: {product_name}")
print()
print("Test - Fetching reviews via internal API...")
print()

response = requests.post(url, headers=headers, cookies=cookies, json=payload)
print(f"Status code: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    reviews = data.get('mediaGroupList', [])
    print(f"Reviews fetched: {len(reviews)}")
    print()
    
    if reviews:
        sample = reviews[0]['metadata']['review']
        print("Sample review fields:")
        print(f"  id: {sample.get('id')}")
        print(f"  title: {sample.get('title')}")
        print(f"  rating: {sample.get('rating')}")
        print(f"  date: {sample.get('originDescription')}")
        text = sample.get('text', {}).get('fragments', [{}])[0].get('paragraph', {}).get('fragments', [{}])[0].get('text', 'None')
        print(f"  text: {text[:100]}")
        contributor = reviews[0]['metadata'].get('contributor', {})
        print(f"  userName: {contributor.get('name')}")
else:
    print("Failed to fetch reviews")
    print(response.text[:200])

print()
print("Test completed.")