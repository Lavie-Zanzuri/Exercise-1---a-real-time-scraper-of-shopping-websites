import requests
from bs4 import BeautifulSoup
import re
import time
import random

# Rotate between different user agents to reduce chance of being blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "DNT": "1"  # Do Not Track
    }

def basic_scrape(product_name: str):
    """Main function to scrape all websites for a product"""
    results = []
    query = product_name.replace(" ", "+")
    
    # Amazon scraping
    amazon_result = scrape_amazon(query)
    if amazon_result:
        results.append(amazon_result)
    
    # Best Buy scraping
    bestbuy_result = scrape_bestbuy(query)
    if bestbuy_result:
        results.append(bestbuy_result)
    
    # Walmart scraping
    walmart_result = scrape_walmart(query)
    if walmart_result:
        results.append(walmart_result)
    
    # Newegg scraping
    newegg_result = scrape_newegg(query)
    if newegg_result:
        results.append(newegg_result)
    
    return results

def clean_price(price_str):
    """Helper function to clean price strings and convert to float"""
    if not price_str:
        return 0.0
    
    # Remove currency symbols, commas, etc.
    cleaned = re.sub(r'[^\d.]', '', price_str)
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def extract_review_count(text):
    """Helper function to extract review count from text"""
    if not text:
        return 0
    
    # Look for patterns like "123 reviews" or "1,234 ratings"
    count_match = re.search(r'([\d,]+)\s*(?:reviews?|ratings?|customer reviews)', text, re.IGNORECASE)
    if count_match:
        return int(count_match.group(1).replace(',', ''))
    
    # If that fails, just try to find any number
    count_match = re.search(r'([\d,]+)', text)
    if count_match:
        return int(count_match.group(1).replace(',', ''))
    
    return 0

def extract_rating(text):
    """Helper function to extract rating from text"""
    if not text:
        return 0.0
    
    # Look for patterns like "4.5 out of 5" or just "4.5"
    rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|\/)\s*\d+', text)
    if rating_match:
        return float(rating_match.group(1))
    
    # If that fails, just try to find any decimal number
    rating_match = re.search(r'(\d+\.?\d*)', text)
    if rating_match:
        return float(rating_match.group(1))
    
    return 0.0

