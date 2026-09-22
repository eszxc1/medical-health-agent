#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 自动化评估脚本
====================
逐条读取评估用例，调用现有 Agent（复用 ai.LoadAgent.load_agent，不重复实现 Agent 逻辑），
检查回答是否命中 expected_keywords，输出测试报告。

用法：
    cd rag_server
    python scripts/eval_agent.py                 # 表格报告
    python scripts/eval_agent.py --json          # JSON 报告（便于接入 CI）
    python scripts/eval_agent.py --cases path    # 自定义用例文件
    python scripts/eval_agent.py --email x@y.com # 指定注入的测试邮箱

依赖：
    - 复用 ai.LoadAgent.load_agent()
    - .env 中需配置 DASHSCOPE_API_KEY 等（与主服务一致）
"""
import argparse
import json
import os
import sys
import time

# 让 scripts/ 下直接运行能 import ai / common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import LoadAgent
from langchain_core.messages import AIMessage

DEFAULT_CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_cases.jsonl")


def load_cases(path):
    cases = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def extract_answer(response):
    """从 agent.invoke 返回结果中提取最终 AIMessage 文本"""
    for msg in reversed(response.get("messages", [])):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return ""


def run_case(agent, case, email):
    messages = []
    if email:
        messages.append({
            "role": "system",
            "content": (
                f"【系统指令】当前对话用户的邮箱是: {email}。"
                f"这是唯一合法的用户标识，执行需要邮箱的操作时直接使用 {email}，严禁询问邮箱。"
            )
        })
    messages.append({"role": "user", "content": case["question"]})
    response = agent.invoke({"messages": messages})
    return extract_answer(response)


def check_keywords(response, expected_keywords):
    found = [kw for kw in expected_keywords if kw in response]
    return len(found) > 0, found


def display_width(s):
    """计算显示宽度（中文等全角字符按 2 计）"""
    return sum(2 if ord(c) > 127 else 1 for c in str(s))


def pad(s, width):
    s = str(s)
    return s + " " * max(0, width - display_width(s))


def truncate(s, width):
    """按显示宽度截断字符串，超出补省略号"""
    s = str(s)
    if display_width(s) <= width:
        return s
    result = ""
    w = 0
    for c in s:
        cw = 2 if ord(c) > 127 else 1
        if w + cw > width - 1:
            result += "…"
            break
        result += c
        w += cw
    return result


def print_table(results):
    headers = ["case_id", "question", "category", "passed", "response", "actual_keywords_found"]
    widths = [8, 24, 17, 6, 42, 28]
    sep = " | "

    print(sep.join(pad(h, w) for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))

    for r in results:
        row = [
            r["case_id"],
            r["question"],
            r["category"],
            "PASS" if r["passed"] else "FAIL",
            truncate(r["response"], 42),
            ", ".join(r["actual_keywords_found"]),
        ]
        print(sep.join(pad(c, w) for c, w in zip(row, widths)))

    print()


def summarize(results):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    by_cat = {}
    for r in results:
        cat = r["category"]
        by_cat.setdefault(cat, {"total": 0, "passed": 0})
        by_cat[cat]["total"] += 1
        if r["passed"]:
            by_cat[cat]["passed"] += 1
    categories = {
        cat: {"passed": v["passed"], "total": v["total"],
              "rate": round(v["passed"] / v["total"] * 100, 1) if v["total"] else 0}
        for cat, v in by_cat.items()
    }
    return {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "by_category": categories,
    }


def main():
    parser = argparse.ArgumentParser(description="Agent 自动化评估")
    parser.add_argument("--cases", default=DEFAULT_CASES, help="评估用例 jsonl 文件路径")
    parser.add_argument("--email", default=os.getenv("EVAL_EMAIL", "test@example.com"),
                        help="注入的测试邮箱（默认读 EVAL_EMAIL，否则 test@example.com）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式报告")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if not cases:
        print(f"[ERROR] 未找到用例: {args.cases}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 加载 {len(cases)} 条用例，初始化 Agent ...")
    agent = LoadAgent.load_agent()
    print("[INFO] Agent 就绪，开始逐条评估\n")

    results = []
    for case in cases:
        t0 = time.time()
        try:
            answer = run_case(agent, case, args.email)
            passed, found = check_keywords(answer, case.get("expected_keywords", []))
            results.append({
                "case_id": case.get("case_id"),
                "question": case["question"],
                "category": case["category"],
                "passed": passed,
                "response": answer,
                "actual_keywords_found": found,
            })
        except Exception as e:
            results.append({
                "case_id": case.get("case_id"),
                "question": case["question"],
                "category": case["category"],
                "passed": False,
                "response": f"[ERROR] {e}",
                "actual_keywords_found": [],
            })
        elapsed = time.time() - t0
        status = "PASS" if results[-1]["passed"] else "FAIL"
        print(f"[{status}] case {case.get('case_id')} ({case['category']}) 耗时 {elapsed:.1f}s")

    print()
    summary = summarize(results)

    if args.json:
        payload = {
            "summary": summary,
            "cases": [
                {
                    "case_id": r["case_id"],
                    "question": r["question"],
                    "category": r["category"],
                    "passed": r["passed"],
                    "response_preview": truncate(r["response"], 100),
                    "actual_keywords_found": r["actual_keywords_found"],
                }
                for r in results
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_table(results)
        print("=" * 72)
        print(f"总通过率: {summary['passed']}/{summary['total']} = {summary['pass_rate']}%")
        print("各分类表现:")
        for cat, v in summary["by_category"].items():
            print(f"  {pad(cat, 20)} {v['passed']}/{v['total']} = {v['rate']}%")
        print("=" * 72)


if __name__ == "__main__":
    main()
