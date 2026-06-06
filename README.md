# SEC 10-K Analytics Assistant

A retrieval-augmented analytics tool that answers business and financial questions over the last three years of 10-K filings from 15 large-cap companies across tech, financial services, and retail.

**Live demo:** https://sec-rag-analyst-azrdpa8gsx3vutkokxappnk.streamlit.app

## What it does

Ask natural-language questions about company strategy, risks, business segments, or comparative analysis. The system retrieves relevant excerpts from SEC filings, then uses Claude to synthesize a grounded answer with inline citations like `[MSFT 2024 risk_factors]`. Every claim traces back to a specific filing section the user can expand and verify.

## Stack

- **Embeddings:** OpenAI `text-embedding-3-small`
- **Vector store:** Supabase Postgres with `pgvector` (ivfflat index)
- **Generation:** Anthropic Claude Sonnet 4.5
- **Frontend:** Streamlit
- **Data:** SEC EDGAR via `sec-edgar-downloader`

## Coverage

- **Tech:** MSFT, GOOGL, AMZN, META, AAPL
- **Finance:** JPM, GS, BLK, V, MA
- **Retail:** WMT, TGT, COST, HD, LOW

44 filings, parsed into 1,829 chunks across Business, Risk Factors, and MD&A sections.

## Architecture

1. **Ingestion:** Filings pulled from SEC EDGAR, parsed to extract Item 1, Item 1A, and Item 7 from the 10-K document within each submission envelope.
2. **Chunking:** 600-token chunks with 80-token overlap, preserving section/year/ticker metadata.
3. **Embedding:** Each chunk embedded with `text-embedding-3-small` (1536 dimensions).
4. **Query pipeline:** User question → ticker extraction (company name → ticker mapping) → embedding → filtered cosine similarity search in pgvector → top-k chunks passed to Claude with a grounding system prompt.

## Evaluation

I built a 30-question benchmark across four categories:

- 10 single-company factual questions
- 8 comparative questions (multi-ticker)
- 6 thematic industry-wide questions
- 6 adversarial questions where the answer isn't in the data (testing whether the system hallucinates or honestly refuses)

**Results:** 75% accuracy overall (correct = 1, partial = 0.5, incorrect = 0).

| Question type | Accuracy |
|---------------|----------|
| Factual       | 100%     |
| Comparative   | 50%      |
| Thematic      | 42%      |
| Should-fail   | 100%     |

Common failure modes observed: Comparative and thematic queries underperformed because retrieval without strict ticker filtering returns chunks dominated by companies with the most text in the corpus, starving smaller companies of representation in top-k results. Thematic queries that map to all five companies in an industry are especially affected since the top 10 chunks rarely cover all five evenly. Future work: rerank with a cross-encoder, or retrieve per-ticker and merge results to guarantee coverage.

## Setup

```bash
git clone https://github.com/MSExcel1803/sec-rag-analyst
cd sec-rag-analyst
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Set environment variables in `.env`:

OPENAI_API_KEY=...  

ANTHROPIC_API_KEY=...  

DATABASE_URL=postgresql://...  

Then:

```bash
python src/download_filings.py
python src/parse_filings.py
python src/embed_and_load.py
streamlit run src/app.py
```