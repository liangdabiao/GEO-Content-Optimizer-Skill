#!/usr/bin/env python3
"""GEO Report Generator - Generate quarterly GEO comparison reports."""

import argparse
import json
import sys
from datetime import datetime


def generate_report(vault):
    if not vault:
        return {"error": "No history data provided"}

    valid = [r for r in vault if "error" not in r]
    if not valid:
        return {"error": "No valid entries in history data"}

    engines = sorted(set(r.get("engine", "Unknown") for r in valid))
    brands = sorted(set(r.get("brand", "Unknown") for r in valid))

    # Split into two halves for trend comparison
    mid = len(valid) // 2
    first_half = valid[:mid] if mid > 0 else valid
    second_half = valid[mid:] if mid > 0 else valid

    first_cited = sum(1 for r in first_half if r.get("cited"))
    second_cited = sum(1 for r in second_half if r.get("cited"))
    first_rate = (first_cited / len(first_half) * 100) if first_half else 0
    second_rate = (second_cited / len(second_half) * 100) if second_half else 0

    if second_rate > first_rate:
        trend = "上升"
        trend_icon = "+"
    elif second_rate < first_rate:
        trend = "下降"
        trend_icon = "-"
    else:
        trend = "持平"
        trend_icon = "="

    # Per-keyword breakdown
    keyword_stats = {}
    for r in valid:
        kw = r.get("keyword", "unknown")
        if kw not in keyword_stats:
            keyword_stats[kw] = {"total": 0, "cited": 0}
        keyword_stats[kw]["total"] += 1
        if r.get("cited"):
            keyword_stats[kw]["cited"] += 1

    # Generate action items
    actions = []
    if second_rate < first_rate:
        actions.extend([
            "更新 FAQ 内容 (加入最近客户问的新问题)",
            "补充新案例数据到文章中",
            "重写未被引用文章的导语段",
            "扩展 Pillar Page 的子主题覆盖",
            "新增 1-2 个 Schema 类型 (如 BreadcrumbList)",
        ])
    elif second_rate >= 80:
        actions.extend([
            "继续当前策略",
            "扩展引擎覆盖范围 (加入 Gemini/Copilot 测试)",
            "创建新的内容集群扩大覆盖面",
        ])
    else:
        actions.extend([
            "继续优化当前内容",
            "增加 FAQ 数量到 15+ 个",
            "加强 E-E-A-T 信号建设",
            "增加引用权威来源的数量",
        ])

    return {
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "total_tests": len(valid),
        "engines_covered": engines,
        "brands": brands,
        "period_first_half": {
            "tests": len(first_half),
            "cited": first_cited,
            "rate": f"{first_rate:.0f}%",
        },
        "period_second_half": {
            "tests": len(second_half),
            "cited": second_cited,
            "rate": f"{second_rate:.0f}%",
        },
        "trend": trend,
        "trend_icon": trend_icon,
        "keyword_breakdown": {
            kw: f"{stats['cited']}/{stats['total']}"
            for kw, stats in keyword_stats.items()
        },
        "actions": actions,
    }


def format_report_md(report):
    if "error" in report:
        return f"# Error\n\n{report['error']}"

    lines = [
        "# GEO 季度效果报告",
        "",
        f"**报告日期**: {report['report_date']}",
        f"**总测试次数**: {report['total_tests']}",
        f"**覆盖引擎**: {', '.join(report['engines_covered'])}",
        f"**品牌**: {', '.join(report['brands'])}",
        "",
        "## 引用率趋势",
        "",
        "| 时段 | 测试数 | 被引用 | 引用率 |",
        "|------|--------|--------|--------|",
        f"| 前半期 | {report['period_first_half']['tests']} | {report['period_first_half']['cited']} | {report['period_first_half']['rate']} |",
        f"| 后半期 | {report['period_second_half']['tests']} | {report['period_second_half']['cited']} | {report['period_second_half']['rate']} |",
        "",
        f"**趋势**: {report['trend']} {report['trend_icon']}",
        "",
        "## 关键词明细",
        "",
        "| 关键词 | 被引用/总测试 |",
        "|--------|--------------|",
    ]
    for kw, stat in report["keyword_breakdown"].items():
        lines.append(f"| {kw} | {stat} |")

    lines.extend([
        "",
        "## 行动建议",
        "",
    ])
    for i, action in enumerate(report["actions"], 1):
        lines.append(f"{i}. {action}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GEO Report Generator")
    parser.add_argument("--history", required=True, help="History JSON file")
    parser.add_argument("--output", help="Output markdown file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    with open(args.history, encoding="utf-8") as f:
        vault = json.load(f)

    report = generate_report(vault)

    if "error" in report:
        print(f"Error: {report['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        md = format_report_md(report)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"Report written to {args.output}")
        else:
            print(md)


if __name__ == "__main__":
    main()
