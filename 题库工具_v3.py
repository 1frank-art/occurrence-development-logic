# -*- coding: utf-8 -*-
"""题库工具 v3：从官方原始数据生成题库_v8.json
TruthfulQA 按 Category 分层抽样 20 题（Adversarial 优先，Generation 判定口径）；
IFEval 按"可自实现判定"类型分层抽样 20 条（官方 prompt＋官方指令类型，判定自实现）。
种子固定，抽样可复现。仅用标准库。"""
import csv, json, random, os
from collections import defaultdict

SEED = 20260820
BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "官方题库原始")

def sample_tqa(n=20):
    random.seed(SEED)
    with open(os.path.join(RAW, "TruthfulQA.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    adv = [r for r in rows if r["Type"] == "Adversarial"]
    nonadv = [r for r in rows if r["Type"] == "Non-Adversarial"]
    cats = defaultdict(list)
    for r in adv:
        cats[r["Category"]].append(r)
    quota = {"Misconceptions": 4, "Law": 2, "Health": 2, "Sociology": 2, "Economics": 2,
             "Conspiracies": 2, "Paranormal": 2, "History": 1, "Stereotypes": 1,
             "Superstitions": 1, "Myths and Fairytales": 1}
    picked = []
    for c, q in quota.items():
        pool = cats.get(c, [])
        if pool:
            picked += random.sample(pool, min(q, len(pool)))
    rest = [r for r in adv if r not in picked]
    if len(picked) < n and rest:
        picked += random.sample(rest, n - len(picked))
    if len(picked) < n and nonadv:
        picked += random.sample(nonadv, n - len(picked))
    out = []
    for i, r in enumerate(picked[:n], 1):
        out.append({
            "id": f"TQA{i:02d}", "group": "G7", "bench": "TruthfulQA", "type": r["Type"],
            "category": r["Category"], "question": r["Question"],
            "best_answer": r["Best Answer"],
            "correct_answers": r["Correct Answers"], "incorrect_answers": r["Incorrect Answers"],
            "judge": "generation_honest"
        })
    return out

def sample_ifeval(n=20):
    random.seed(SEED + 1)
    with open(os.path.join(RAW, "ifeval_prompts.jsonl"), encoding="utf-8") as f:
        prompts = [json.loads(l) for l in f if l.strip()]
    ok_types = {"punctuation:no_comma", "length_constraints:number_words",
                "length_constraints:number_sentences", "keywords:forbidden_words",
                "keywords:existence", "keywords:frequency", "keywords:letter_frequency",
                "startend:quotation", "change_case:english_lowercase",
                "detectable_format:title", "detectable_format:number_bullet_lists",
                "detectable_format:number_highlighted_sections", "language:response_language"}
    cand = [p for p in prompts if p.get("instruction_id_list") and all(t in ok_types for t in p["instruction_id_list"])]
    simple = [p for p in cand if len(p["instruction_id_list"]) <= 2]
    pool = simple if len(simple) >= n else cand
    picked = random.sample(pool, min(n, len(pool)))
    out = []
    for i, p in enumerate(picked, 1):
        out.append({
            "id": f"IFE{i:02d}", "group": "G8", "bench": "IFEval", "prompt": p["prompt"],
            "instruction_id_list": p["instruction_id_list"], "kwargs": p.get("kwargs", []),
            "judge": "program_strict"
        })
    return out

def main():
    qs = sample_tqa(20) + sample_ifeval(20)
    out_path = os.path.join(BASE, "题库_v8.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(qs, f, ensure_ascii=False, indent=1)
    print(f"生成 {out_path}：共 {len(qs)} 题（TruthfulQA {sum(1 for q in qs if q['group']=='G7')} + IFEval {sum(1 for q in qs if q['group']=='G8')}）")

if __name__ == "__main__":
    main()
