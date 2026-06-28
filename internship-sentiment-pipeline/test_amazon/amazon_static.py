import requests
from bs4 import BeautifulSoup
import time

product_name = 'Apple AirPods 4'
product_url = 'https://www.amazon.com/product-reviews/B0DGHMNQ5Z'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Target product: {product_name}")
print()

# Test 1: Basic accessibility
print("Test 1 - Basic accessibility check")
response = requests.get(product_url, headers=headers)
print(f"Status code: {response.status_code}")
print(f"Page accessible: {'Yes' if response.status_code == 200 else 'No'}")
print()

# Test 2: Parse review content
print("Test 2 - Parse review content")
soup = BeautifulSoup(response.text, 'html.parser')
reviews = soup.find_all('div', {'data-hook': 'review'})
print(f"Reviews found on page: {len(reviews)}")
print()

# Test 3: Pagination
print("Test 3 - Pagination test")
page_2_url = product_url + '?pageNumber=2'
time.sleep(2)
response_2 = requests.get(page_2_url, headers=headers)
print(f"Page 2 status code: {response_2.status_code}")
soup_2 = BeautifulSoup(response_2.text, 'html.parser')
reviews_2 = soup_2.find_all('div', {'data-hook': 'review'})
print(f"Reviews found on page 2: {len(reviews_2)}")
print()

# Test 4: Anti-scraping detection
print("Test 4 - Anti-scraping detection")
blocked = 'Robot Check' in response.text or 'captcha' in response.text.lower()
print(f"Bot detection triggered: {blocked}")
print()

print("Test completed.")