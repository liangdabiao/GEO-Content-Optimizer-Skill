#!/usr/bin/env python3
"""GEO Schema Generator - Generate JSON-LD structured data for AI search optimization."""

import argparse
import json
import sys
from datetime import datetime


def generate_organization(name, description, knows_about=None, offers=None,
                          area_served=None, founding_date=None, url=None):
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "description": description,
    }
    if founding_date:
        schema["foundingDate"] = founding_date
    if url:
        schema["url"] = url
    if area_served:
        schema["areaServed"] = {"@type": "Country", "name": area_served}
    if knows_about:
        schema["knowsAbout"] = knows_about
    if offers:
        schema["offers"] = {"@type": "Offer", "description": offers}
    return schema


def generate_faq(questions):
    entities = []
    for q in questions:
        entities.append({
            "@type": "Question",
            "name": q["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": q["answer"]
            }
        })
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }


def generate_article(headline, author_name, date_published, description=None,
                     url=None, image=None, publisher_name=None, publisher_logo=None,
                     article_type="TechArticle"):
    schema = {
        "@context": "https://schema.org",
        "@type": article_type,
        "headline": headline,
        "author": {
            "@type": "Person",
            "name": author_name,
        },
        "datePublished": date_published,
        "dateModified": date_published,
    }
    if description:
        schema["description"] = description
    if url:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}
    if image:
        schema["image"] = image
    if publisher_name:
        pub = {"@type": "Organization", "name": publisher_name}
        if publisher_logo:
            pub["logo"] = {"@type": "ImageObject", "url": publisher_logo}
        schema["publisher"] = pub
    return schema


def generate_person(name, job_title, knows_about=None, same_as=None,
                    has_credential=None, person_id=None):
    schema = {
        "@type": "Person",
        "name": name,
        "jobTitle": job_title,
    }
    if person_id:
        schema["@id"] = person_id
    if knows_about:
        schema["knowsAbout"] = knows_about
    if same_as:
        schema["sameAs"] = same_as
    if has_credential:
        schema["hasCredential"] = has_credential
    return schema


def generate_eeat_graph(author_info, article_info):
    person = generate_person(
        name=author_info["name"],
        job_title=author_info.get("job_title", ""),
        knows_about=author_info.get("knows_about"),
        same_as=author_info.get("same_as"),
        has_credential=author_info.get("has_credential"),
        person_id=author_info.get("person_id"),
    )
    article = generate_article(
        headline=article_info["headline"],
        author_name=author_info["name"],
        date_published=article_info.get("date_published", datetime.now().strftime("%Y-%m-%d")),
        description=article_info.get("description"),
        url=article_info.get("url"),
        article_type=article_info.get("article_type", "TechArticle"),
    )
    if author_info.get("person_id"):
        article["author"] = {"@id": author_info["person_id"]}
    return {
        "@context": "https://schema.org",
        "@graph": [person, article]
    }


def generate_citation(sources, headline=None, article_url=None):
    citations = []
    for s in sources:
        entry = {
            "@type": s.get("type", "ScholarlyArticle"),
            "name": s["name"],
        }
        if "url" in s:
            entry["url"] = s["url"]
        if "publisher" in s:
            entry["publisher"] = {"@type": "Organization", "name": s["publisher"]}
        if "date_published" in s:
            entry["datePublished"] = s["date_published"]
        citations.append(entry)
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "citation": citations,
    }
    if headline:
        schema["headline"] = headline
    if article_url:
        schema["mainEntityOfPage"] = {"@type": "WebPage", "@id": article_url}
    return schema


def generate_breadcrumb(items):
    elements = []
    for i, item in enumerate(items):
        elements.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": item["name"],
            **({"item": item["url"]} if "url" in item else {}),
        })
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }


def wrap_script_tag(schema):
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'


def main():
    parser = argparse.ArgumentParser(description="GEO Schema Generator")
    parser.add_argument("--type", required=True,
                        choices=["organization", "faq", "article", "person",
                                 "eeat", "citation", "breadcrumb"],
                        help="Schema type to generate")
    parser.add_argument("--input", help="Input JSON file")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--wrap", action="store_true",
                        help="Wrap in <script> HTML tag")

    # Organization args
    parser.add_argument("--name", help="Organization/Person name")
    parser.add_argument("--description", help="Description")
    parser.add_argument("--knows-about", nargs="+", help="Areas of expertise")
    parser.add_argument("--offers", help="Offer description")
    parser.add_argument("--area-served", help="Target market/country")
    parser.add_argument("--founding-date", help="Founding date")
    parser.add_argument("--url", help="Website URL")

    # Article args
    parser.add_argument("--headline", help="Article headline")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--date-published", help="Publication date")
    parser.add_argument("--publisher", help="Publisher name")
    parser.add_argument("--publisher-logo", help="Publisher logo URL")
    parser.add_argument("--image", help="Article image URL")
    parser.add_argument("--article-type", default="TechArticle",
                        help="Article type (default: TechArticle)")

    args = parser.parse_args()
    result = None

    if args.type == "organization":
        if not args.name or not args.description:
            # Try loading from input file
            if args.input:
                with open(args.input, encoding="utf-8") as f:
                    data = json.load(f)
                result = generate_organization(**data)
            else:
                parser.error("--name and --description required for organization")
        else:
            result = generate_organization(
                name=args.name, description=args.description,
                knows_about=args.knows_about, offers=args.offers,
                area_served=args.area_served, founding_date=args.founding_date,
                url=args.url,
            )

    elif args.type == "faq":
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
            result = generate_faq(data)
        else:
            parser.error("--input required for faq (JSON file with question/answer pairs)")

    elif args.type == "article":
        if not args.headline or not args.author:
            parser.error("--headline and --author required for article")
        result = generate_article(
            headline=args.headline, author_name=args.author,
            date_published=args.date_published or datetime.now().strftime("%Y-%m-%d"),
            description=args.description, url=args.url, image=args.image,
            publisher_name=args.publisher, publisher_logo=args.publisher_logo,
            article_type=args.article_type,
        )

    elif args.type == "person":
        if not args.name:
            parser.error("--name required for person")
        result = generate_person(
            name=args.name, job_title=args.description or "",
            knows_about=args.knows_about,
            same_as=[args.url] if args.url else None,
        )

    elif args.type == "eeat":
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
            result = generate_eeat_graph(data["author"], data["article"])
        else:
            parser.error("--input required for eeat (JSON with author and article info)")

    elif args.type == "citation":
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
            result = generate_citation(
                data.get("sources", data if isinstance(data, list) else []),
                headline=data.get("headline") if isinstance(data, dict) else None,
                article_url=data.get("url") if isinstance(data, dict) else None,
            )
        else:
            parser.error("--input required for citation")

    elif args.type == "breadcrumb":
        if args.input:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
            result = generate_breadcrumb(data)
        else:
            parser.error("--input required for breadcrumb")

    output_text = wrap_script_tag(result) if args.wrap else json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Schema written to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
