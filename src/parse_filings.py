import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json

FILINGS_DIR = Path("filings/sec-edgar-filings")
OUTPUT_FILE = Path("data/parsed_filings.json")

SECTIONS = {
    "business": (
        r"item\s*[\u00a0\s]*1[\.\s]*(?:business)?(?!\s*a)",
        r"item\s*[\u00a0\s]*(?:1\s*a|1\s*b|2[\.\s])"
    ),
    "risk_factors": (
        r"item\s*[\u00a0\s]*1\s*a[\.\s]*(?:risk\s*factors)?",
        r"item\s*[\u00a0\s]*(?:1\s*b|2[\.\s]|3[\.\s])"
    ),
    "mda": (
        r"item\s*[\u00a0\s]*7[\.\s]*(?:management)?(?!\s*a)",
        r"item\s*[\u00a0\s]*(?:7\s*a|8[\.\s])"
    ),
}

def extract_10k_document(raw):
    """SEC full-submission.txt contains multiple <DOCUMENT> blocks.
    Find the one with <TYPE>10-K (not 10-K/A, not exhibits, not XBRL)."""
    doc_pattern = re.compile(
        r"<DOCUMENT>(.*?)</DOCUMENT>", re.DOTALL | re.IGNORECASE
    )
    type_pattern = re.compile(r"<TYPE>([^\n<]+)", re.IGNORECASE)
    
    for match in doc_pattern.finditer(raw):
        doc_content = match.group(1)
        type_match = type_pattern.search(doc_content)
        if type_match:
            doc_type = type_match.group(1).strip().upper()
            if doc_type == "10-K":
                return doc_content
    return None

def html_to_text(html_content):
    """Convert HTML to clean text, removing tables and scripts."""
    soup = BeautifulSoup(html_content, "lxml")
    
    # Remove tables (they're mostly financial data, noisy for retrieval)
    for tag in soup(["script", "style"]):
        tag.decompose()
    
    text = soup.get_text(separator=" ")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove non-breaking spaces
    text = text.replace("\u00a0", " ")
    return text

def extract_section(text, start_pattern, end_pattern):
    """Find section between two Item markers, taking the LAST start match
    (which skips TOC entries) and the first end match after it."""
    text_lower = text.lower()
    
    start_matches = list(re.finditer(start_pattern, text_lower))
    if not start_matches:
        return None
    
    # Use last start match — earlier ones are usually in the table of contents
    start_match = start_matches[-1]
    
    end_search = re.search(end_pattern, text_lower[start_match.end():])
    if end_search:
        section = text[start_match.start():start_match.end() + end_search.start()]
    else:
        # Cap at 100k chars if no end found
        section = text[start_match.start():start_match.start() + 100000]
    
    return section.strip()

def parse_filing(filepath, ticker, accession):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    
    # Extract just the 10-K document from the submission envelope
    doc_content = extract_10k_document(raw)
    if not doc_content:
        return None
    
    text = html_to_text(doc_content)
    
    result = {
        "ticker": ticker,
        "accession": accession,
        "sections": {}
    }
    
    for section_name, (start, end) in SECTIONS.items():
        section_text = extract_section(text, start, end)
        if section_text and len(section_text) > 1000:
            result["sections"][section_name] = section_text
    
    year_match = re.search(r"-(\d{2})-", accession)
    if year_match:
        yy = int(year_match.group(1))
        result["year"] = 2000 + yy if yy < 50 else 1900 + yy
    
    return result

def main():
    parsed = []
    
    for ticker_dir in FILINGS_DIR.iterdir():
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        
        tenk_dir = ticker_dir / "10-K"
        if not tenk_dir.exists():
            continue
        
        for accession_dir in tenk_dir.iterdir():
            filing_file = accession_dir / "full-submission.txt"
            if not filing_file.exists():
                continue
            
            print(f"Parsing {ticker} / {accession_dir.name}...")
            try:
                result = parse_filing(filing_file, ticker, accession_dir.name)
                if result is None:
                    print(f"  No 10-K document found in submission")
                    continue
                sections_found = {
                    k: len(v) for k, v in result["sections"].items()
                }
                print(f"  Sections: {sections_found}")
                parsed.append(result)
            except Exception as e:
                print(f"  ERROR: {e}")
    
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)
    
    print(f"\nParsed {len(parsed)} filings -> {OUTPUT_FILE}")
    
    section_counts = {"business": 0, "risk_factors": 0, "mda": 0}
    total_chars = {"business": 0, "risk_factors": 0, "mda": 0}
    for p in parsed:
        for s, content in p["sections"].items():
            section_counts[s] += 1
            total_chars[s] += len(content)
    
    print(f"Section coverage: {section_counts}")
    print(f"Avg section length (chars):")
    for s in section_counts:
        if section_counts[s] > 0:
            avg = total_chars[s] // section_counts[s]
            print(f"  {s}: {avg:,}")

if __name__ == "__main__":
    main()