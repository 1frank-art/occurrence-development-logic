# -*- coding: utf-8 -*-
"""token统计.py：长度指标（字符＋官方 token 双口径，按档位分组）
输入1：本目录 results/ab_summary.csv（v2.5 新题 G7/G8，含官方 usage token）。
输入2（可选）：v7 历史 ab_summary.csv 路径（v7 题组 G1-G6，含官方 usage token），默认自动探测
    E:\\天津大学文献\\博士课题调研\\汇报汇总\\历史测试数据归档_前两轮\\v7_results\\ab_summary.csv
输出：token统计_v8.csv（臂×组：题目数、中位字符、中位token、均值token）＋控制台摘要。"""
import csv, os, sys, pathlib, statistics
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = pathlib.Path(__file__).parent
V7_DEFAULT = r"E:\天津大学文献\博士课题调研\汇报汇总\历史测试数据归档_前两轮\v7_results\ab_summary.csv"
V7 = sys.argv[1] if len(sys.argv) > 1 else V7_DEFAULT

# 档位归类：一档事实/问候情感 → 短场景；二三档多句/长文 → 长场景；G7 事实解释 → 二档；G8 任务 → 三档
TIER = {"G1": "一档(事实)", "G2": "一档(事实)", "G4": "一档(问候情感)", "G5": "二三档(多句)", "G6": "二三档(多句)",
        "G3": "三档(长文任务)", "G7": "二档(事实解释)", "G8": "三档(指令任务)"}

def load(path):
    if not os.path.exists(path):
        print("跳过（不存在）:", path)
        return []
    with open(path, encoding="utf-8-sig") as f:
        rd = list(csv.reader(f))
    hdr = rd[0]
    i_q, i_g, i_arm, i_ch, i_tk = hdr.index("题号"), hdr.index("组"), hdr.index("臂"), hdr.index("字符数"), hdr.index("completion_tokens")
    out = []
    for r in rd[1:]:
        try:
            tk = int(r[i_tk]) if r[i_tk] else None
        except ValueError:
            tk = None
        out.append((r[i_q], r[i_g], r[i_arm], int(r[i_ch]), tk))
    return out

rows = load(os.path.join(BASE, "results", "ab_summary.csv")) + load(V7)
if not rows:
    raise SystemExit("无数据：请先跑 ab_test.py，并确认 v7 历史 CSV 路径")

from collections import defaultdict
acc = defaultdict(lambda: defaultdict(list))
for qid, grp, arm, ch, tk in rows:
    key = TIER.get(grp, grp)
    acc[arm][key].append((ch, tk))

with open(BASE / "token统计_v8.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["臂", "档位组", "题目数", "中位字符", "中位token", "均值token"])
    for arm in ("A", "B", "C"):
        for key in sorted(acc[arm]):
            vs = acc[arm][key]
            chs = [v[0] for v in vs]
            tks = [v[1] for v in vs if v[1] is not None]
            med_ch = int(statistics.median(chs)) if chs else 0
            med_tk = int(statistics.median(tks)) if tks else ""
            avg_tk = round(statistics.mean(tks), 1) if tks else ""
            w.writerow([arm, key, len(vs), med_ch, med_tk, avg_tk])
print("token统计_v8.csv 已生成。")
print("说明：v7 题组(G1-G6)与 v2.5 新题(G7/G8)的 token 均为 API 官方 usage 字段口径；字符数为本地口径。")
print("档位分组：" + "；".join(f"{k}={v}" for k, v in TIER.items()))
