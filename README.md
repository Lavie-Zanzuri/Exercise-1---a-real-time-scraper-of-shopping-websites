# Product Price Scraper

A full-stack web app that compares a product's price across **Amazon, Best Buy, Walmart and Newegg** in real time. You type in a product name, choose a scraping method, and get the title, price, rating and number of reviews from each store. The results can be sorted by price.

## Three scraping methods

| Method | How it works |
|---|---|
| **Basic** | Classic scraping with Requests, BeautifulSoup and Selenium (undetected-chromedriver) to handle JavaScript-heavy pages |
| **LLM** | Sends the page content to the Google Gemini API and lets the model extract the product data |
| **Firecrawl** | Uses the Firecrawl API to get JS-rendered, clean page content, then extracts the data from it |

Each method handles real-world scraping problems differently, such as bot detection, CAPTCHA pages, dynamic content and inconsistent page layouts.

## Tech stack

**Backend:** Python · FastAPI · Pydantic · Selenium · BeautifulSoup · Google Gemini API · Firecrawl API
**Frontend:** Next.js 15 · React · TypeScript · Tailwind CSS

## Project structure

```
main.py               # FastAPI server (POST /scrape, GET /methods, GET /health)
Basic_scraping.py     # Requests + BeautifulSoup + Selenium
LLM_scraping.py       # Gemini-based extraction
Firecrawl.py          # Firecrawl-based extraction
scraper-frontend/     # Next.js + TypeScript + Tailwind UI
```

## Getting started

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is ignored by git):

```
GEMINI_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
```

Run the API:

```bash
python main.py
```

The API runs at `http://localhost:8001`, and the interactive docs are at `http://localhost:8001/docs`.

### Frontend

```bash
cd scraper-frontend
npm install
npm run dev
```

Then open `http://localhost:3000`.