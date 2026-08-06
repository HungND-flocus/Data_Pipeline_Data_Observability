# 📚 Giáo Trình Lý Thuyết & Cú Pháp Thực Hành: Data Pipeline & Observability Cho RAG

Tài liệu này được thiết kế theo phương pháp **Vừa Học Lý Thuyết - Vừa Học Cú Pháp - Vừa Thực Hành**. Dưới đây là toàn bộ nền tảng lý thuyết chuyên sâu kết hợp cú pháp Python (Syntax) chi tiết từng dòng code cho dự án Day 10 tại `DAY10_2A202601936_NguyenDucHung`.

---

## 🎯 PHẦN 1: KIẾN THỨC NỀN TẢNG & TỔNG QUAN LÝ THUYẾT (THEORY & CONCEPTS)

### 1. Tại sao Data Pipeline & Data Observability lại quan trọng đối với RAG?
- **Garbage In, Garbage Out**: Trong RAG (Retrieval-Augmented Generation), nếu dữ liệu nguồn bị lỗi (rỗng, rác text, thông tin cũ/mốc, trùng lặp), mô hình Vector Index sẽ tìm ra tài liệu sai $\rightarrow$ LLM trả lời sai (Hallucination).
- **Data Observability (Khả năng giám sát dữ liệu)**: Giúp kỹ sư kiểm soát 5 trụ cột dữ liệu chuẩn Production:
  1. **Freshness (Độ tươi)**: Dữ liệu có mới không? Có bị mốc/stale không?
  2. **Quality (Chất lượng)**: Dữ liệu có bị rỗng, thiếu trường, hoặc trùng lặp không?
  3. **Volume (Thể tích)**: Số lượng bản ghi có bị rớt đột ngột không?
  4. **Schema (Cấu trúc)**: Các trường dữ liệu có đúng kiểu dữ liệu mong đợi không?
  5. **Lineage (Nguồn gốc)**: Dữ liệu sinh ra từ raw payload nào để có thể truy vết và sửa chữa (Repair)?

---

### 2. Chi tiết các khái niệm trong dự án

#### A. Raw Data Artifacts (Dữ liệu thô gốc)
- Khi gọi API bên ngoài (như Crossref REST API), bạn **luôn luôn phải lưu lại Raw JSON Payload gốc** vào đĩa (`data/raw/`).
- **Lý do**: Khi pipeline bị lỗi ở bước Clean hay Vector Index, bạn có thể tái tạo (re-run) hoặc sửa lỗi (repair) từ dữ liệu gốc mà không cần phải spam/gọi lại API bên ngoài.

#### B. Crossref API & Data Cleaning
- **Crossref REST API**: Cung cấp metadata của các bài báo học thuật có mã DOI.
- **XML Tag Stripping**: Nội dung `abstract` từ Crossref thường chứa thẻ XML như `<jats:p>`, `<jats:sec>`. Cần dùng Regular Expression `re.sub(r"<[^>]+>", " ", text)` để làm sạch trước khi đưa vào embedding.
- **`text_for_embedding`**: Kết hợp Tiêu đề (Title), Tác giả (Authors), Chủ đề (Categories) và Tóm tắt (Summary) thành một đoạn văn duy nhất để mô hình Vector hóa captures đầy đủ ngữ cảnh.

#### C. MiniLM Embeddings & ChromaDB Vector Store
- **Embedding Model (`all-MiniLM-L6-v2`)**: Nén câu văn thành vector 384 chiều. Sử dụng cosine similarity để tính độ tương đồng giữa câu hỏi của user và tài liệu.
- **ChromaDB Indexing**: Cơ sở dữ liệu Vector lưu trữ vector embeddings và metadata bài báo, cho phép truy vấn top-k ngữ cảnh liên quan nhất chỉ trong vài milisecond.

