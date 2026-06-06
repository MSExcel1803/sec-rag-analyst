import json
from pathlib import Path
from collections import defaultdict

with open("data/eval_questions.json") as f:
    questions = {q["id"]: q for q in json.load(f)}
with open("data/scores.json") as f:
    scores = json.load(f)

# Overall
total = len(scores)
correct = sum(1 for s in scores.values() if s["score"] == "correct")
partial = sum(1 for s in scores.values() if s["score"] == "partial")
incorrect = sum(1 for s in scores.values() if s["score"] == "incorrect")

# By type
by_type = defaultdict(lambda: {"correct": 0, "partial": 0, "incorrect": 0, "total": 0})
for qid, score in scores.items():
    qtype = questions[int(qid)]["type"]
    by_type[qtype][score["score"]] += 1
    by_type[qtype]["total"] += 1

print(f"=== Overall ===")
print(f"Total: {total}")
print(f"Correct: {correct} ({correct/total*100:.0f}%)")
print(f"Partial: {partial} ({partial/total*100:.0f}%)")
print(f"Incorrect: {incorrect} ({incorrect/total*100:.0f}%)")
print(f"\nAccuracy (correct + 0.5*partial): {(correct + 0.5*partial)/total*100:.1f}%")

print(f"\n=== By Question Type ===")
for qtype, counts in by_type.items():
    acc = (counts["correct"] + 0.5*counts["partial"]) / counts["total"] * 100
    print(f"{qtype}: {acc:.0f}% ({counts['correct']}/{counts['total']} correct, {counts['partial']} partial)")