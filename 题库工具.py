# -*- coding: utf-8 -*-
"""官方题库读取与抽样工具 v1（固定种子，可复现）
SimpleQA: simple_qa_test_set.csv（列 metadata/problem/answer）
TruthfulQA: TruthfulQA.csv（列 Type/Category/Question/Best Answer/...）
IFEval: input_data.jsonl（字段 prompt/instruction_id_list）
MT-Bench: mt_bench_question.jsonl（字段 question_id/category/turns）
输出: 官方题库抽样/ 下各来源 JSONL + 控制台预览。"""
import csv, json, random, pathlib, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = pathlib.Path(__file__).parent
OUT = BASE / "官方题库抽样"
OUT.mkdir(exist_ok=True)
SEED = 20260820

def sample(items, n, seed):
    rng = random.Random(seed)
    return rng.sample(items, min(n, len(items)))

def parse_simpleqa(path):
    rows = []
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            rows.append({"source": "SimpleQA", "problem": r["problem"].strip(), "answer": r["answer"].strip()})
    return rows

def parse_truthfulqa(path):
    rows = []
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            rows.append({"source": "TruthfulQA", "problem": r["Question"].strip(), "answer": r["Best Answer"].strip()})
    return rows

def parse_ifeval(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            j = json.loads(line)
            rows.append({"source": "IFEval", "problem": j["prompt"].strip(), "answer": ""})
    return rows

def parse_mtbench(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            j = json.loads(line)
            first_turn = j["turns"][0] if j.get("turns") else ""
            rows.append({"source": "MTBench", "problem": first_turn.strip(), "answer": ""})
    return rows

candidates = [
    ("simple_qa_test_set.csv", parse_simpleqa, 30),
    ("TruthfulQA.csv", parse_truthfulqa, 20),
    ("input_data.jsonl", parse_ifeval, 20),
    ("mt_bench_question.jsonl", parse_mtbench, 10),
]

all_out = []
for fname, parser, n in candidates:
    p = BASE / fname
    if not p.exists():
        print(f"[缺] {fname} —— 下载后放本目录即可自动纳入")
        continue
    rows = parser(p)
    chosen = sample(rows, n, SEED + hash(fname) % 1000)
    out = OUT / (fname.split(".")[0] + f"_抽{n}.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in chosen:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    all_out.extend(chosen)
    print(f"[OK] {fname}: 全量 {len(rows)} 题 → 抽样 {len(chosen)} 题 → {out.name}")
    print("   预览: " + chosen[0]["problem"][:120] + " ｜答: " + chosen[0]["answer"][:80])

print("总抽样:", len(all_out), "题（固定种子", SEED, "可复现）")