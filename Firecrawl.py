import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
import os
from dotenv import load_dotenv

load_dotenv()
import datetime
from typing import Dict, Any, List
from urllib.parse import urljoin

# Firecrawl API configuration
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v0"

print(f"🔥 Enhanced Firecrawl Scraper Ready!")

# Mobile and varied user agents (less likely to be blocked)
MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36"
]

DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
]

def get_smart_delay():
    """Calculate smart delay based on time of day"""
    current_hour = datetime.datetime.now().hour
    
    if 2 <= current_hour <= 6:  # Early morning (less traffic)
        base_delay = random.uniform(5, 10)
        print(f"🌙 Early morning - using shorter delay: {base_delay:.1f}s")
    elif 9 <= current_hour <= 17:  # Business hours (high traffic)
        base_delay = random.uniform(15, 25)
        print(f"☀️ Business hours - using longer delay: {base_delay:.1f}s")
    else:  # Evening/night
        base_delay = random.uniform(8, 15)
        print(f"🌆 Evening/night - using medium delay: {base_delay:.1f}s")
    
    return base_delay

def get_random_headers(mobile_preferred=True):
    """Get randomized headers with mobile preference"""
    agents = MOBILE_USER_AGENTS if mobile_preferred else DESKTOP_USER_AGENTS
    user_agent = random.choice(agents)
    
    # Common referers to look more natural
    referers = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://duckduckgo.com/",
        "https://search.yahoo.com/"
    ]
    
    headers = {
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": random.choice(referers),
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Cache-Control": "max-age=0"
    }
    
    print(f"📱 Using {'mobile' if mobile_preferred else 'desktop'} user agent")
    return headers

def enhanced_firecrawl_scrape_url(url: str, attempt: int = 1) -> Dict[str, Any]:
    """Enhanced Firecrawl scraping with anti-blocking measures"""
    if not FIRECRAWL_API_KEY:
        return {"error": "Firecrawl API key not set"}
    
    try:
        # Use mobile headers for first 2 attempts, then try desktop
        mobile_preferred = attempt <= 2
        headers = get_random_headers(mobile_preferred)
        
        # Progressive wait times and configurations
        if attempt == 1:
            wait_time = 8000
            actions = [
                {"type": "wait", "milliseconds": 3000},
                {"type": "scroll", "direction": "down"}
            ]
        elif attempt == 2:
            wait_time = 12000
            actions = [
                {"type": "wait", "milliseconds": 5000},
                {"type": "scroll", "direction": "down"},
                {"type": "wait", "milliseconds": 2000}
            ]
        else:
            wait_time = 15000
            actions = [
                {"type": "wait", "milliseconds": 8000},
                {"type": "scroll", "direction": "down"},
                {"type": "wait", "milliseconds": 3000},
                {"type": "scroll", "direction": "up"}
            ]
        
        api_headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "formats": ["markdown", "html", "links"],
            "onlyMainContent": True,
            "includeTags": ["title", "meta", "h1", "h2", "h3", "p", "span", "div", "script", "article"],
            "waitFor": wait_time,
            "headers": headers,
            "actions": actions,
            "timeout": 60000  # 60 second timeout
        }
        
        print(f"🔥 Firecrawl attempt #{attempt}: {url[:60]}...")
        print(f"⏱️ Wait time: {wait_time/1000}s, Actions: {len(actions)}")
        
        # Make API call with longer timeout
        response = requests.post(
            f"{FIRECRAWL_BASE_URL}/scrape", 
            headers=api_headers, 
            json=payload,
            timeout=90  # 90 second timeout
        )
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            content_length = len(data.get("data", {}).get("markdown", ""))
            print(f"✅ Firecrawl success! Content length: {content_length} chars")
            
            return {
                "success": True,
                "content": data.get("data", {}),
                "markdown": data.get("data", {}).get("markdown", ""),
                "html": data.get("data", {}).get("html", ""),
                "metadata": data.get("data", {}).get("metadata", {}),
                "attempt": attempt
            }
        else:
            error_msg = data.get("error", "Unknown error")
            print(f"❌ Firecrawl API error (attempt {attempt}): {error_msg}")
            return {"error": f"API error: {error_msg}", "attempt": attempt}
            
    except requests.exceptions.Timeout:
        print(f"⏰ Firecrawl timeout on attempt {attempt}")
        return {"error": "Request timed out", "attempt": attempt}
    except requests.exceptions.RequestException as e:
        print(f"🌐 Firecrawl request failed (attempt {attempt}): {str(e)}")
        return {"error": f"Request failed: {str(e)}", "attempt": attempt}
    except Exception as e:
        print(f"❌ Firecrawl error (attempt {attempt}): {str(e)}")
        return {"error": f"Unexpected error: {str(e)}", "attempt": attempt}

