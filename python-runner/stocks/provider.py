import yfinance as yf
import httpx
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import urllib.parse

logger = logging.getLogger(__name__)

async def search_assets(query: str) -> List[Dict]:
    """
    Search for stocks using Yahoo Finance Autocomplete API, 
    with fallbacks to Web Scraping and Exact Ticker lookup.
    """
    # Strategy 1: Autocomplete API
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {
        "q": query,
        "lang": "en-US",
        "region": "US",
        "quotesCount": 10,
        "newsCount": 0,
        "enableFuzzyQuery": "false",
        "enableCb": "true",
        "enableNavLinks": "true",
        "enableEnhancedTrivialQuery": "true"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://finance.yahoo.com",
        "Referer": "https://finance.yahoo.com/"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for quote in data.get("quotes", []):
                    if quote.get("quoteType") not in ["EQUITY", "ETF", "MUTUALFUND"]:
                        continue
                    results.append({
                        "symbol": quote["symbol"],
                        "name": quote.get("shortname", quote.get("longname", quote["symbol"])),
                        "exchange": quote.get("exchange"),
                        "type": quote.get("quoteType"),
                        "thumb": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Infobox_info_icon.svg"
                    })
                if results:
                    return results
            else:
                logger.warning(f"Yahoo search API failed ({resp.status_code}), trying scraper...")
        
        except Exception as e:
            logger.warning(f"Yahoo search API error ({e})")
            
        # Strategy 2: Web Scraping - DISABLED (Unreliable, picks up trending tickers)
        # Proceed directly to ticker lookup fallback


        # Strategy 3: Exact Ticker Lookup (Last Resort)
        try:
            # Force uppercase and strip for ticker lookup
            clean_query = query.strip().upper()
            logger.info(f"Strategy 3: Trying exact ticker lookup for '{clean_query}'")
            
            details = get_asset_details(clean_query)
            if details:
                logger.info(f"Strategy 3: Found details for '{clean_query}'")
                return [{
                    "symbol": details['symbol'],
                    "name": details['name'],
                    "exchange": "UNKNOWN",
                    "type": "EQUITY",
                    "thumb": "https://upload.wikimedia.org/wikipedia/commons/e/e4/Infobox_info_icon.svg"
                }]
            else:
                logger.warning(f"Strategy 3: No details found for '{clean_query}'")
        except Exception as e:
            logger.error(f"Strategy 3 error: {e}")
            pass
            
        return []

def get_asset_details(symbol: str) -> Optional[Dict]:
    """
    Get detailed breakdown for a symbol using yfinance.
    Blocking call (run in executor if needed).
    """
    try:
        logger.info(f"get_asset_details called for {symbol}")
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Fast exit if no data
        if not info:
             logger.warning(f"get_asset_details: Info empty for {symbol}")
             return None
             
        if 'regularMarketPrice' not in info:
            logger.warning(f"get_asset_details: No regularMarketPrice for {symbol}, checking history")
            # Fallback for some ETFs or weird tickers
            hist = ticker.history(period="1d")
            if hist.empty:
                logger.warning(f"get_asset_details: History empty for {symbol}")
                return None
            price = hist["Close"].iloc[-1]
        else:
            price = info.get("regularMarketPrice")

        return {
            "symbol": symbol,
            "name": info.get("shortName") or info.get("longName") or symbol,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency", "USD"),
            "price": price,
            "market_cap": info.get("marketCap"),
            "volume": info.get("volume"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow")
        }
    except Exception as e:
        logger.error(f"Error fetching details for {symbol}: {e}")
        return None
