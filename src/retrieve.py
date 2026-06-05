import os
from openai import OpenAI # type: ignore
import psycopg2 # type: ignore 
from dotenv import load_dotenv # type: ignore 

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

def embed_query(query):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding

def retrieve(query, top_k=5, ticker_filter=None):
    embedding = embed_query(query)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    base_sql = """
        select ticker, year, section, content,
               1 - (embedding <=> %s::vector) as similarity
        from filing_chunks
    """
    params = [embedding]
    
    if ticker_filter:
        base_sql += " where ticker = any(%s)"
        params.append(ticker_filter)
    
    base_sql += " order by embedding <=> %s::vector limit %s"
    params.extend([embedding, top_k])
    
    cur.execute(base_sql, params)
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return [
        {
            "ticker": r[0], "year": r[1], "section": r[2],
            "content": r[3], "similarity": r[4]
        }
        for r in results
    ]

if __name__ == "__main__":
    test_queries = [
        "How does Microsoft describe risks from artificial intelligence?",
        "What are the main business segments of Amazon?",
        "How do banks describe interest rate risk?",
    ]
    
    for q in test_queries:
        print(f"\n=== {q} ===")
        results = retrieve(q, top_k=3)
        for r in results:
            print(f"  [{r['ticker']} {r['year']} {r['section']}] sim={r['similarity']:.3f}")
            print(f"    {r['content'][:200]}...")