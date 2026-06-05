import re

TICKER_MAP = {
    # Tech
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL",
    "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "facebook": "META",
    "apple": "AAPL", "aapl": "AAPL",
    # Finance
    "jpmorgan": "JPM", "jp morgan": "JPM", "jpm": "JPM",
    "goldman": "GS", "goldman sachs": "GS",
    "blackrock": "BLK", "blk": "BLK",
    "visa": "V",
    "mastercard": "MA",
    # Retail
    "walmart": "WMT", "wmt": "WMT",
    "target": "TGT", "tgt": "TGT",
    "costco": "COST",
    "home depot": "HD",
    "lowe's": "LOW", "lowes": "LOW", "lowe": "LOW",
}

INDUSTRY_MAP = {
    "tech": ["MSFT", "GOOGL", "AMZN", "META", "AAPL"],
    "technology": ["MSFT", "GOOGL", "AMZN", "META", "AAPL"],
    "bank": ["JPM", "GS"],
    "banks": ["JPM", "GS"],
    "financial": ["JPM", "GS", "BLK", "V", "MA"],
    "finance": ["JPM", "GS", "BLK", "V", "MA"],
    "retail": ["WMT", "TGT", "COST", "HD", "LOW"],
    "retailer": ["WMT", "TGT", "COST", "HD", "LOW"],
    "retailers": ["WMT", "TGT", "COST", "HD", "LOW"],
}

def extract_tickers(question):
    """Return list of tickers mentioned in the question, or None if none found."""
    q_lower = question.lower()
    tickers = set()
    
    # Sort by length descending so multi-word names match before single words
    for name in sorted(TICKER_MAP.keys(), key=len, reverse=True):
        # Word boundary match
        if re.search(r"\b" + re.escape(name) + r"\b", q_lower):
            tickers.add(TICKER_MAP[name])
    
    # Industry expansion (only if no specific companies mentioned)
    if not tickers:
        for industry, ticker_list in INDUSTRY_MAP.items():
            if re.search(r"\b" + industry + r"\b", q_lower):
                tickers.update(ticker_list)
    
    return sorted(tickers) if tickers else None

if __name__ == "__main__":
    tests = [
        "How does Microsoft describe AI risks?",
        "What are Amazon's main business segments?",
        "Compare JPMorgan and Goldman Sachs on interest rate risk",
        "How do banks describe regulatory risk?",
        "What does Meta say about VR?",
        "Tell me about retail competition",
    ]
    for q in tests:
        print(f"{q}\n  -> {extract_tickers(q)}")