#### D. RAG Evaluation Metrics (Chỉ số đánh giá RAG)
Để chứng minh chất lượng dữ liệu ảnh hưởng thế nào đến Agent, ta đo 4 chỉ số:
1. **Retrieval Hit Rate**: Tỷ lệ câu hỏi mà hệ thống tìm đúng tài liệu chứa câu trả lời (`ground_truth_doc_ids`).
2. **Mean Token F1**: Độ khớp từ vựng giữa câu trả lời của Agent và đáp án chuẩn (`ground_truth`).
3. **LLM-as-a-Judge Accuracy**: Dùng LLM đánh giá câu trả lời của Agent đúng hay sai dựa trên thang điểm 1-5.
4. **Ragas Score** *(tùy chọn)*: Bộ chỉ số tiêu chuẩn RAG (Faithfulness, Answer Relevancy, Context Precision/Recall).

#### E. Data Corruption & Data Repair Flow
- **Data Corruption (Giả lập dữ liệu lỗi)**: Cố tình làm hỏng dữ liệu sạch (xóa tóm tắt, cắt tiêu đề, chèn từ nhiễu, làm cũ ngày...) để đo xem điểm số của Agent bị giảm bao nhiêu phần trăm.
- **Data Repair (Phục hồi dữ liệu)**: Dùng Data Observability phát hiện lỗi $\rightarrow$ kích hoạt luồng khôi phục lại dữ liệu sạch từ Raw Artifacts $\rightarrow$ Re-index $\rightarrow$ Điểm số của Agent phục hồi trở lại.

---

## 🛠️ PHẦN 2: TỔNG HỢP CÚ PHÁP PYTHON QUAN TRỌNG (SYNTAX CHEAT SHEET)

1. **Regex xóa thẻ HTML/XML**:
   ```python
   import re
   clean_text = re.sub(r"<[^>]+>", " ", raw_text) # Thay thế mọi thẻ <...> bằng khoảng trắng
   ```
2. **Ép kiểu & bóc tách dictionary an toàn**:
   ```python
   value = payload.get("key", {}).get("sub_key", []) # Tránh lỗi KeyError khi key không tồn tại
   ```
3. **List Comprehension trong Python**:
   ```python
   authors = [a.get("family", "") for a in item.get("author", []) if a.get("family")]
   ```
4. **Tạo dataclass từ dict**:
   ```python
   from dataclasses import asdict
   dict_data = asdict(paper_record_instance) # Chuyển Dataclass sang Dict để lưu JSON
   ```
5. **Thao tác Pandas DataFrame**:
   ```python
   df = df.drop_duplicates(subset=["paper_id"], keep="first") # Xóa dòng trùng id
   df = df.sort_values(by="published", ascending=False)       # Sắp xếp ngày giảm dần
   ```

---

## 🚀 PHẦN 3: HƯỚNG DẪN CÚ PHÁP CHI TIẾT TỪNG CHẶNG

---

### 🟢 CHẶNG 1: Data Ingestion (`src/ingestion/crossref.py`)

