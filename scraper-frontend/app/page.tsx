'use client'

import { useState } from 'react'

interface ProductResult {
  website: string
  title: string
  price: number
  average_rating: number
  review_count: number
  error?: string
}

interface ScrapeResponse {
  success: boolean
  results: ProductResult[]
  method_used: string
  total_sites: number
  successful_sites: number
  errors?: string[]
}

interface ScrapingMethod {
  id: string
  name: string
  description: string
}

export default function ProductScraper() {
  const [productName, setProductName] = useState<string>('')
  const [scrapingMethod, setScrapingMethod] = useState<string>('basic')
  const [loading, setLoading] = useState<boolean>(false)
  const [results, setResults] = useState<ScrapeResponse | null>(null)
  const [error, setError] = useState<string>('')

  const scrapingMethods: ScrapingMethod[] = [
    { id: 'basic', name: 'Basic Scraping', description: 'Requests + BeautifulSoup' },
    { id: 'llm', name: 'LLM Scraping', description: 'AI-powered extraction' },
    { id: 'firecrawl', name: 'Firecrawl', description: 'Firecrawl API service' }
  ]

  const handleScrape = async (): Promise<void> => {
    if (!productName.trim()) {
      setError('Please enter a product name')
      return
    }

    setLoading(true)
    setError('')
    setResults(null)

    try {
      const response = await fetch('http://localhost:8001/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_name: productName,
          scraping_method: scrapingMethod
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ScrapeResponse = await response.json()
      setResults(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(`Failed to scrape: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            🛍️ Product Price Scraper
          </h1>
          
          <div className="space-y-6 mb-8">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Product Name
              </label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="e.g., iPhone 15, Lenovo Tab P12-2024"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scraping Method
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {scrapingMethods.map((method) => (
                  <div key={method.id}>
                    <input
                      type="radio"
                      id={method.id}
                      name="scraping_method"
                      value={method.id}
                      checked={scrapingMethod === method.id}
                      onChange={(e) => setScrapingMethod(e.target.value)}
                      className="sr-only"
                    />
                    <label
                      htmlFor={method.id}
                      className={`block p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        scrapingMethod === method.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="font-medium text-gray-900">{method.name}</div>
                      <div className="text-sm text-gray-500">{method.description}</div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleScrape}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Scraping...
                </div>
              ) : (
                'Scrape Products'
              )}
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="text-red-800">❌ {error}</div>
            </div>
          )}

          {results && (
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h2 className="text-xl font-semibold mb-2 text-gray-900">Scraping Results</h2>
                <div className="text-sm text-gray-600">
                  Method: <span className="font-medium">{results.method_used}</span> | 
                  Success: <span className="font-medium">{results.successful_sites}/{results.total_sites}</span> sites
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 px-4 py-2 text-left text-gray-900">Website</th>
                      <th className="border border-gray-300 px-4 py-2 text-left text-gray-900">Product Title</th>
                      <th className="border border-gray-300 px-4 py-2 text-left text-gray-900">Price (USD)</th>
                      <th className="border border-gray-300 px-4 py-2 text-left text-gray-900">Rating</th>
                      <th className="border border-gray-300 px-4 py-2 text-left text-gray-900">Reviews</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.results.map((result, index) => (
                      <tr key={index} className={result.error ? 'bg-red-50' : 'bg-white'}>
                        <td className="border border-gray-300 px-4 py-2 font-medium text-gray-900">
                          {result.website}
                        </td>
                        <td className="border border-gray-300 px-4 py-2">
                          {result.error ? (
                            <span className="text-red-600">❌ {result.error}</span>
                          ) : (
                            <span className="text-sm text-gray-900">{result.title}</span>
                          )}
                        </td>
                        <td className="border border-gray-300 px-4 py-2 text-gray-900">
                          {result.error ? '-' : `$${result.price.toFixed(2)}`}
                        </td>
                        <td className="border border-gray-300 px-4 py-2 text-gray-900">
                          {result.error ? '-' : `${result.average_rating.toFixed(1)}/5.0`}
                        </td>
                        <td className="border border-gray-300 px-4 py-2 text-gray-900">
                          {result.error ? '-' : result.review_count.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {results.errors && results.errors.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-800 mb-2">⚠️ Errors Encountered:</h3>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {results.errors.map((error, index) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}