from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import sys
import os

# Add the current directory to Python path so we can import our scrapers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your scraping modules
try:
    # Import with the EXACT file names you have
    from Basic_scraping import basic_scrape
    from LLM_scraping import llm_scrape  
    from Firecrawl import enhanced_firecrawl_scrape
    print("✅ All scraping modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all scraping files are in the same directory as this server file")
    print("Your files are: Basic_scraping.py, LLM_scraping.py, Firecrawl.py")

app = FastAPI(title="Product Scraper API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    product_name: str
    scraping_method: str  # "basic", "llm", or "firecrawl"

class ProductResult(BaseModel):
    website: str
    title: str
    price: float
    average_rating: float
    review_count: int
    error: str = None

class ScrapeResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    method_used: str
    total_sites: int
    successful_sites: int
    errors: List[str] = []

@app.get("/")
async def root():
    return {
        "message": "Product Scraper API",
        "version": "1.0.0",
        "available_methods": ["basic", "llm", "firecrawl"],
        "endpoints": ["/scrape", "/health"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_product(request: ScrapeRequest):
    """
    Scrape product information using the specified method
    """
    try:
        product_name = request.product_name.strip()
        method = request.scraping_method.lower()
        
        if not product_name:
            raise HTTPException(status_code=400, detail="Product name cannot be empty")
        
        if method not in ["basic", "llm", "firecrawl"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid scraping method. Must be 'basic', 'llm', or 'firecrawl'"
            )
        
        print(f"🚀 Starting {method} scraping for: {product_name}")
        
        results = []
        errors = []
        
        # Route to appropriate scraping method
        if method == "basic":
            try:
                results = basic_scrape(product_name)
            except Exception as e:
                errors.append(f"Basic scraping failed: {str(e)}")
                
        elif method == "llm":
            try:
                results = llm_scrape(product_name)
            except Exception as e:
                errors.append(f"LLM scraping failed: {str(e)}")
                
        elif method == "firecrawl":
            try:
                results = enhanced_firecrawl_scrape(product_name)
            except Exception as e:
                errors.append(f"Firecrawl scraping failed: {str(e)}")
        
        # Process results
        successful_sites = 0
        processed_results = []
        
        for result in results:
            if isinstance(result, dict):
                if "error" not in result:
                    successful_sites += 1
                    # Ensure all required fields are present
                    processed_result = {
                        "website": result.get("website", "Unknown"),
                        "title": result.get("title", "Title not found"),
                        "price": float(result.get("price", 0.0)),
                        "average_rating": float(result.get("average_rating", 0.0)),
                        "review_count": int(result.get("review_count", 0)),
                        "error": None
                    }
                else:
                    processed_result = {
                        "website": result.get("website", "Unknown"),
                        "title": "Error occurred",
                        "price": 0.0,
                        "average_rating": 0.0,
                        "review_count": 0,
                        "error": result.get("error", "Unknown error")
                    }
                    errors.append(f"{result.get('website', 'Unknown')}: {result.get('error', 'Unknown error')}")
                
                processed_results.append(processed_result)
        
        total_sites = len(processed_results)
        success = successful_sites > 0 or len(errors) == 0
        
        print(f"✅ Scraping completed: {successful_sites}/{total_sites} sites successful")
        
        return ScrapeResponse(
            success=success,
            results=processed_results,
            method_used=method,
            total_sites=total_sites,
            successful_sites=successful_sites,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/methods")
async def get_scraping_methods():
    """Get available scraping methods with descriptions"""
    return {
        "methods": [
            {
                "id": "basic",
                "name": "Basic Scraping",
                "description": "Uses requests + BeautifulSoup with hardcoded selectors"
            },
            {
                "id": "llm", 
                "name": "LLM Scraping",
                "description": "Uses AI (Gemini) to extract data from HTML content"
            },
            {
                "id": "firecrawl",
                "name": "Firecrawl API",
                "description": "Uses Firecrawl service for automated content extraction"
            }
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Product Scraper API...")
    print("📍 API will be available at: http://localhost:8001")  # Changed port
    print("📖 API docs will be available at: http://localhost:8001/docs")
    
    uvicorn.run(
        "main:app",  # Change this to match your filename
        host="0.0.0.0",
        port=8001,  # Changed from 8000 to 8001
        reload=True,
        log_level="info"
    )