File: [src/ingestion/crossref.py](file:///d:/VinAI%20in%20Action/VinAI%20Lab/DAY10_2A202601936_NguyenDucHung/src/ingestion/crossref.py)

#### 💡 Lý thuyết chặng 1:
- Gọi API bằng thư viện `requests` có cấu hình `User-Agent` (Crossref polite pool) để tránh bị chặn IP.
- Thêm vòng lặp `try...except` với cơ chế retry exponential backoff (`time.sleep(backoff)`) để xử lý lỗi `429 Too Many Requests` hoặc `503 Service Unavailable`.
- Dùng `write_json()` lưu cả response thô (`crossref_response.json`) và records thô (`crossref_records.json`).

#### 📝 Cú pháp code chi tiết:

```python
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_xml_tags(text: str) -> str:
    """Xóa các thẻ XML/HTML như <jats:p> và chuẩn hóa khoảng trắng."""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(cleaned)


def _extract_date(date_struct: dict[str, Any] | None) -> str:
    """Trích xuất chuỗi ngày dạng YYYY-MM-DD từ dict date-parts của Crossref."""
    if not date_struct or "date-parts" not in date_struct:
        return datetime.now().strftime("%Y-%m-%d")
    date_parts = date_struct.get("date-parts", [[]])[0]
    if not date_parts:
        return datetime.now().strftime("%Y-%m-%d")
    year = date_parts[0] if len(date_parts) > 0 else 2026
    month = date_parts[1] if len(date_parts) > 1 else 1
    day = date_parts[2] if len(date_parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    # Lấy danh sách bài báo từ payload JSON
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        # Lấy DOI (mã bài báo) và Tiêu đề
        doi = str(item.get("DOI", "")).strip()
        title_raw = item.get("title", [])
        if isinstance(title_raw, list) and title_raw:
            title = _clean_xml_tags(str(title_raw[0]))
        else:
            title = _clean_xml_tags(str(title_raw or ""))

        # Bỏ qua bản ghi nếu thiếu DOI hoặc tiêu đề
        if not doi or not title:
            continue

        # Trích xuất Summary (Tóm tắt)
        summary = _clean_xml_tags(str(item.get("abstract", "")))

        # Trích xuất Tác giả
        author_list = item.get("author", [])
        authors: list[str] = []
        for author in author_list:
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            name = f"{given} {family}".strip() if given and family else (family or given)
            if name:
                authors.append(name)
        if not authors:
            authors = ["Anonymous"]

        # Trích xuất Danh mục/Chủ đề
        subjects = item.get("subject", [])
        categories = [normalize_whitespace(str(s)) for s in subjects if s]
        if not categories:
            categories = ["General"]
        primary_category = categories[0]

        # Trích xuất Ngày đăng
        pub_struct = item.get("published-online") or item.get("published-print") or item.get("issued")
        published = _extract_date(pub_struct)
        dep_struct = item.get("deposited") or item.get("indexed") or pub_struct
        updated = _extract_date(dep_struct)

        # URL bài báo & PDF
        abs_url = str(item.get("URL", f"https://doi.org/{doi}"))
        pdf_url = ""
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = str(link.get("URL", ""))
                break

        container_title = item.get("container-title", [])
        comment = container_title[0] if isinstance(container_title, list) and container_title else str(container_title or "")

        # Đóng gói đối tượng PaperRecord
        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "Day10DataObservabilityLab/1.0 (mailto:student@example.com)",
    }

    max_retries = 4
    backoff = 1.0
    payload: dict[str, Any] = {}

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code in {429, 503, 502, 504}:
                time.sleep(backoff)
                backoff *= 2
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as exc:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to fetch Crossref records: {exc}") from exc
            time.sleep(backoff)
            backoff *= 2

    # Lưu Raw API Response JSON
    write_json(settings.paths.raw_api_response, payload)

    # Parse sang danh sách PaperRecord
    records = parse_crossref_payload(payload)

    # Lưu Raw Records JSON
    raw_records_data = [asdict(record) for record in records]
    write_json(settings.paths.raw_records_json, raw_records_data)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    raw_data = read_json(path)
    records: list[PaperRecord] = []
    for item in raw_data:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item.get("authors", []),
                categories=item.get("categories", []),
                primary_category=item.get("primary_category", "General"),
                published=item.get("published", ""),
                updated=item.get("updated", ""),
                abs_url=item.get("abs_url", ""),
                pdf_url=item.get("pdf_url", ""),
                comment=item.get("comment", ""),
            )
        )
    return records
```

---

### 🟡 CHẶNG 2: Data Cleaning (`src/ingestion/cleaning.py`)

File: [src/ingestion/cleaning.py](file:///d:/VinAI%20in%20Action/VinAI%20Lab/DAY10_2A202601936_NguyenDucHung/src/ingestion/cleaning.py)

#### 💡 Lý thuyết chặng 2:
- Chuẩn hóa text loại bỏ các ký tự xuống dòng thừa bằng `normalize_whitespace()`.
- Ghép `Title`, `Authors`, `Categories`, `Summary` thành `text_for_embedding` với định dạng `Title: [title] | Authors: [authors] | Summary: [summary]`.
- Lọc rác: Loại bỏ tiêu đề rỗng hoặc phần tóm tắt quá ngắn (dưới 100 ký tự `len(summary) < 100`).
- Tính `age_days` phục vụ việc kiểm tra độ tươi (Freshness).
- Lưu kết quả vào `data/clean/papers_clean.csv` và `data/clean/papers_clean.json`.

#### 📝 Cú pháp code chi tiết:

```python
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

        try:
            pub_dt = datetime.strptime(rec.published, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pub_dt = run_dt_date

        age_days = (run_dt_date - pub_dt).days

        # Ghép văn bản tổng hợp cho Vector Embedding theo chuẩn đề bài
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

    # 1. Lọc bỏ dòng không có tiêu đề hoặc summary quá ngắn (< 100 ký tự)
    df = df.dropna(subset=["paper_id", "title"])
    df = df[(df["paper_id"].str.strip() != "") & (df["title"].str.strip() != "")]
    df = df[df["summary_chars"] >= 100]

    # 2. Xóa trùng lặp paper_id
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    return df
```

---

### 🟠 CHẶNG 3: Benchmark Test Set (`src/evaluation/testset.py`)

File: [src/evaluation/testset.py](file:///d:/VinAI%20in%20Action/VinAI%20Lab/DAY10_2A202601936_NguyenDucHung/src/evaluation/testset.py)

#### 💡 Lý thuyết chặng 3:
- Muốn đo hiệu năng của RAG Agent, ta cần có **bộ câu hỏi chuẩn (Ground Truth)**.
- Mỗi câu hỏi cần ghi lại `ground_truth_doc_ids` chứa mã DOI bài báo để chấm điểm **Retrieval Hit Rate** (xem vector search có tìm ra đúng bài báo chứa đáp án không).

#### 📝 Cú pháp code chi tiết:

```python
from typing import Any
import pandas as pd
from core.utils import write_json

def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    records = df.to_dict(orient="records")
    test_set: list[dict[str, Any]] = []

    for index, row in enumerate(records[:10]):  # Lấy 10 bài làm câu hỏi mẫu
        paper_id = row["paper_id"]
        title = row["title"]

        # 1. Dạng câu hỏi Summary
        test_set.append({
            "id": f"eval_{index}_summary",
            "question_type": "summary",
            "question": f"What is the main summary of the paper titled '{title}'?",
            "ground_truth": row["summary"],
            "ground_truth_doc_ids": [paper_id],
        })

        # 2. Dạng câu hỏi Authors
        test_set.append({
            "id": f"eval_{index}_authors",
            "question_type": "authors",
            "question": f"Who are the authors of the paper titled '{title}'?",
            "ground_truth": row["authors_joined"],
            "ground_truth_doc_ids": [paper_id],
        })

    write_json(output_path, test_set)
    return test_set
```

---

### 🔵 CHẶNG 4: Observability (`src/observability/quality.py`)

File: [src/observability/quality.py](file:///d:/VinAI%20in%20Action/VinAI%20Lab/DAY10_2A202601936_NguyenDucHung/src/observability/quality.py)

#### 💡 Lý thuyết chặng 4:
- Thực hiện kiểm tra tự động xem dữ liệu có vi phạm các ràng buộc:
  - Có bị rỗng/thiếu tóm tắt không?
  - Có trùng lặp ID bài báo không?
  - Dữ liệu có bị mốc (quá 180 ngày) không?

#### 📝 Cú pháp code chi tiết:

```python
from typing import Any
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    total_rows = len(df)
    unique_ids = df["paper_id"].nunique() if not df.empty else 0
    missing_summary = int((df["summary"].str.strip() == "").sum()) if not df.empty else 0
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if not df.empty else 0

    results = {
        "report_name": report_name,
        "total_rows": total_rows,
        "unique_ids": unique_ids,
        "is_unique": unique_ids == total_rows,
        "missing_summary_rows": missing_summary,
        "stale_rows": stale_rows,
        "passed": (unique_ids == total_rows) and (missing_summary == 0),
    }

    output_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(output_path, results)
    return results


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    latest = df["published"].max() if not df.empty else ""
    oldest = df["published"].min() if not df.empty else ""
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if not df.empty else 0

    report = {
        "latest_published": latest,
        "oldest_published": oldest,
        "stale_rows": stale_rows,
        "total_rows": len(df),
        "is_fresh": stale_rows == 0,
    }
    write_json(report_path, report)
    return report
```

---

### 🟣 CHẶNG 5: Data Corruption (`src/ingestion/corruption.py`)

File: [src/ingestion/corruption.py](file:///d:/VinAI%20in%20Action/VinAI%20Lab/DAY10_2A202601936_NguyenDucHung/src/ingestion/corruption.py)

#### 💡 Lý thuyết chặng 5:
- Để chứng minh giá trị của Data Observability, ta cố tình tiêm (inject) lỗi vào DataFrame sạch để đo xem RAG Agent bị suy giảm hiệu năng bao nhiêu phần trăm.

#### 📝 Cú pháp code chi tiết:

```python
import pandas as pd
from core.utils import write_json

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    corrupted = df.copy()
    logs = []

    if len(corrupted) > 3:
        # 1. Drop 2 dòng mới nhất
        corrupted = corrupted.iloc[2:].reset_index(drop=True)
        logs.append("Dropped top 2 latest paper records.")

        # 2. Xóa tóm tắt của dòng đầu tiên
        corrupted.at[0, "summary"] = ""
        logs.append(f"Cleared summary for paper_id={corrupted.at[0, 'paper_id']}.")

        # 3. Chèn text nhiễu vào dòng thứ 2
        corrupted.at[1, "summary"] = corrupted.at[1, "summary"] + " [NOISE_CORRUPTED_TEXT_DATA]"
        logs.append(f"Injected noise into paper_id={corrupted.at[1, 'paper_id']}.")

        # Cập nhật lại cột text_for_embedding
        corrupted["text_for_embedding"] = (
            "Title: " + corrupted["title"] + " | Authors: " + corrupted["authors_joined"] + " | Summary: " + corrupted["summary"]
        )

    write_json(output_log_path, {"corruption_actions": logs})
    return corrupted
```

---

### 🔴 CHẶNG 6: Pipeline Orchestration (`src/pipelines/phase1.py`)

File: [src/pipelines/phase1.py](file:///d:/VinAI%20in%20Action/VinAI%20Lab/DAY10_2A202601936_NguyenDucHung/src/pipelines/phase1.py)

#### 💡 Lý thuyết chặng 6:
- Ghép nối tất cả các thành phần lại với nhau để chạy từ đầu đến cuối (End-to-End Execution).

#### 📝 Cú pháp code chi tiết:

```python
from datetime import datetime, UTC

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()

    # 1. Ingestion
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    # 2. Cleaning
    df = build_clean_dataframe(records, run_date=datetime.now(UTC))
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    # 3. Vector Indexing
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)

    # 4. Evaluation Set & Metrics
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)
    evaluate_pipeline(settings, index, settings.paths.eval_testset, settings.paths.baseline_metrics, settings.paths.baseline_answers)

    # 5. Observability
    run_data_quality_checks(df, settings, "baseline_quality")
    build_freshness_report(df, settings, settings.paths.freshness_report)

    print("Phase 1 baseline completed successfully!")


if __name__ == "__main__":
    main()
```

---

Bây giờ bạn có thể tiếp tục gõ phần còn lại của `src/ingestion/crossref.py` (hàm `parse_crossref_payload`, `fetch_source_records`, `load_raw_records`) theo đúng cú pháp Chặng 1 nhé!
