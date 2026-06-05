from sec_edgar_downloader import Downloader

# SEC requires a real name and email for rate limiting
dl = Downloader("Harsh", "harshsahu2183@gmail.com", "./filings")

companies = {
    "tech": ["MSFT", "GOOGL", "AMZN", "META", "AAPL"],
    "finance": ["JPM", "GS", "BLK", "V", "MA"],
    "retail": ["WMT", "TGT", "COST", "HD", "LOW"],
}

total = 0
for sector, tickers in companies.items():
    print(f"\n=== {sector.upper()} ===")
    for ticker in tickers:
        print(f"Downloading {ticker}...")
        try:
            count = dl.get("10-K", ticker, limit=3)
            print(f"  Got {count} filings for {ticker}")
            total += count
        except Exception as e:
            print(f"  ERROR for {ticker}: {e}")

print(f"\nDone. Total filings downloaded: {total}")