from __future__ import annotations

from datetime import datetime
import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    rows = []
    run_dt_date = run_date.date() if isinstance(run_date, datetime) else run_date

    for rec in records:
        paper_id = rec.paper_id.strip()
        title = normalize_whitespace(rec.title)
        summary = normalize_whitespace(rec.summary)
        
        authors = [normalize_whitespace(a) for a in rec.authors if a]
        authors_joined = compact_join(authors)
        
        categories = [normalize_whitespace(c) for c in rec.categories if c]
        categories_joined = compact_join(categories)
        primary_category = rec.primary_category or (categories[0] if categories else "General")

        if rec.published:
            try:
                pub_dt = datetime.strptime(rec.published, "%Y-%m-%d").date()
                age_days = (run_dt_date - pub_dt).days
            except (ValueError, TypeError):
                age_days = 9999
        else:
            age_days = 9999

        text_for_embedding = (
            f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"
        ).strip()

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "authors_joined": authors_joined,
                "categories": categories,
                "categories_joined": categories_joined,
                "primary_category": primary_category,
                "published": rec.published,
                "updated": rec.updated,
                "age_days": age_days,
                "abs_url": rec.abs_url,
                "pdf_url": rec.pdf_url,
                "comment": rec.comment,
                "summary_chars": len(summary),
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.dropna(subset=["paper_id", "title"])
    df = df[(df["paper_id"].str.strip() != "") & (df["title"].str.strip() != "")]
    df = df[df["summary_chars"] >= 100]
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)

    return df