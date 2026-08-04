# GEO Best Practices

## Industry Data

- BrightEdge analyzed 1M AI responses: **68% of AI citations** come from high-authority sites, **43%** from correctly Schema-marked FAQ content.
- McKinsey predicts **40% of searches** will be AI-driven by 2026.
- Not doing GEO in 2025 = not doing SEO in 2015.

## Deployment Priority

| Priority | Action | Impact | Time |
|----------|--------|--------|------|
| P0 | FAQ Schema (10+ entries) | Highest — 43% citation source | 10 min |
| P0 | Organization Schema | Foundation — tells AI who you are | 5 min |
| P1 | Article Schema on all pages | Required for every article | 10 min |
| P1 | Author Person Schema | E-E-A-T signal — no anonymous content | 5 min |
| P2 | BreadcrumbList | Navigation structure for crawlers | 5 min |
| P2 | Citation markup | Boosts authority of referenced sources | 5 min |
| P3 | Pillar Page cluster | Content architecture optimization | 30 min |
| P3 | Multi-format embedding | Multi-modal AI coverage | On demand |

## Common Mistakes

1. **Marketing speak** — AI engines penalize buzzword-heavy content. Use `readability_checker.py` before publishing.
2. **Anonymous authorship** — "佚名"/"本站编辑" triggers AI downweight. Always use real author + bio.
3. **Keyword-stuffed alt text** — Image alt should be a descriptive sentence, not keyword lists.
4. **Videos without subtitles** — AI cannot understand video without VTT caption files.
5. **FAQ too short** — Minimum 10 FAQ entries. Answers should contain specific data.
6. **Missing Schema validation** — Always validate at [Schema.org Validator](https://validator.schema.org/) before deploying.
7. **Ignoring AI Overview** — Use `/geo-content-optimizer <url>` to compare your content against Google AI Overview.

## AI Engine Preferences

| Engine | Strength | Content Preference |
|--------|----------|-------------------|
| ChatGPT | General knowledge | Well-structured, factual content with data |
| Perplexity | Real-time search | FAQ-style content, authoritative citations |
| Gemini | Multimodal | Image-rich content with proper alt text |
| Google AI Overview | Search integration | High-authority sites with complete Schema |

## Monthly GEO Checklist

1. Run `readability_checker.py` on new content
2. Run `visibility_tester.py` for brand monitoring (requires Perplexity API key)
3. Update FAQ with new customer questions
4. Add new case study data to articles
5. Verify all new pages have correct Schema

## Quarterly GEO Review

1. Run `geo_report_generator.py` for trend analysis
2. Compare citation rate vs. previous quarter
3. Identify underperforming keywords
4. Plan next quarter's content cluster expansion
5. Refresh Schema types (add BreadcrumbList, etc.)
