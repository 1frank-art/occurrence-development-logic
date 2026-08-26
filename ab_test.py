# -*- coding: utf-8 -*-
"""A/B/C 测试脚本 v5（对齐 运行时配置操作手册 v2.4）
三臂：A 裸调用 / B 加载手册 v2.4 / C 等长中性 placebo。模型含 deepseek-v4-pro（探测，仅单次组）。
断点续跑：跳过已生成文件、载入历史 CSV。每行记录响应 model 字段＋时间戳。"""
import json, os, sys, time, datetime, urllib.request, csv, pathlib
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not KEY:
    raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY")

BASE = pathlib.Path(__file__).parent
manuals = sorted(BASE.glob("发生发展逻辑模型_运行时配置操作手册_*.md"))
if not manuals:
    raise SystemExit("未找到手册 v2.4 文件")
MANUAL = manuals[-1].read_text(encoding="utf-8")
print("手册:", manuals[-1].name)

BANK = BASE / "题库_v7.json"
if not BANK.exists():
    BANK = BASE / "题库_v6.json"
TS = json.loads(BANK.read_text(encoding="utf-8"))
print("题库:", BANK.name)
QUESTIONS = TS["questions"]
UNIT = "这是一段与测试无关的中性说明文字，仅用于平衡上下文长度。"
PLACEBO = (UNIT * (len(MANUAL) // len(UNIT) + 1))[:len(MANUAL)]
print("placebo 长度(≈手册):", len(PLACEBO), "vs", len(MANUAL))

def chat(model, system, user, temp=None, tries=3):
    for attempt in range(1, tries + 1):
        try:
            payload = {"model": model, "messages": [], "stream": False}
            if temp is not None:
                payload["temperature"] = temp
            if system:
                if "reasoner" in model or "pro" in model:
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
            resp_model = j.get("model", model)
            return msg, usage, resp_model
        except Exception as e:
            if attempt == tries:
                return "[ERROR] " + str(e), {}, model
            time.sleep(5 * attempt)
    return "[ERROR] unreachable", {}, model

def probe(model):
    msg, _, _ = chat(model, None, "ping", temp=None, tries=1)
    ok = not msg.startswith("[ERROR]")
    print(f"探测 {model}: {'可用' if ok else '跳过'}")
    return ok

def main():
    outdir = BASE / "results"
    outdir.mkdir(exist_ok=True)
    models = [m for m in TS["meta"]["models"] if probe(m)]
    if not models:
        raise SystemExit("无可用模型")
    rows = []
    csv_path = outdir / "ab_summary.csv"
    if csv_path.exists():
        with open(csv_path, encoding="utf-8-sig") as f:
            rd = csv.reader(f)
            next(rd, None)
            rows = [r[:10] for r in rd]
        print("断点续跑：已载入", len(rows), "条历史记录")
    try:
        for model in models:
            for q in QUESTIONS:
                if model == "deepseek-v4-pro" and q["reps"] > 1:
                    print(f"skip {model} q{q['id']}（reps>1 慢组，仅测单次组）")
                    continue
                temp = None
                if model == "deepseek-chat":
                    temp = 0.0 if q["reps"] == 1 else 1.0
                for arm, sysmsg in (("A", None), ("B", MANUAL), ("C", PLACEBO)):
                    for rep in range(1, q["reps"] + 1):
                        out_file = outdir / f"{arm}_{model}_q{q['id']}_r{rep}.md"
                        if out_file.exists():
                            print(f"skip {model} q{q['id']} {arm} r{rep}（已有）")
                            continue
                        msg, usage, resp_model = chat(model, sysmsg, q["text"], temp=temp)
                        ts = datetime.datetime.now().isoformat(timespec="seconds")
                        out_file.write_text(msg, encoding="utf-8")
                        rows.append([q["id"], q["group"], model, resp_model, arm, rep, ts, len(msg), usage.get("prompt_tokens", ""), usage.get("completion_tokens", "")])
                        print(f"done {model} q{q['id']} {arm} r{rep}")
                        time.sleep(0.3)
    finally:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["题号", "组", "模型(请求)", "模型(响应)", "臂", "重复", "时间戳", "字符数", "prompt_tokens", "completion_tokens"])
            w.writerows(rows)
    print("完成：results/ + ab_summary.csv（" + str(len(rows)) + " 条）。下一步：python grade.py。")

if __name__ == "__main__":
    main()
