import os
from anthropic import Anthropic
from dotenv import load_dotenv
from retrieve import retrieve
from company_filter import extract_tickers

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are a financial analyst assistant that answers questions about public companies using ONLY the provided excerpts from their SEC 10-K filings.

Rules:
1. Base every claim on the provided excerpts. Do not use outside knowledge.
2. Cite sources inline using the format [TICKER YEAR SECTION], for example [MSFT 2024 risk_factors].
3. If the excerpts do not contain enough information to answer, say "The provided filings don't contain enough information to answer this question" and explain what's missing.
4. When comparing companies, structure the answer clearly with each company's position discussed separately, then synthesize.
5. Keep answers concise and analytical. Avoid hedging language unless the filings themselves hedge.
6. Quote directly from filings only for short phrases that carry legal or specific weight. Otherwise paraphrase.
"""

def format_context(chunks):
    """Format retrieved chunks for the LLM prompt."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        header = f"[Excerpt {i}: {c['ticker']} {c['year']} {c['section']}]"
        blocks.append(f"{header}\n{c['content']}")
    return "\n\n".join(blocks)

def answer_question(question, top_k=8):
    """End-to-end: detect companies, retrieve, generate answer."""
    tickers = extract_tickers(question)
    
    chunks = retrieve(question, top_k=top_k, ticker_filter=tickers)
    
    if not chunks:
        return {
            "answer": "No relevant excerpts were found in the filings.",
            "chunks": [],
            "tickers_used": tickers,
        }
    
    context = format_context(chunks)
    
    user_message = f"""Question: {question}

Excerpts from 10-K filings:

{context}

Answer the question using only these excerpts. Cite sources inline like [TICKER YEAR SECTION]."""
    
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    
    answer_text = response.content[0].text
    
    return {
        "answer": answer_text,
        "chunks": chunks,
        "tickers_used": tickers,
    }

if __name__ == "__main__":
    questions = [
        "How does Microsoft describe risks from artificial intelligence?",
        "Compare how JPMorgan and Goldman Sachs discuss interest rate risk.",
    ]
    for q in questions:
        print(f"\n{'='*70}\nQ: {q}\n{'='*70}")
        result = answer_question(q)
        print(f"Tickers detected: {result['tickers_used']}")
        print(f"Chunks retrieved: {len(result['chunks'])}")
        print(f"\nAnswer:\n{result['answer']}")