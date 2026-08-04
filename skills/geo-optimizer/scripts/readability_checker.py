#!/usr/bin/env python3
"""GEO Readability Checker - Analyze text for AI search engine friendliness."""

import argparse
import re
import sys


BUZZWORDS = [
    '创新', '领先', '卓越', '全方位', '一站式', '极致',
    '颠覆', '最佳', '最优质', '革命性', '顶级', '独一无二',
    '首屈一指', '无与伦比', '领跑', '标杆', '龙头',
]

IDEAL_MIN_SENTENCE = 15
IDEAL_MAX_SENTENCE = 25


def split_sentences(text):
    parts = re.split(r'[。！？\n]', text)
    return [s.strip() for s in parts if len(s.strip()) > 5]


def check_buzzwords(text):
    return [w for w in BUZZWORDS if w in text]


def avg_sentence_length(sentences):
    if not sentences:
        return 0
    return sum(len(s) for s in sentences) / len(sentences)


def has_questions(text):
    return bool(re.search(r'[？?]', text))


def count_numbers(text):
    return len(re.findall(r'\d+', text))


def check_readability(text):
    sentences = split_sentences(text)
    if not sentences:
        return {"error": "No valid sentences found in input text"}

    avg_len = avg_sentence_length(sentences)
    buzz_hits = check_buzzwords(text)
    has_q = has_questions(text)
    num_count = count_numbers(text)

    # Score calculation
    score = 0
    if IDEAL_MIN_SENTENCE <= avg_len <= IDEAL_MAX_SENTENCE:
        score += 2
    elif avg_len <= 35:
        score += 1

    if has_q:
        score += 1
    if num_count >= 3:
        score += 2
    elif num_count >= 1:
        score += 1
    if len(buzz_hits) == 0:
        score += 2
    elif len(buzz_hits) <= 2:
        score += 1

    if score >= 6:
        rating = "高"
    elif score >= 4:
        rating = "中"
    else:
        rating = "低"

    suggestions = []
    if buzz_hits:
        suggestions.append(f"替换营销词为具体事实: {', '.join(buzz_hits)}")
    if avg_len > IDEAL_MAX_SENTENCE:
        suggestions.append(f"拆分长句 (当前均长{avg_len:.0f}字, 建议{IDEAL_MIN_SENTENCE}-{IDEAL_MAX_SENTENCE}字)")
    elif avg_len < IDEAL_MIN_SENTENCE:
        suggestions.append(f"句子偏短 (当前均长{avg_len:.0f}字, 建议{IDEAL_MIN_SENTENCE}-{IDEAL_MAX_SENTENCE}字)")
    if not has_q:
        suggestions.append("加入 1-2 个直接问句 (如: '如何...？''...有什么区别？')")
    if num_count == 0:
        suggestions.append("加入具体数据 (百分比、金额、案例数量等)")

    return {
        "total_sentences": len(sentences),
        "avg_length": round(avg_len, 1),
        "length_status": "ok" if IDEAL_MIN_SENTENCE <= avg_len <= IDEAL_MAX_SENTENCE else "warn",
        "buzzwords": buzz_hits,
        "has_questions": has_q,
        "number_count": num_count,
        "score": score,
        "rating": rating,
        "suggestions": suggestions,
    }


def format_report(result):
    lines = ["=== AI 可读性检查报告 ==="]
    lines.append(f"总段落数: {result['total_sentences']}")

    len_status = "OK" if result["length_status"] == "ok" else f"Warn (理想: {IDEAL_MIN_SENTENCE}-{IDEAL_MAX_SENTENCE}字)"
    lines.append(f"平均句长: {result['avg_length']}字 [{len_status}]")

    bw = ", ".join(result["buzzwords"]) if result["buzzwords"] else "None OK"
    lines.append(f"营销词命中: {bw}")

    q_status = "OK" if result["has_questions"] else "X (建议加入直接问句)"
    lines.append(f"包含问句: [{q_status}]")

    n_status = "OK" if result["number_count"] > 0 else "X (建议加入具体数据)"
    lines.append(f"数据引用: {result['number_count']}个数字 [{n_status}]")

    lines.append(f"综合评分: {result['rating']} ({result['score']}/7)")

    if result["suggestions"]:
        lines.append("")
        lines.append("优化建议:")
        for i, s in enumerate(result["suggestions"], 1):
            lines.append(f"  {i}. {s}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GEO Readability Checker")
    parser.add_argument("--text", help="Text to analyze")
    parser.add_argument("--file", help="File to analyze")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    text = ""
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        parser.error("Provide --text or --file")

    result = check_readability(text)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_report(result))


if __name__ == "__main__":
    main()