def extract_product_info_from_content(content: str, website_name: str) -> Dict[str, Any]:
    """Enhanced product information extraction"""
    try:
        # Check for blocking indicators
        blocking_indicators = [
            "enter the characters you see",
            "captcha", 
            "403 forbidden",
            "access denied",
            "sorry, this item is out of stock",
            "page not found",
            "blocked",
            "robot check",
            "security check", 
            "verify you are human",
            "unusual traffic",
            "please complete the security check"
        ]
        
        content_lower = content.lower()
        for indicator in blocking_indicators:
            if indicator in content_lower:
                return {"error": f"Blocking detected: {indicator}"}
        
        # Check content quality
        if len(content.strip()) < 200:
            return {"error": "Insufficient content - likely blocked"}
        
        result = {
            "title": "Product not found",
            "price": 0.0,
            "average_rating": 0.0,
            "review_count": 0
        }
        
        # Enhanced title extraction
        title_patterns = [
            r'# (.+?)(?:\n|$)',  # Markdown H1
            r'## (.+?)(?:\n|$)',  # Markdown H2
            r'<h1[^>]*>([^<]+)</h1>',  # HTML H1
            r'<title[^>]*>([^<]+)</title>',  # HTML title
            r'"name":\s*"([^"]+)"',  # JSON-LD name
            r'product[_\s]*title[^>]*>([^<]+)',  # Product title classes
            r'item[_\s]*title[^>]*>([^<]+)',  # Item title classes
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            for match in matches:
                cleaned = re.sub(r'<[^>]+>', '', match).strip()
                cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
                
                if (len(cleaned) > 15 and 
                    not any(skip in cleaned.lower() for skip in [
                        'home', 'search', 'category', 'sign in', 'cart', 'checkout',
                        'captcha', 'forbidden', 'error', 'blocked', 'amazon.com',
                        'best buy', 'walmart', 'newegg'
                    ])):
                    result["title"] = cleaned[:100]  # Limit length
                    break
            if result["title"] != "Product not found":
                break
        
        # Enhanced price extraction
        price_patterns = [
            r'\$(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',
            r'USD\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',
            r'Price:?\s*\$(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',
            r'Current Price:?\s*\$(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',
            r'"price":\s*"?(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)"?',
            r'(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',
        ]
        
        all_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 5 < price < 5000:  # Reasonable range for electronics
                        all_prices.append(price)
                except ValueError:
                    continue
        
        if all_prices:
            # Take most common price, or median if no clear winner
            from collections import Counter
            price_counts = Counter(all_prices)
            if price_counts.most_common(1)[0][1] > 1:
                result["price"] = price_counts.most_common(1)[0][0]
            else:
                all_prices.sort()
                result["price"] = all_prices[len(all_prices)//2]  # Median
        
        # Enhanced rating extraction
        rating_patterns = [
            r'(\d+\.?\d*)\s*(?:out of|/) ?5\s*(?:stars?)?',
            r'(\d+\.?\d*)\s*stars?',
            r'(\d+\.?\d*)/5',
            r'"ratingValue":\s*"?(\d+\.?\d*)"?',
            r'Rating:?\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*star rating',
        ]
        
        ratings_found = []
        for pattern in rating_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    rating = float(match)
                    if 0 <= rating <= 5:
                        ratings_found.append(rating)
                except ValueError:
                    continue
        
        if ratings_found:
            result["average_rating"] = round(sum(ratings_found) / len(ratings_found), 1)
        
        # Enhanced review count extraction
        review_patterns = [
            r'(\d{1,6}(?:,\d{3})*)\s*(?:reviews?|ratings?|customer reviews?)',
            r'(\d{1,6}(?:,\d{3})*)\s*(?:people|customers?)\s*(?:rated|reviewed)',
            r'Based on\s*(\d{1,6}(?:,\d{3})*)\s*reviews?',
            r'"reviewCount":\s*"?(\d{1,6}(?:,\d{3})*)"?',
            r'(\d{1,6}(?:,\d{3})*)\s*total reviews?',
        ]
        
        reviews_found = []
        for pattern in review_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    count = int(match.replace(',', ''))
                    if 0 < count < 100000:  # Reasonable review count
                        reviews_found.append(count)
                except ValueError:
                    continue
        
        if reviews_found:
            result["review_count"] = max(reviews_found)  # Take highest count found
        
        print(f"✅ Extracted data:")
        print(f"   📝 Title: {result['title'][:60]}...")
        print(f"   💰 Price: ${result['price']}")
        print(f"   ⭐ Rating: {result['average_rating']}")
        print(f"   💬 Reviews: {result['review_count']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Extraction error: {str(e)}")
        return {"error": f"Extraction failed: {str(e)}"}

def enhanced_firecrawl_scrape_website(query: str, website_name: str, search_url: str) -> Dict[str, Any]:
    """Enhanced website scraping with multiple retry attempts"""
    try:
        print(f"\n🎯 Starting enhanced scraping for {website_name}")
        
        # Step 1: Get product URL (same as before)
        time.sleep(random.uniform(2, 5))
        
        headers = get_random_headers(mobile_preferred=True)
        if "bestbuy" in search_url.lower():
            headers.update({
                "CF-IPCountry": "US",
                "X-Forwarded-For": "8.8.8.8"
            })
        
        search_res = requests.get(search_url, headers=headers, timeout=20)
        search_res.raise_for_status()
        search_soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Find product link (same logic as before)
        product_link = None
        
        if "amazon" in website_name.lower():
            selectors = ["a[href*='/dp/']", ".s-result-item a[href*='/dp/']"]
        elif "bestbuy" in website_name.lower():
            selectors = [".sku-item .sku-header a", "h4.sku-header a", "a[href*='/site/'][href*='.p?']"]
        elif "walmart" in website_name.lower():
            selectors = ["a[href*='/ip/']", "[data-testid='product-title']"]
        elif "newegg" in website_name.lower():
            selectors = [".item-title", "a.item-title"]
        else:
            selectors = ["a[href*='/product']", "a[href*='/item']"]
        
        for selector in selectors:
            elements = search_soup.select(selector)
            if elements:
                element = elements[0]
                href = element.get('href', '') if hasattr(element, 'get') else ''
                
                if not href and hasattr(element, 'find_parent'):
                    parent_link = element.find_parent('a')
                    if parent_link:
                        href = parent_link.get('href', '')
                
                if href:
                    product_link = href
                    break
        
        if not product_link:
            return {"website": website_name, "error": "No product link found"}
        
        if not product_link.startswith('http'):
            product_link = urljoin(search_url, product_link)
        
        print(f"📍 Product URL found: {product_link[:80]}...")
        
        # Step 2: Enhanced Firecrawl scraping with retries
        smart_delay = get_smart_delay()
        print(f"⏳ Waiting {smart_delay:.1f}s before Firecrawl request...")
        time.sleep(smart_delay)
        
        # Try up to 3 times with different configurations
        for attempt in range(1, 4):
            if attempt > 1:
                retry_delay = random.uniform(10, 20) * attempt
                print(f"🔄 Retry #{attempt} after {retry_delay:.1f}s delay...")
                time.sleep(retry_delay)
            
            firecrawl_result = enhanced_firecrawl_scrape_url(product_link, attempt)
            
            if "error" not in firecrawl_result:
                # Success! Extract the data
                content = firecrawl_result.get("markdown", "") or firecrawl_result.get("html", "")
                
                if content:
                    product_info = extract_product_info_from_content(content, website_name)
                    
                    if "error" not in product_info:
                        return {
                            "website": website_name,
                            "title": product_info["title"],
                            "price": product_info["price"],
                            "average_rating": product_info["average_rating"],
                            "review_count": product_info["review_count"],
                            "attempt_used": attempt
                        }
                    else:
                        print(f"⚠️ Content extraction failed: {product_info['error']}")
                        if attempt == 3:  # Last attempt
                            return {"website": website_name, "error": product_info["error"]}
                else:
                    print(f"⚠️ No content returned on attempt {attempt}")
            else:
                print(f"⚠️ Firecrawl failed on attempt {attempt}: {firecrawl_result['error']}")
        
        return {"website": website_name, "error": "All retry attempts failed"}
        
    except Exception as e:
        return {"website": website_name, "error": f"Enhanced scraping failed: {str(e)}"}

def enhanced_firecrawl_scrape(product_name: str) -> List[Dict[str, Any]]:
    """Main enhanced Firecrawl scraping function"""
    results = []
    query = product_name.replace(" ", "+")
    
    print(f"🚀 ENHANCED FIRECRAWL SCRAPING: {product_name}")
    print("=" * 80)
    
    websites = [
        {"name": "Amazon.com", "search_url": f"https://www.amazon.com/s?k={query}"},
        {"name": "BestBuy.com", "search_url": f"https://www.bestbuy.com/site/searchpage.jsp?st={query}"},
        {"name": "Walmart.com", "search_url": f"https://www.walmart.com/search?q={query}"},
        {"name": "Newegg.com", "search_url": f"https://www.newegg.com/p/pl?d={query}"}
    ]
    
    for i, website in enumerate(websites):
        print(f"\n🎯 [{i+1}/{len(websites)}] Processing {website['name']}...")
        
        result = enhanced_firecrawl_scrape_website(query, website["name"], website["search_url"])
        results.append(result)
        
        # Smart delay between websites
        if i < len(websites) - 1:  # Don't delay after last website
            inter_site_delay = get_smart_delay() * 1.5
            print(f"⏳ Inter-site delay: {inter_site_delay:.1f}s")
            time.sleep(inter_site_delay)
    
    return results

def display_enhanced_results(results: List[Dict[str, Any]]):
    """Display results with enhanced formatting"""
    print(f"\n📊 ENHANCED SCRAPING RESULTS:")
    print("=" * 80)
    
    success_count = 0
    for result in results:
        print(f"\n{result['website']}:")
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            success_count += 1
            attempt = result.get('attempt_used', 1)
            print(f"  ✅ Success (attempt #{attempt})")
            print(f"  📝 Title: {result['title'][:70]}{'...' if len(result['title']) > 70 else ''}")
            print(f"  💰 Price: ${result['price']:.2f}")
            print(f"  ⭐ Rating: {result['average_rating']:.1f}/5.0")
            print(f"  💬 Reviews: {result['review_count']:,}")
    
    print(f"\n📈 Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    print("=" * 80)

def test_enhanced_scraper():
    """Test the enhanced scraper"""
    product_name = "Lenovo Tab P12-2024"
    results = enhanced_firecrawl_scrape(product_name)
    display_enhanced_results(results)

if __name__ == "__main__":
    test_enhanced_scraper()