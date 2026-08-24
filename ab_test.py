# -*- coding: utf-8 -*-
"""ODL A/B 测试脚本 v4（无第三方依赖）
读取 题库_v4.json 与当前版本手册（自动发现 发生发展逻辑模型_操作手册_*.md）。
混合采样：reps=1 组在 deepseek-chat 上用 temperature=0（reasoner 不支持该参数，省略）；reps=3 组用默认采样。
输出：results/ 原始输出 + ab_summary.csv。调用量 120 次。健壮性：单次失败重试3次退避；中途出错也写CSV。
"""
import json, os, sys, time, urllib.request, csv, pathlib
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not KEY:
    raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY")

BASE = pathlib.Path(__file__).parent
manuals = sorted(BASE.glob("发生发展逻辑模型_操作手册_*.md"))
if not manuals:
    raise SystemExit("未找到手册文件")
MANUAL = manuals[-1].read_text(encoding="utf-8")
print("手册版本文件:", manuals[-1].name)

TS = json.loads((BASE / "题库_v4.json").read_text(encoding="utf-8"))
QUESTIONS = TS["questions"]
MODELS = TS["meta"]["models"]

def chat(model, system, user, temp=None, tries=3):
    for attempt in range(1, tries + 1):
        try:
            payload = {"model": model, "messages": [], "stream": False}
            if temp is not None:
                payload["temperature"] = temp
            if system:
                if "reasoner" in model:
                    payload["messages"].append({"role": "user", "content": system + "\n\n---\n\n" + user})
                else:
                    payload["messages"] += [{"role": "system", "content": system}, {"role": "user", "content": user}]
            else:
                payload["messages"].append({"role": "user", "content": user})
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
            with urllib.request.urlopen(req, timeout=300) as r:
                j = json.loads(r.read().decode("utf-8"))
            msg = j["choices"][0]["message"]["content"]
            usage = j.get("usage", {})
            return msg, usage
        except Exception as e:
            if attempt == tries:
                return "[ERROR] " + str(e), {}
            time.sleep(5 * attempt)
    return "[ERROR] unreachable", {}

def main():
    outdir = BASE / "results"
    outdir.mkdir(exist_ok=True)
    rows = []
    try:
        for model in MODELS:
            for q in QUESTIONS:
                temp = None
                if model == "deepseek-chat":
                    temp = 0.0 if q["reps"] == 1 else 1.0
                for arm, sysmsg in (("A", None), ("B", MANUAL)):
                    for rep in range(1, q["reps"] + 1):
                        msg, usage = chat(model, sysmsg, q["text"], temp=temp)
                        (outdir / f"{arm}_{model}_q{q['id']}_r{rep}.md").write_text(msg, encoding="utf-8")
                        rows.append([q["id"], q["group"], model, arm, rep, len(msg), usage.get("prompt_tokens", ""), usage.get("completion_tokens", "")])
                        print(f"done {model} q{q['id']} {arm} r{rep}")
                        time.sleep(0.3)
    finally:
        with open(outdir / "ab_summary.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["题号", "组", "模型", "组别", "重复", "字符数", "prompt_tokens", "completion_tokens"])
            w.writerows(rows)
    print("完成：results/ + ab_summary.csv（" + str(len(rows)) + " 条）。下一步：python grade.py 出评分。")

if __name__ == "__main__":
    main()
