# Schema Templates Reference

Complete JSON-LD templates for all GEO Schema types.

## Table of Contents
1. [Organization](#organization)
2. [FAQPage](#faqpage)
3. [TechArticle](#techarticle)
4. [Person (E-E-A-T)](#person)
5. [E-E-A-T @graph](#eeat-graph)
6. [Citation](#citation)
7. [BreadcrumbList](#breadcrumblist)
8. [BlogPosting](#blogposting)
9. [ImageObject (figure)](#imageobject)

---

## Organization {#organization}

Brand identity — inject into site `<head>` or via Google Tag Manager.

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{{品牌名}}",
  "description": "{{一句话描述}}",
  "url": "{{网站URL}}",
  "foundingDate": "{{成立年份}}",
  "areaServed": {
    "@type": "Country",
    "name": "{{目标市场}}"
  },
  "knowsAbout": ["{{领域1}}", "{{领域2}}", "{{领域3}}"],
  "offers": {
    "@type": "Offer",
    "description": "{{产品/服务描述}}"
  }
}
```

---

## FAQPage {#faqpage}

Highest ROI single action — 43% of AI citations come from FAQ Schema.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "{{自然口语问题}}",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "{{含具体数据的答案，80-200字}}"
      }
    }
  ]
}
```

Minimum 10 FAQ entries recommended.

---

## TechArticle {#techarticle}

Apply to every article page.

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "{{文章标题}}",
  "description": "{{文章摘要}}",
  "author": {
    "@type": "Person",
    "name": "{{作者名}}"
  },
  "datePublished": "{{YYYY-MM-DD}}",
  "dateModified": "{{YYYY-MM-DD}}",
  "image": "{{封面图URL}}",
  "publisher": {
    "@type": "Organization",
    "name": "{{品牌名}}",
    "logo": {
      "@type": "ImageObject",
      "url": "{{logo URL}}"
    }
  },
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "{{文章URL}}"
  }
}
```

---

## Person (E-E-A-T) {#person}

Author credibility signal — AI downgrades anonymous content.

```json
{
  "@type": "Person",
  "@id": "{{作者页面URL}}",
  "name": "{{作者名}}",
  "jobTitle": "{{职位/角色描述}}",
  "knowsAbout": ["{{领域1}}", "{{领域2}}"],
  "hasCredential": "{{资质/成果描述}}",
  "sameAs": [
    "{{社交链接1}}",
    "{{社交链接2}}"
  ]
}
```

---

## E-E-A-T @graph {#eeat-graph}

Combined Person + Article for maximum authority signal.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Person",
      "@id": "{{作者页面URL}}",
      "name": "{{作者名}}",
      "jobTitle": "{{角色}}",
      "knowsAbout": ["{{领域1}}", "{{领域2}}"],
      "hasCredential": "{{成果}}",
      "sameAs": ["{{链接}}"]
    },
    {
      "@type": "TechArticle",
      "headline": "{{文章标题}}",
      "author": { "@id": "{{作者页面URL}}" },
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": "{{文章URL}}"
      }
    }
  ]
}
```

---

## Citation {#citation}

Mark authoritative sources to boost AI trust.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{{文章标题}}",
  "citation": [
    {
      "@type": "ScholarlyArticle",
      "name": "{{来源标题}}",
      "url": "{{来源URL}}",
      "publisher": {
        "@type": "Organization",
        "name": "{{发布机构}}"
      }
    }
  ]
}
```

---

## BreadcrumbList {#breadcrumblist}

Navigation structure for AI crawlers.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "首页", "item": "{{base_url}}" },
    { "@type": "ListItem", "position": 2, "name": "{{分类名}}", "item": "{{category_url}}" },
    { "@type": "ListItem", "position": 3, "name": "{{文章名}}" }
  ]
}
```

---

## BlogPosting {#blogposting}

For blog articles specifically.

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "{{标题}}",
  "author": { "@type": "Person", "name": "{{作者}}" },
  "datePublished": "{{YYYY-MM-DD}}",
  "publisher": {
    "@type": "Organization",
    "name": "{{品牌}}",
    "logo": { "@type": "ImageObject", "url": "{{logo}}" }
  }
}
```

---

## ImageObject (figure) {#imageobject}

Structured image with full alt description.

```html
<figure itemscope itemtype="https://schema.org/ImageObject">
  <img src="{{image_url}}"
       alt="{{完整描述句: 告诉AI这张图表达什么}}"
       loading="lazy">
  <figcaption itemprop="caption">
    {{图片说明文字}}
  </figcaption>
  <meta itemprop="author" content="{{作者}}">
</figure>
```

Key: alt text should be a full descriptive sentence, not just keywords.
