import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
import os
from dotenv import load_dotenv

load_dotenv()
from typing import Dict, Any, Optional
from urllib.parse import urljoin

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("🔍 DEBUG: Using Gemini API key")

# User agents for web scraping
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
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

def call_gemini_api(prompt: str) -> str:
    """Call Gemini API directly using HTTP requests"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000,
                "topP": 0.8,
                "topK": 10
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        print("🤖 Calling Gemini API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract the generated text
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                return candidate["content"]["parts"][0]["text"]
        
        raise Exception("No valid response from Gemini API")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Gemini API request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

def clean_html(html_content: str) -> str:
    """Clean HTML content to reduce token usage for LLM"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unnecessary elements that don't contain product info
    for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe', 'noscript', 'svg']):
        element.decompose()
    
    # Remove comments
    comments = soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text)
    for comment in comments:
        comment.extract()
    
    # Get text content but preserve some structure
    text_content = soup.get_text(separator=' ', strip=True)
    
    # Clean up extra whitespace
    text_content = re.sub(r'\s+', ' ', text_content)
    
    # Limit size to avoid token limits (keep first 6000 characters)
    if len(text_content) > 6000:
        text_content = text_content[:6000] + "... [content truncated for length]"
    
    return text_content

def extract_product_data_with_llm(html_content: str, website_name: str, product_query: str) -> Dict[str, Any]:
    """Extract product data using LLM via direct API call"""
    try:
        # Clean HTML to reduce tokens
        cleaned_content = clean_html(html_content)
        print(f"📝 Cleaned content length: {len(cleaned_content)} characters")
        
        # Create a prompt that extracts from whatever product is found (like basic scraping)
        prompt = f"""Extract product information from this {website_name} webpage. This is the FIRST search result for "{product_query}".

Extract information from whatever product you find on this page, even if it's not an exact match for the search query.

WEBPAGE CONTENT:
{cleaned_content}

Extract information from the main product shown on this page:
{{
    "title": "the main product title shown on the page",
    "price": current_price_as_number,
    "average_rating": rating_as_decimal,
    "review_count": total_reviews_as_number
}}

Rules:
- Extract from whatever product is displayed, even if it's a related/similar product
- Return ONLY valid JSON
- Use 0 for missing numeric values, "Product not found" for missing title
- Get the current price (not crossed out prices)
- Convert ratings to 5-star scale if needed

JSON:"""

        print(f"🤖 Asking LLM to extract data from {website_name}...")
        
        # Call Gemini API
        llm_response = call_gemini_api(prompt)
        print(f"📝 LLM raw response: {llm_response[:200]}...")
        
        # Clean response
        cleaned_response = llm_response.strip()
        
        # Remove markdown formatting if present
        if "```json" in cleaned_response:
            cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_response:
            cleaned_response = cleaned_response.split("```")[1].strip()
        
        # Find JSON in response
        json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
        if json_match:
            cleaned_response = json_match.group(0)
        
        # Parse JSON
        try:
            extracted_data = json.loads(cleaned_response)
            print(f"✅ LLM successfully extracted data from {website_name}")
            
            # Handle null values safely
            title = extracted_data.get('title') or "Not found"
            price = extracted_data.get('price') or 0
            rating = extracted_data.get('average_rating') or 0
            reviews = extracted_data.get('review_count') or 0
            
            print(f"   Title: {title[:50]}...")
            print(f"   Price: ${price}")
            print(f"   Rating: {rating}")
            print(f"   Reviews: {reviews}")
            
            return {
                "title": title,
                "price": price,
                "average_rating": rating,
                "review_count": reviews
            }
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON from LLM: {cleaned_response[:300]}...")
            return {"error": f"Invalid JSON: {str(e)}"}
    
    except Exception as e:
        print(f"❌ LLM extraction failed: {str(e)}")
        return {"error": f"LLM extraction failed: {str(e)}"}

