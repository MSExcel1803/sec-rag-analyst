import os
import psycopg2
from dotenv import load_dotenv
from retrieve import retrieve

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Check 1: How many chunks per ticker actually in DB?
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("select ticker, count(*) from filing_chunks group by ticker order by ticker")
print("=== Chunks per ticker in DB ===")
for ticker, count in cur.fetchall():
    print(f"  {ticker}: {count}")
cur.close()
conn.close()

# Check 2: Try retrieval with each ticker filter
print("\n=== Retrieval test with ticker filter ===")
test_cases = [
    ("Amazon business segments", ["AMZN"]),
    ("Meta regulatory EU", ["META"]),
    ("retail supply chain", ["COST", "HD", "LOW", "TGT", "WMT"]),
    ("JPMorgan Goldman interest rate", ["GS", "JPM"]),
]
for query, tickers in test_cases:
    results = retrieve(query, top_k=5, ticker_filter=tickers)
    print(f"\nQuery: {query}")
    print(f"Filter: {tickers}")
    print(f"Results: {len(results)} chunks")
    for r in results[:3]:
        print(f"  [{r['ticker']} {r['year']} {r['section']}] sim={r['similarity']:.3f}")