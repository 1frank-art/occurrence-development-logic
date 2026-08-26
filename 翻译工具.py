# -*- coding: utf-8 -*-
"""翻译工具 v2：官方英文抽样题→中文。要求：人名/地名/机构名/产品名等专有名词保留英文原文；数字/单位/代码保留原文。"""
import json, os, sys, time, urllib.request, pathlib
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not KEY:
    raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY")
BASE = pathlib.Path(__file__).parent
SRC = BASE / "官方题库抽样"
if not SRC.exists():
    alt = BASE.parent / "执行版SystemPrompt包" / "官方题库抽样"
    SRC = alt if alt.exists() else SRC
print("翻译源目录:", SRC)
OUT = SRC / "中文版"
OUT.mkdir(exist_ok=True, parents=True)

def chat(user, tries=3):
    for attempt in range(1, tries + 1):
        try:
            payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": user}], "stream": False, "temperature": 0}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
            with urllib.request.urlopen(req, timeout=300) as r:
                j = json.loads(r.read().decode("utf-8"))
            return j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == tries:
                return "[翻译失败] " + str(e)
            time.sleep(5 * attempt)
    return "[翻译失败]"

PROMPT = "把下面的英文翻译成中文，只输出译文，不加任何解释。翻译规则：人名、地名、机构名、产品名、作品名等专有名词保留英文原文；数字、单位、代码、文件名保留原文。\n"

total = 0
files = sorted(SRC.glob("*.jsonl"))
if not files:
    raise SystemExit("官方题库抽样 目录为空：先下载官方题库并运行 题库工具.py")
for f in files:
    items = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    out_rows = []
    for it in items:
        p_cn = chat(PROMPT + it.get("problem", ""))
        a_cn = chat(PROMPT + it.get("answer", "")) if it.get("answer") else ""
        out_rows.append({"source": it.get("source", ""), "problem_cn": p_cn, "answer_cn": a_cn, "problem_en": it.get("problem", ""), "answer_en": it.get("answer", "")})
        print(f"{f.name}: {p_cn[:50]}")
        time.sleep(0.3)
    out = OUT / (f.stem + "_中文.jsonl")
    with open(out, "w", encoding="utf-8") as g:
        for r in out_rows:
            g.write(json.dumps(r, ensure_ascii=False) + "\n")
    total += len(items)
    print("写出:", out.name)
print("完成，共", total, "题")