def scrape_amazon(query: str):
    """Scrape product information from Amazon"""
    search_url = f"https://www.amazon.com/s?k={query}"
    
    try:
        # Add a slight random delay
        time.sleep(random.uniform(1, 2))
        
        # Step 1: Search results page
        search_res = requests.get(search_url, headers=get_headers(), timeout=10)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Step 2: Find first product link
        first_result = soup.select_one("a.a-link-normal.s-no-outline")
        
        # Try alternative selectors if the first one doesn't work
        if not first_result:
            first_result = soup.select_one('.s-result-item [data-component-type="s-product-image"] a')
        if not first_result:
            first_result = soup.select_one('a.a-link-normal.s-underline-text')
        if not first_result:
            first_result = soup.select_one('.s-result-item a.a-link-normal')
        
        if not first_result:
            return {"website": "Amazon.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        if not product_url.startswith('http'):
            product_url = "https://www.amazon.com" + product_url
        
        # Step 3: Open the product page
        time.sleep(random.uniform(1, 2))
        product_res = requests.get(product_url, headers=get_headers(), timeout=10)
        product_res.raise_for_status()
        product_soup = BeautifulSoup(product_res.text, 'html.parser')
        
        # Step 4: Extract data
        # Title
        title_tag = product_soup.select_one("#productTitle")
        title = title_tag.get_text(strip=True) if title_tag else "Product title not found"
        
        # Price
        price_tag = product_soup.select_one(".a-price span.a-offscreen")
        if not price_tag:
            price_tag = product_soup.select_one("#priceblock_ourprice")
        if not price_tag:
            price_tag = product_soup.select_one("#priceblock_dealprice")
        if not price_tag:
            price_tag = product_soup.select_one(".a-price")
        
        price = 0.0
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            price = clean_price(price_text)
        
        # Rating
        rating_tag = product_soup.select_one("span.a-icon-alt")
        if not rating_tag:
            rating_tag = product_soup.select_one("#acrPopover")
            if rating_tag:
                rating_text = rating_tag.get('title', '')
            else:
                rating_text = ""
        else:
            rating_text = rating_tag.get_text(strip=True)
        
        rating = extract_rating(rating_text)
        
        # Review count
        review_tag = product_soup.select_one("#acrCustomerReviewText")
        review_count = extract_review_count(review_tag.get_text(strip=True) if review_tag else "")
        
        return {
            "website": "Amazon.com",
            "title": title,
            "price": price,
            "average_rating": rating,
            "review_count": review_count
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Amazon request error: {e}")
        return {"website": "Amazon.com", "error": f"Request failed: {str(e)}"}
    except Exception as e:
        print(f"Amazon unexpected error: {e}")
        return {"website": "Amazon.com", "error": str(e)}

def scrape_bestbuy(query: str):
    """Scrape product information from Best Buy"""
    search_url = f"https://www.bestbuy.com/site/searchpage.jsp?st={query}"
    
    try:
        # Add a slight random delay
        time.sleep(random.uniform(1, 2))
        
        # Step 1: Search results page
        search_res = requests.get(search_url, headers=get_headers(), timeout=10)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Step 2: Find first product link
        first_result = soup.select_one("a.image-link")
        if not first_result:
            first_result = soup.select_one(".sku-item .image-link")
        if not first_result:
            first_result = soup.select_one(".sku-header a")
        
        if not first_result:
            return {"website": "BestBuy.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        if not product_url.startswith('http'):
            product_url = "https://www.bestbuy.com" + product_url
        
        # Step 3: Open the product page
        time.sleep(random.uniform(1, 2))
        product_res = requests.get(product_url, headers=get_headers(), timeout=10)
        product_res.raise_for_status()
        product_soup = BeautifulSoup(product_res.text, 'html.parser')
        
        # Step 4: Extract data
        # Title
        title_tag = product_soup.select_one(".sku-title h1")
        if not title_tag:
            title_tag = product_soup.select_one("h1.heading-5")
        
        title = title_tag.get_text(strip=True) if title_tag else "Product title not found"
        
        # Price
        price_tag = product_soup.select_one(".priceView-customer-price span")
        if not price_tag:
            price_tag = product_soup.select_one(".priceView-purchase-price")
        if not price_tag:
            price_tag = product_soup.select_one(".pricing-price__current-price")
        
        price = 0.0
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            price = clean_price(price_text)
        
        # Rating
        rating_tag = product_soup.select_one(".customer-review-summary .c-review-average")
        if not rating_tag:
            rating_tag = product_soup.select_one("span.c-reviews-v4 p.visually-hidden")
        
        rating = 0.0
        if rating_tag:
            rating_text = rating_tag.get_text(strip=True)
            rating = extract_rating(rating_text)
        
        # Review count
        review_tag = product_soup.select_one(".customer-review-summary .c-reviews-count")
        if not review_tag:
            review_tag = product_soup.select_one("span.c-reviews-v4")
        
        review_count = extract_review_count(review_tag.get_text(strip=True) if review_tag else "")
        
        return {
            "website": "BestBuy.com",
            "title": title,
            "price": price,
            "average_rating": rating,
            "review_count": review_count
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Best Buy request error: {e}")
        return {"website": "BestBuy.com", "error": f"Request failed: {str(e)}"}
    except Exception as e:
        print(f"Best Buy unexpected error: {e}")
        return {"website": "BestBuy.com", "error": str(e)}

def scrape_walmart(query: str):
    """Scrape product information from Walmart"""
    search_url = f"https://www.walmart.com/search?q={query}"
    
    try:
        # Add a slight random delay
        time.sleep(random.uniform(1, 2))
        
        # Step 1: Search results page
        search_res = requests.get(search_url, headers=get_headers(), timeout=10)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Step 2: Find first product link
        first_result = soup.select_one("a[data-testid='product-title']")
        if not first_result:
            first_result = soup.select_one(".search-result-gridview-item a")
        if not first_result:
            first_result = soup.select_one(".product-title-link")
        
        if not first_result:
            return {"website": "Walmart.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        if not product_url.startswith('http'):
            product_url = "https://www.walmart.com" + product_url
        
        # Step 3: Open the product page
        time.sleep(random.uniform(1, 2))
        product_res = requests.get(product_url, headers=get_headers(), timeout=10)
        product_res.raise_for_status()
        product_soup = BeautifulSoup(product_res.text, 'html.parser')
        
        # Step 4: Extract data
        # Title
        title_tag = product_soup.select_one("h1[itemprop='name']")
        if not title_tag:
            title_tag = product_soup.select_one(".prod-ProductTitle")
        if not title_tag:
            title_tag = product_soup.select_one("[data-testid='product-title']")
        
        title = title_tag.get_text(strip=True) if title_tag else "Product title not found"
        
        # Price
        price_tag = product_soup.select_one("[data-testid='price-wrap'] span")
        if not price_tag:
            price_tag = product_soup.select_one(".price-characteristic")
        if not price_tag:
            price_tag = product_soup.select_one("[itemprop='price']")
        
        price = 0.0
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            price = clean_price(price_text)
        
        # Rating
        rating_tag = product_soup.select_one(".stars-reviews-count-node span")
        if not rating_tag:
            rating_tag = product_soup.select_one("[itemprop='ratingValue']")
        if not rating_tag:
            rating_tag = product_soup.select_one("[data-testid='stars-container']")
        
        rating = 0.0
        if rating_tag:
            rating_text = rating_tag.get_text(strip=True)
            if not rating_text and rating_tag.get('content'):
                rating_text = rating_tag.get('content')
            rating = extract_rating(rating_text)
        
        # Review count
        review_tag = product_soup.select_one(".stars-reviews-count")
        if not review_tag:
            review_tag = product_soup.select_one("[itemprop='reviewCount']")
        if not review_tag:
            review_tag = product_soup.select_one("[data-testid='review-count']")
        
        review_count = extract_review_count(review_tag.get_text(strip=True) if review_tag else "")
        
        return {
            "website": "Walmart.com",
            "title": title,
            "price": price,
            "average_rating": rating,
            "review_count": review_count
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Walmart request error: {e}")
        return {"website": "Walmart.com", "error": f"Request failed: {str(e)}"}
    except Exception as e:
        print(f"Walmart unexpected error: {e}")
        return {"website": "Walmart.com", "error": str(e)}

def scrape_newegg(query: str):
    """Scrape product information from Newegg"""
    search_url = f"https://www.newegg.com/p/pl?d={query}"
    
    try:
        # Add a slight random delay
        time.sleep(random.uniform(1, 2))
        
        # Step 1: Search results page
        search_res = requests.get(search_url, headers=get_headers(), timeout=10)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Step 2: Find first product link
        first_result = soup.select_one(".item-cell .item-title")
        if not first_result:
            first_result = soup.select_one(".item-container .item-info a.item-title")
        if not first_result:
            first_result = soup.select_one("a.item-img")
        
        if not first_result:
            return {"website": "Newegg.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        
        # Step 3: Open the product page
        time.sleep(random.uniform(1, 2))
        product_res = requests.get(product_url, headers=get_headers(), timeout=10)
        product_res.raise_for_status()
        product_soup = BeautifulSoup(product_res.text, 'html.parser')
        
        # Step 4: Extract data
        # Title
        title_tag = product_soup.select_one(".product-title")
        if not title_tag:
            title_tag = product_soup.select_one("h1.product-title")
        
        title = title_tag.get_text(strip=True) if title_tag else "Product title not found"
        
        # Price
        price_tag = product_soup.select_one(".price-current strong")
        if not price_tag:
            price_tag = product_soup.select_one(".product-price li.price-current")
        if not price_tag:
            price_tag = product_soup.select_one("[itemprop='price']")
        
        price = 0.0
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            if not price_text and price_tag.get('content'):
                price_text = price_tag.get('content')
            price = clean_price(price_text)
        
        # Rating
        rating_tag = product_soup.select_one(".product-rating")
        if not rating_tag:
            rating_tag = product_soup.select_one("[itemprop='ratingValue']")
        
        rating = 0.0
        if rating_tag:
            if rating_tag.get('title'):
                rating_text = rating_tag.get('title')
            elif rating_tag.get('content'):
                rating_text = rating_tag.get('content')
            else:
                rating_text = rating_tag.get_text(strip=True)
            rating = extract_rating(rating_text)
        
        # Review count
        review_tag = product_soup.select_one("span.product-rating-num")
        if not review_tag:
            review_tag = product_soup.select_one("[itemprop='reviewCount']")
        
        review_count = extract_review_count(review_tag.get_text(strip=True) if review_tag else "")
        
        return {
            "website": "Newegg.com",
            "title": title,
            "price": price,
            "average_rating": rating,
            "review_count": review_count
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Newegg request error: {e}")
        return {"website": "Newegg.com", "error": f"Request failed: {str(e)}"}
    except Exception as e:
        print(f"Newegg unexpected error: {e}")
        return {"website": "Newegg.com", "error": str(e)}

# Test function to run the scraper
def test_scraper():
    product_name = "Lenovo Tab P12-2024"
    print(f"Searching for: {product_name}")
    
    results = basic_scrape(product_name)
    
    # Print results in a nice format
    for result in results:
        print("\n" + "="*50)
        if "error" in result:
            print(f"{result['website']}: {result['error']}")
        else:
            print(f"Website: {result['website']}")
            print(f"Title: {result['title']}")
            print(f"Price: ${result['price']:.2f}")
            print(f"Rating: {result['average_rating']:.1f}/5.0")
            print(f"Reviews: {result['review_count']}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_scraper()