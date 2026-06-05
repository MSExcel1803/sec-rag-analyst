import os
import json
import time
from pathlib import Path
from openai import OpenAI # type: ignore
import psycopg2 # type: ignore
import tiktoken # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DATABASE_URL = os.getenv("DATABASE_URL")

PARSED_FILE = Path("data/parsed_filings.json")
CHUNK_TOKENS = 600
CHUNK_OVERLAP = 80
EMBED_MODEL = "text-embedding-3-small"

encoder = tiktoken.get_encoding("cl100k_base")

def chunk_text(text, chunk_tokens=CHUNK_TOKENS, overlap=CHUNK_OVERLAP):
    """Split text into overlapping token chunks."""
    tokens = encoder.encode(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_token_ids = tokens[i:i + chunk_tokens]
        chunk_text = encoder.decode(chunk_token_ids)
        chunks.append(chunk_text)
        i += chunk_tokens - overlap
    return chunks

def embed_batch(texts):
    """Embed a list of texts in one API call."""
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [d.embedding for d in response.data]

def main():
    print("Starting...")
    with open(PARSED_FILE, "r", encoding="utf-8") as f:
        parsed = json.load(f)
    print(f"Loaded {len(parsed)} filings from JSON")
    
    # Build chunk list
    all_chunks = []
    for filing in parsed:
        ticker = filing["ticker"]
        year = filing.get("year")
        for section_name, section_text in filing["sections"].items():
            chunks = chunk_text(section_text)
            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "ticker": ticker,
                    "year": year,
                    "section": section_name,
                    "chunk_index": idx,
                    "content": chunk
                })
    
    print(f"Total chunks to embed: {len(all_chunks)}")
    
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    print("Connected.")
    cur = conn.cursor()
    
    print(f"Total chunks to embed: {len(all_chunks)}")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    BATCH = 100
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i:i + BATCH]
        texts = [c["content"] for c in batch]
        
        try:
            embeddings = embed_batch(texts)
        except Exception as e:
            print(f"Embed error at batch {i}: {e}, retrying in 5s...")
            time.sleep(5)
            embeddings = embed_batch(texts)
        
        for c, emb in zip(batch, embeddings):
            cur.execute(
                """insert into filing_chunks 
                   (ticker, year, section, chunk_index, content, embedding)
                   values (%s, %s, %s, %s, %s, %s)""",
                (c["ticker"], c["year"], c["section"], c["chunk_index"], 
                 c["content"], emb)
            )
        conn.commit()
        print(f"  Inserted {min(i + BATCH, len(all_chunks))} / {len(all_chunks)}")
    
    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()