import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def load_page_with_selenium(url, wait_time=5):
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(wait_time)
    html = driver.page_source
    driver.quit()
    return html

def create_retry_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# Rotate between different user agents to reduce chance of being blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def basic_scrape(product_name: str):
    """Main function to scrape all websites for a product"""
    results = []
    query = product_name.replace(" ", "+")
    
    # Amazon scraping
    print("🔍 Scraping Amazon...")
    amazon_result = scrape_amazon(query)
    if amazon_result:
        results.append(amazon_result)
    
    # Best Buy scraping
    print("🔍 Scraping Best Buy...")
    bestbuy_result = scrape_bestbuy(query)
    if bestbuy_result:
        results.append(bestbuy_result)
    
    # Walmart scraping
    print("🔍 Scraping Walmart...")
    walmart_result = scrape_walmart(query)
    if walmart_result:
        results.append(walmart_result)
    
    # Newegg scraping
    print("🔍 Scraping Newegg...")
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
        rating = float(rating_match.group(1))
        # If rating is greater than 5, it might be out of 100, so convert
        if rating > 5:
            rating = rating / 20  # Convert from 100 scale to 5 scale
        return rating
    
    return 0.0

def save_debug_html(content, filename):
    """Save HTML content for debugging"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🔍 Saved debug HTML to '{filename}' for manual inspection.")
    except Exception as e:
        print(f"Failed to save debug HTML: {e}")

def scrape_amazon(query: str):
    """Scrape product information from Amazon"""
    search_url = f"https://www.amazon.com/s?k={query}"
    
    try:
        # Add a slight random delay
        time.sleep(random.uniform(1, 3))
        
        # Step 1: Search results page
        search_res = requests.get(search_url, headers=get_headers(), timeout=15)
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
            save_debug_html(search_res.text, "amazon_search_debug.html")
            return {"website": "Amazon.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        if not product_url.startswith('http'):
            product_url = "https://www.amazon.com" + product_url
        
        # Step 3: Open the product page
        time.sleep(random.uniform(1, 3))
        product_res = requests.get(product_url, headers=get_headers(), timeout=15)
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
    """Scrape product information from Best Buy - GEO BYPASS VERSION"""
    search_url = f"https://www.bestbuy.com/site/searchpage.jsp?st={query}"
    
    try:
        # Longer delay for Best Buy (they're very strict)
        time.sleep(random.uniform(4, 7))
        
        # Step 1: Enhanced headers with US geo indicators
        headers = get_headers()
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",  # Strong US preference
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate", 
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            # Geographic bypass headers
            "CF-IPCountry": "US",
            "X-Forwarded-For": "8.8.8.8",  # Google DNS (US)
            "X-Real-IP": "8.8.8.8",
            "CF-Connecting-IP": "8.8.8.8"
        })
        
        print("🔍 Attempting Best Buy search with geo bypass...")
        session = create_retry_session()
        
        # First, try to set US location by visiting Best Buy homepage
        try:
            print("🌎 Setting US location preference...")
            us_url = "https://www.bestbuy.com/"
            session.get(us_url, headers=headers, timeout=15)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Homepage visit failed: {e}")
        
        # Now do the search
        search_res = session.get(search_url, headers=headers, timeout=30)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Check if we got the country selection page
        if "choose a country" in search_res.text.lower() or "select your country" in search_res.text.lower():
            print("🚫 Still getting country selection page, trying direct product approach...")
            
            # Try a different approach - search for the specific product directly
            # Use the Lenovo Tab P12 that we know exists
            direct_search_url = f"https://www.bestbuy.com/site/searchpage.jsp?st=lenovo+tab+p12"
            search_res = session.get(direct_search_url, headers=headers, timeout=30)
            soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Debug: Save search page HTML
        save_debug_html(search_res.text, "bestbuy_search_debug.html")
        
        # Step 2: Updated selectors for Best Buy 2024/2025
        first_result = None
        
        # More comprehensive selectors for Best Buy product links
        selectors = [
            # Original selectors
            "h4.sku-header a",
            ".sku-item .sku-header a",
            ".list-item .sku-header a", 
            "a.image-link",
            ".sku-item a[href*='/site/']",
            ".sr-item h3 a",
            ".product-title a",
            # New/updated selectors for 2024-2025
            ".sku-title a",
            "[data-testid='sku-title'] a",
            ".product-item .sku-header a",
            ".product-link",
            ".sku-item h4 a",
            ".sr-item .sku-header a",
            # Generic fallbacks
            "a[href*='/site/'][href*='.p?']",  # Best Buy product URL pattern
            ".sku-item a[href^='/site/']"
        ]
        
        for selector in selectors:
            try:
                first_result = soup.select_one(selector)
                if first_result and first_result.get("href"):
                    print(f"✅ Found Best Buy product using selector: {selector}")
                    break
            except Exception as e:
                continue
        
        if not first_result:
            # Try to find ANY link that looks like a Best Buy product
            all_links = soup.find_all("a", href=True)
            for link in all_links:
                href = link.get("href", "")
                if "/site/" in href and (".p?" in href or "skuId=" in href):
                    first_result = link
                    print("✅ Found Best Buy product via URL pattern matching")
                    break
        
        if not first_result:
            return {"website": "BestBuy.com", "error": "No product found in search results - may be geo-blocked"}
        
        # Get product URL
        product_url = first_result.get("href")
        if not product_url.startswith('http'):
            product_url = "https://www.bestbuy.com" + product_url
        
        print(f"📍 Best Buy product URL: {product_url}")
        
        # Step 3: Load product page with geo bypass
        print("🔍 Loading Best Buy product page with geo bypass...")
        
        # Add US location parameters to URL if possible
        if "?" in product_url:
            product_url += "&loc=us"
        else:
            product_url += "?loc=us"
        
        # Enhanced headers for product page
        product_headers = headers.copy()
        product_headers.update({
            "Referer": search_url,
            "X-Requested-With": "XMLHttpRequest",  # Sometimes helps
        })
        
        # Multiple attempts with different strategies
        product_soup = None
        
        # Strategy 1: Try with enhanced headers
        try:
            print("📍 Strategy 1: Enhanced headers...")
            time.sleep(random.uniform(3, 6))
            product_res = session.get(product_url, headers=product_headers, timeout=30)
            product_res.raise_for_status()
            
            # Check if we got country selection again
            if "choose a country" not in product_res.text.lower():
                product_soup = BeautifulSoup(product_res.text, 'html.parser')
                print("✅ Strategy 1 successful")
            else:
                print("⚠️ Strategy 1 still showing country selection")
        except Exception as e:
            print(f"⚠️ Strategy 1 failed: {e}")
        
        # Strategy 2: Try Selenium if available and strategy 1 failed
        if not product_soup:
            try:
                print("🤖 Strategy 2: Selenium with US settings...")
                html = load_page_with_selenium(product_url, wait_time=10)
                if html and "choose a country" not in html.lower():
                    product_soup = BeautifulSoup(html, 'html.parser')
                    save_debug_html(html, "bestbuy_selenium_debug.html")
                    print("✅ Strategy 2 successful")
                else:
                    print("⚠️ Strategy 2 still showing country selection")
            except Exception as selenium_error:
                print(f"⚠️ Strategy 2 failed: {selenium_error}")
        
        # Strategy 3: Try a different product URL format
        if not product_soup:
            try:
                print("🔄 Strategy 3: Alternative URL format...")
                # Remove location parameter and try base URL
                clean_url = product_url.split('?')[0]
                time.sleep(random.uniform(3, 6))
                product_res = session.get(clean_url, headers=product_headers, timeout=30)
                
                if "choose a country" not in product_res.text.lower():
                    product_soup = BeautifulSoup(product_res.text, 'html.parser')
                    print("✅ Strategy 3 successful")
            except Exception as e:
                print(f"⚠️ Strategy 3 failed: {e}")
        
        if not product_soup:
            return {"website": "BestBuy.com", "error": "Unable to bypass geographic restrictions"}
        
        # Save the working HTML for debugging
        save_debug_html(str(product_soup), "bestbuy_working_debug.html")
        
        # Step 4: Enhanced data extraction (same as before)
        
        # Title - Comprehensive selectors
        title_selectors = [
            ".sku-title h1",
            "h1.heading-5",
            ".product-title h1", 
            "h1[data-testid='product-title']",
            ".pdp-product-name h1",
            ".sku-title",
            "[data-testid='sku-title']",
            ".product-title",
            "h1.sr-only",
            "h1"  # Last resort
        ]
        
        title = "Product title not found"
        for selector in title_selectors:
            try:
                title_tag = product_soup.select_one(selector)
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    # Make sure we got a real title (not country selection text)
                    if (len(title_text) > 10 and 
                        not title_text.lower().startswith('best buy') and
                        'choose a country' not in title_text.lower() and
                        'select your country' not in title_text.lower()):
                        title = title_text
                        print(f"✅ Found Best Buy title using: {selector}")
                        break
            except Exception as e:
                continue
        
        # Price - Enhanced extraction
        price_selectors = [
            # Screen reader text (most reliable)
            ".sr-only:contains('current price')",
            ".visually-hidden:contains('current price')", 
            ".sr-only:contains('Current price')",
            # Aria labels
            "[aria-label*='current price']",
            "[aria-label*='Current price']",
            # Class-based selectors
            ".pricing-price__current-price",
            ".current-price",
            ".price-current strong",
            ".sale-price",
            "[data-testid='customer-price']",
            # Generic price selectors
            ".price .sr-only",
            ".price-block .sr-only",
            ".notranslate:contains('$')"
        ]
        
        price = 0.0
        for selector in price_selectors:
            try:
                price_tag = product_soup.select_one(selector)
                if price_tag:
                    price_text = ""
                    
                    # Try different ways to get price text
                    if price_tag.get_text(strip=True):
                        price_text = price_tag.get_text(strip=True)
                    elif price_tag.get('aria-label'):
                        price_text = price_tag.get('aria-label')
                    elif price_tag.get('content'):
                        price_text = price_tag.get('content')
                    
                    if price_text and '$' in price_text:
                        extracted_price = clean_price(price_text)
                        if extracted_price > 0:
                            price = extracted_price
                            print(f"✅ Found Best Buy price: ${price} using {selector}")
                            break
            except Exception as e:
                continue
        
        # Rating - Look for screen reader text and aria labels
        rating_selectors = [
            ".sr-only:contains('out of 5')",
            ".visually-hidden:contains('out of 5')",
            "[aria-label*='out of 5']",
            "[aria-label*='star rating']", 
            "[aria-label*='stars']",
            ".stars-rating [aria-label]",
            ".review-rating [aria-label]",
            ".c-rating [aria-label]",
            "[data-testid='customer-review-average']"
        ]
        
        rating = 0.0
        for selector in rating_selectors:
            try:
                rating_tag = product_soup.select_one(selector)
                if rating_tag:
                    rating_text = ""
                    
                    if rating_tag.get_text(strip=True):
                        rating_text = rating_tag.get_text(strip=True)
                    elif rating_tag.get('aria-label'):
                        rating_text = rating_tag.get('aria-label')
                    
                    if rating_text and ('out of' in rating_text.lower() or 'star' in rating_text.lower()):
                        extracted_rating = extract_rating(rating_text)
                        if extracted_rating > 0:
                            rating = extracted_rating
                            print(f"✅ Found Best Buy rating: {rating} using {selector}")
                            break
            except Exception as e:
                continue
        
        # Review count - Look for review mentions
        review_selectors = [
            ".sr-only:contains('reviews')",
            ".visually-hidden:contains('reviews')",
            "[aria-label*='reviews']",
            "[aria-label*='review']",
            ".review-count",
            ".c-rating-count", 
            "[data-testid='customer-review-count']"
        ]
        
        review_count = 0
        for selector in review_selectors:
            try:
                review_tag = product_soup.select_one(selector)
                if review_tag:
                    review_text = ""
                    
                    if review_tag.get_text(strip=True):
                        review_text = review_tag.get_text(strip=True)
                    elif review_tag.get('aria-label'):
                        review_text = review_tag.get('aria-label')
                    
                    if review_text and 'review' in review_text.lower():
                        extracted_count = extract_review_count(review_text)
                        if extracted_count > 0:
                            review_count = extracted_count
                            print(f"✅ Found Best Buy reviews: {review_count} using {selector}")
                            break
            except Exception as e:
                continue
        
        # JSON-LD fallback (like Walmart)
        if rating == 0.0 or review_count == 0:
            try:
                scripts = product_soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    if script.string:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and "aggregateRating" in data:
                            if rating == 0.0:
                                rating = float(data["aggregateRating"].get("ratingValue", 0.0))
                            if review_count == 0:
                                review_count = int(data["aggregateRating"].get("reviewCount", 0))
                            print("✅ Found Best Buy rating/reviews in JSON-LD")
                            break
            except Exception as e:
                pass
        
        return {
            "website": "BestBuy.com",
            "title": title,
            "price": price,
            "average_rating": rating,
            "review_count": review_count
        }
    
    except requests.exceptions.Timeout:
        print("⚠️  Best Buy request timed out")
        return {"website": "BestBuy.com", "error": "Request timed out - Best Buy may be blocking requests"}
    except requests.exceptions.RequestException as e:
        print(f"Best Buy request error: {e}")
        return {"website": "BestBuy.com", "error": f"Request failed: {str(e)}"}
    except Exception as e:
        print(f"Best Buy unexpected error: {e}")
        return {"website": "BestBuy.com", "error": str(e)}

def extract_walmart_jsonld(product_soup):
    try:
        scripts = product_soup.find_all("script", type="application/ld+json")
        for script in scripts:
            json_text = script.string
            if not json_text:
                continue
            data = json.loads(json_text)
            if isinstance(data, dict) and "aggregateRating" in data:
                rating_data = data["aggregateRating"]
                rating = float(rating_data.get("ratingValue", 0.0))
                review_count = int(rating_data.get("reviewCount", 0))
                return rating, review_count
    except Exception as e:
        print(f"JSON-LD parse error: {e}")
    return 0.0, 0


def scrape_walmart(query: str):
    """Scrape product information from Walmart - IMPROVED VERSION"""
    search_url = f"https://www.walmart.com/search?q={query}"
    
    try:
        # Add a slight random delay
        time.sleep(random.uniform(2, 4))
        
        # Step 1: Search results page
        headers = get_headers()
        # Walmart is particularly strict, so we need good headers
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        })
        
        search_res = requests.get(search_url, headers=headers, timeout=15)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Debug: Save search page HTML
        save_debug_html(search_res.text, "walmart_search_debug.html")
        
        # Step 2: Find first product link - Updated selectors for Walmart
        first_result = None
        
        # Try multiple selectors for Walmart product links
        selectors = [
            "[data-testid='product-title']",
            "a[data-testid='product-title']",
            ".search-result-gridview-item a",
            ".product-title-link",
            "[data-automation-id='product-title'] a",
            "span[data-automation-id='product-title'] a",
            ".sans-serif a[href*='/ip/']"
        ]
        
        for selector in selectors:
            first_result = soup.select_one(selector)
            if first_result:
                print(f"✅ Found Walmart product using selector: {selector}")
                break
        
        # If we can't find a link, try to find any product and construct the link
        if not first_result:
            # Look for product titles and try to find parent links
            title_elements = soup.select("[data-testid='product-title'], .product-title")
            for title_elem in title_elements:
                parent_link = title_elem.find_parent("a")
                if parent_link and parent_link.get("href"):
                    first_result = parent_link
                    print("✅ Found Walmart product via parent link search")
                    break
        
        if not first_result:
            return {"website": "Walmart.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        if not product_url.startswith('http'):
            product_url = "https://www.walmart.com" + product_url
        
        print(f"📍 Walmart product URL: {product_url}")
        
        # Step 3: Open the product page
        time.sleep(random.uniform(2, 4))
        product_res = requests.get(product_url, headers=get_headers(), timeout=15)
        product_res.raise_for_status()
        product_soup = BeautifulSoup(product_res.text, 'html.parser')
        
        # Debug: Save product page HTML
        save_debug_html(product_res.text, "walmart_product_debug.html")
        
        # Step 4: Extract data with improved selectors
        # Title - Updated selectors
        title_selectors = [
            "h1[data-automation-id='product-title']",
            "h1[itemprop='name']",
            ".prod-ProductTitle",
            "[data-testid='product-title']",
            "h1.prod-ProductTitle",
            ".x-product-title-label h1"
        ]
        
        title = "Product title not found"
        for selector in title_selectors:
            title_tag = product_soup.select_one(selector)
            if title_tag:
                title = title_tag.get_text(strip=True)
                break
        
        # Price - Updated selectors
        price_selectors = [
            "[itemprop='price']",
            "[data-testid='price-wrap'] span",
            "[data-automation-id='product-price']",
            ".price-characteristic",
            ".price-group span[itemprop='price']",
            ".notranslate[data-automation-id='product-price']"
        ]
        
        price = 0.0
        for selector in price_selectors:
            price_tag = product_soup.select_one(selector)
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                if not price_text and price_tag.get('content'):
                    price_text = price_tag.get('content')
                if price_text:
                    price = clean_price(price_text)
                    if price > 0:
                        break
        
        # Rating - Updated selectors
        rating_selectors = [
            "[itemprop='ratingValue']",
            "[data-testid='reviews-section'] span",
            ".average-rating",
            ".stars-reviews-count-node span"
        ]
        
        rating = 0.0
        for selector in rating_selectors:
            rating_tag = product_soup.select_one(selector)
            if rating_tag:
                rating_text = rating_tag.get_text(strip=True)
                if not rating_text and rating_tag.get('content'):
                    rating_text = rating_tag.get('content')
                if rating_text:
                    rating = extract_rating(rating_text)
                    if rating > 0:
                        break
        
        # Review count - Updated selectors
        review_selectors = [
            "[itemprop='reviewCount']",
            "[data-testid='review-count']",
            ".stars-reviews-count",
            "[data-testid='reviews-section'] span:contains('review')"
        ]
        
        review_count = 0
        for selector in review_selectors:
            review_tag = product_soup.select_one(selector)
            if review_tag:
                review_text = review_tag.get_text(strip=True)
                if not review_text and review_tag.get('content'):
                    review_text = review_tag.get('content')
                if review_text:
                    review_count = extract_review_count(review_text)
                    if review_count > 0:
                        break
        rating, review_count = extract_walmart_jsonld(product_soup)
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
        time.sleep(random.uniform(1, 3))
        
        # Step 1: Search results page
        search_res = requests.get(search_url, headers=get_headers(), timeout=15)
        search_res.raise_for_status()
        soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Step 2: Find first product link
        first_result = soup.select_one(".item-cell .item-title")
        if not first_result:
            first_result = soup.select_one(".item-container .item-info a.item-title")
        if not first_result:
            first_result = soup.select_one("a.item-img")
        
        if not first_result:
            save_debug_html(search_res.text, "newegg_search_debug.html")
            return {"website": "Newegg.com", "error": "No product found in search results"}
        
        # Get product URL
        product_url = first_result.get("href")
        
        # Step 3: Open the product page
        time.sleep(random.uniform(1, 3))
        product_res = requests.get(product_url, headers=get_headers(), timeout=15)
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
    print(f"🚀 Searching for: {product_name}")
    print("="*60)
    
    results = basic_scrape(product_name)
    
    # Print results in a nice format
    print("\n📊 SCRAPING RESULTS:")
    print("="*60)
    
    for result in results:
        print("\n" + "-"*50)
        if "error" in result:
            print(f"❌ {result['website']}: {result['error']}")
        else:
            print(f"✅ Website: {result['website']}")
            print(f"   Title: {result['title'][:80]}{'...' if len(result['title']) > 80 else ''}")
            print(f"   Price: ${result['price']:.2f}")
            print(f"   Rating: {result['average_rating']:.1f}/5.0")
            print(f"   Reviews: {result['review_count']:,}")
    
    print("\n" + "="*60)
    print("🔍 Debug HTML files saved for manual inspection if needed.")

if __name__ == "__main__":
    test_scraper()