def llm_scrape_website(query: str, website_name: str, search_url: str) -> Dict[str, Any]:
    """Generic LLM scraping function for any website"""
    try:
        print(f"🔍 LLM scraping {website_name}...")
        
        # Add random delay
        time.sleep(random.uniform(3, 6))
        
        # Get search results page
        headers = get_headers()
        if "bestbuy" in search_url.lower():
            # Special handling for Best Buy
            headers.update({
                "Accept-Language": "en-US,en;q=0.9",
                "CF-IPCountry": "US",
                "X-Forwarded-For": "8.8.8.8"
            })
        
        search_res = requests.get(search_url, headers=headers, timeout=20)
        search_res.raise_for_status()
        search_soup = BeautifulSoup(search_res.text, 'html.parser')
        
        # Try to find the first product link using common patterns
        product_link = None
        
        # Site-specific link patterns - get FIRST result like basic scraper
        if "amazon" in website_name.lower():
            selectors = ["a[href*='/dp/']", ".s-result-item a[href*='/dp/']", "a[href*='/gp/product/']"]
            for selector in selectors:
                links = search_soup.select(selector)
                if links:
                    # Take the FIRST result, just like basic scraper
                    product_link = links[0].get('href', '')
                    if product_link and '/dp/' in product_link:
                        break
                        
        elif "bestbuy" in website_name.lower():
            selectors = [
                ".sku-item .sku-header a", 
                "h4.sku-header a",
                ".product-title a",
                "a[href*='/site/'][href*='.p?']"
            ]
            for selector in selectors:
                links = search_soup.select(selector)
                if links:
                    # Take the FIRST result
                    product_link = links[0].get('href', '')
                    if product_link and '/site/' in product_link:
                        break
                    
        elif "walmart" in website_name.lower():
            selectors = ["a[href*='/ip/']", "[data-testid='product-title']"]
            for selector in selectors:
                elements = search_soup.select(selector)
                if elements:
                    element = elements[0]
                    href = element.get('href', '') if hasattr(element, 'get') else ''
                    if not href and hasattr(element, 'find_parent'):
                        parent_link = element.find_parent('a')
                        if parent_link:
                            href = parent_link.get('href', '')
                    
                    if href and '/ip/' in href:
                        product_link = href
                        break
                        
        elif "newegg" in website_name.lower():
            selectors = [
                ".item-title", 
                "a.item-title",
                ".item-container .item-title",
                "a[href*='/Product/Product.aspx']"
            ]
            for selector in selectors:
                links = search_soup.select(selector)
                if links:
                    # Take the FIRST result
                    product_link = links[0].get('href', '')
                    if product_link:
                        break
        else:
            selectors = ["a[href*='/product']", "a[href*='/item']", ".product-item a"]
            for selector in selectors:
                links = search_soup.select(selector)
                if links:
                    product_link = links[0].get('href', '')
                    if product_link:
                        break
        
        # If no product link found, try LLM on search page
        if not product_link:
            print("🤖 No product link found, analyzing search page directly...")
            search_data = extract_product_data_with_llm(search_res.text, website_name, query)
            
            if "error" not in search_data and search_data.get("title") and search_data.get("title") != "Not found":
                return {
                    "website": website_name,
                    "title": search_data.get("title") or "Not found",
                    "price": float(search_data.get("price") or 0),
                    "average_rating": float(search_data.get("average_rating") or 0),
                    "review_count": int(search_data.get("review_count") or 0)
                }
            else:
                return {"website": website_name, "error": "No product found on search page"}
        
        # Build full product URL
        if not product_link.startswith('http'):
            product_link = urljoin(search_url, product_link)
        
        print(f"📍 Found product URL: {product_link[:100]}...")
        
        # Get product page
        time.sleep(random.uniform(2, 4))
        product_res = requests.get(product_link, headers=headers, timeout=20)
        product_res.raise_for_status()
        
        # Use LLM to extract product data
        extracted_data = extract_product_data_with_llm(product_res.text, website_name, query)
        
        if "error" in extracted_data:
            return {"website": website_name, "error": extracted_data["error"]}
        
        return {
            "website": website_name,
            "title": extracted_data.get("title") or "Not found",
            "price": float(extracted_data.get("price") or 0),
            "average_rating": float(extracted_data.get("average_rating") or 0),
            "review_count": int(extracted_data.get("review_count") or 0)
        }
    
    except requests.exceptions.Timeout:
        return {"website": website_name, "error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"website": website_name, "error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"website": website_name, "error": f"Unexpected error: {str(e)}"}

def llm_scrape(product_name: str) -> list:
    """Main LLM scraping function for all websites"""
    results = []
    query = product_name.replace(" ", "+")
    
    # Define websites to scrape
    websites = [
        {
            "name": "Amazon.com",
            "search_url": f"https://www.amazon.com/s?k={query}"
        },
        {
            "name": "BestBuy.com", 
            "search_url": f"https://www.bestbuy.com/site/searchpage.jsp?st={query}"
        },
        {
            "name": "Walmart.com",
            "search_url": f"https://www.walmart.com/search?q={query}"
        },
        {
            "name": "Newegg.com",
            "search_url": f"https://www.newegg.com/p/pl?d={query}"
        }
    ]
    
    for website in websites:
        result = llm_scrape_website(query, website["name"], website["search_url"])
        results.append(result)
        
        # Add delay between sites to be respectful
        time.sleep(random.uniform(3, 6))
    
    return results

def test_gemini_api():
    """Test if Gemini API is working"""
    try:
        test_prompt = "Please respond with exactly this text: API_TEST_SUCCESS"
        response = call_gemini_api(test_prompt)
        if "API_TEST_SUCCESS" in response:
            print("✅ Gemini API is working correctly!")
            return True
        else:
            print(f"⚠️ Gemini API responded but with unexpected content: {response}")
            return False
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

def compare_scraping_methods(product_name: str):
    """Compare LLM scraping results"""
    print(f"🔬 LLM SCRAPING FOR: {product_name}")
    print("=" * 80)
    
    # Test API first
    if not test_gemini_api():
        print("❌ Cannot proceed - Gemini API is not working")
        return
    
    print("\n🤖 LLM SCRAPING RESULTS:")
    print("-" * 40)
    llm_results = llm_scrape(product_name)
    
    for result in llm_results:
        print(f"\n{result['website']}:")
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  📝 Title: {result['title'][:60]}{'...' if len(result['title']) > 60 else ''}")
            print(f"  💰 Price: ${result['price']:.2f}")
            print(f"  ⭐ Rating: {result['average_rating']:.1f}/5.0")
            print(f"  💬 Reviews: {result['review_count']:,}")

# Test function
def test_llm_scraper():
    product_name = "Lenovo Tab P12-2024"
    compare_scraping_methods(product_name)

if __name__ == "__main__":
    test_llm_scraper()