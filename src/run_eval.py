import json
import time
from pathlib import Path
from answer import answer_question

EVAL_FILE = Path("data/eval_questions.json")
RESULTS_FILE = Path("data/eval_results.json")

def main():
    with open(EVAL_FILE, "r") as f:
        questions = json.load(f)
    
    results = []
    for q in questions:
        print(f"\n[{q['id']}/{len(questions)}] {q['type']}: {q['question']}")
        try:
            result = answer_question(q["question"], top_k=10)
            results.append({
                "id": q["id"],
                "question": q["question"],
                "type": q["type"],
                "expected": q["expected"],
                "answer": result["answer"],
                "tickers_used": result["tickers_used"],
                "chunks_retrieved": len(result["chunks"]),
                "top_tickers_retrieved": list(set(c["ticker"] for c in result["chunks"])),
            })
            print(f"  Tickers: {result['tickers_used']}, Chunks: {len(result['chunks'])}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "id": q["id"],
                "question": q["question"],
                "type": q["type"],
                "expected": q["expected"],
                "error": str(e),
            })
        time.sleep(1)  # be nice to the API
    
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved {len(results)} results to {RESULTS_FILE}")

if __name__ == "__main__":
    main()