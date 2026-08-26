# -*- coding: utf-8 -*-
"""合并工具 v2：G1＝官方抽样（优先中文版v2翻译）；G2-G6＝现有题库_v7.json 的自拟题。"""
import json, pathlib, sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
BASE = pathlib.Path(__file__).parent
SRC = BASE / "官方题库抽样"
if not SRC.exists():
    alt = BASE.parent / "执行版SystemPrompt包" / "官方题库抽样"
    SRC = alt if alt.exists() else SRC
print("官方题库目录:", SRC)

cur = BASE / "题库_v7.json"
if not cur.exists():
    raise SystemExit("未找到题库_v7.json（先把旧题库复制进本目录）")
old = json.loads(cur.read_text(encoding="utf-8"))
self_made = [q for q in old["questions"] if q["group"] in ("G2","G3","G4","G5","G6")]
print("自拟 G2-G6:", len(self_made), "题")

g1 = []
cn_files = sorted((SRC/"中文版").glob("*.jsonl")) if (SRC/"中文版").exists() else []
if cn_files:
    for l in cn_files[0].read_text(encoding="utf-8").splitlines():
        if not l.strip(): continue
        j = json.loads(l)
        g1.append({"text": j["problem_cn"], "answer": j["answer_cn"]})
    lang = "中文（v2翻译：专有名词保留原文）"
else:
    for q in old["questions"]:
        if q["group"] == "G1":
            g1.append({"text": q["text"], "answer": q["answer"]})
    lang = "沿用旧题库G1（未重译——建议先跑 翻译工具.py）"
print("G1:", len(g1), "题｜语言:", lang)

questions = []
qid = 1
for it in g1:
    questions.append({"id": qid, "group": "G1", "reps": 1, "text": it["text"], "answer": it["answer"]})
    qid += 1
for q in self_made:
    nq = {"id": qid, "group": q["group"], "reps": q["reps"], "text": q["text"], "answer": q.get("answer", "")}
    if q.get("checks"):
        nq["checks"] = q["checks"]
    questions.append(nq)
    qid += 1

bank = dict(old)
bank["meta"] = dict(old["meta"])
bank["meta"]["version"] = 7
bank["meta"]["language"] = lang
bank["questions"] = questions
cur.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
print("题库_v7.json 已重新生成：共", len(questions), "题")
print("提醒：如已用旧题库跑过 ab_test，请删除 results 目录后重跑（题目文本已变）。")