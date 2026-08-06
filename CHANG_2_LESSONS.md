# 📖 BÀI HỌC VÀ GIẢI THÍCH CHI TIẾT: CHẶNG 2 (DATA CLEANING)

Tài liệu này tổng hợp toàn bộ kiến thức chuyên sâu, giải thích từng dòng cú pháp Python và các bài học kỹ thuật thu được sau khi hoàn thành **Chặng 2 (`src/ingestion/cleaning.py`)**.

---

## 🎯 1. TỔNG QUAN CHẶNG 2: VAI TRÒ CỦA DATA CLEANING TRONG RAG
Nếu Chặng 1 (`crossref.py`) có nhiệm vụ "mang dữ liệu thô từ bên ngoài về nhà", thì **Chặng 2 (`cleaning.py`)** đóng vai trò là **Chốt chặn chất lượng (Quality Gate)** biến dữ liệu thô thành **Pandas DataFrame chuẩn mực** trước khi đưa vào mô hình Vector Embedding và ChromaDB.

### 💡 Bài học cốt lõi:
1. **Lọc dữ liệu rác (Junk Data Filtering)**: Một bài báo thiếu tiêu đề hoặc tóm tắt quá ngắn (dưới 100 ký tự) sẽ cung cấp quá ít ngữ cảnh, khiến mô hình Embedding tính toán vector sai lệch $\rightarrow$ Cần chủ động loại bỏ (`summary_chars >= 100`).
2. **Xây dựng Thuộc tính biểu diễn Ngữ nghĩa (`text_for_embedding`)**:
   - Định dạng chuẩn đề bài: `Title: [title] | Authors: [authors_joined] | Summary: [summary]`.
   - **Tác dụng**: Giúp mô hình Vector Search (`all-MiniLM-L6-v2`) ghi nhận đồng thời thông tin về **Tiêu đề + Tác giả + Nội dung nghiên cứu** trong cùng một không gian vector. Khi người dùng tìm kiếm theo tên tác giả hoặc chủ đề, vector search vẫn truy vấn ra chính xác.

---

## 🔬 2. GIẢI THÍCH CHI TIẾT 5 YÊU CẦU KỸ THUẬT VÀ CÚ PHÁP PYTHON

---

### A. Ghép Chuỗi Danh Sách Tác Giả & Danh Mục (`authors_joined`, `categories_joined`)

```python
authors = [normalize_whitespace(a) for a in rec.authors if a]
authors_joined = compact_join(authors)

categories = [normalize_whitespace(c) for c in rec.categories if c]
categories_joined = compact_join(categories)
```

#### 🔍 Giải thích cú pháp & Kiến thức:
- **`compact_join(items, sep=", ")`**: Hàm utility trong `core.utils` giúp ghép một danh sách các phần tử chuỗi thành một chuỗi duy nhất phân tách bằng dấu phẩy `, `, tự động loại bỏ các phần tử rỗng.
- **Ví dụ**: `['Anna Smith', 'John Doe']` $\rightarrow$ `"Anna Smith, John Doe"`.

---

### B. Tính Độ Tươi Dữ Liệu (`age_days`) & Xử Lý An Toàn

```python
if rec.published:
    try:
        pub_dt = datetime.strptime(rec.published, "%Y-%m-%d").date()
        age_days = (run_dt_date - pub_dt).days
    except (ValueError, TypeError):
        age_days = 9999
else:
    age_days = 9999
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **Khái niệm Data Age**: `age_days` đo khoảng cách số ngày giữa ngày chạy pipeline (`run_date`) và ngày bài báo xuất bản (`published`).
2. **Kỹ thuật Phòng vệ (Defensive Value Assignment)**:
   - Ở Chặng 1, nếu bài báo thiếu ngày xuất bản, ta đã gán fallback `rec.published = ""`.
   - Khi `rec.published` bị rỗng hoặc lỗi định dạng, ta gán `age_days = 9999` (một con số rất lớn).
   - **Lý do**: Hệ thống Observability ở Chặng 4 sẽ dựa vào `age_days > 180` để phát hiện đây là bài báo cũ/thiếu ngày. Nếu ta gán ngày hiện tại, Observability sẽ bị đánh lừa là bài báo mới 100%.

---

### C. Tạo Cột Biểu Diễn Ngữ Nghĩa (`text_for_embedding`)

```python
text_for_embedding = (
    f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"
).strip()
```

#### 🔍 Giải thích cú pháp & Kiến thức:
- Dùng **f-string** trong Python để tạo chuỗi văn bản hoàn chỉnh.
- Định dạng `Title: ... | Authors: ... | Summary: ...` giúp phân định rõ ràng các vùng thông tin cho mô hình Transformer Embedding khi tính toán khoảng cách cosine similarity.

---

### D. Lọc Bỏ Bản Ghi Rác & Khử Trùng Lặp bằng Pandas

```python
# 1. Lọc bỏ dòng rỗng tiêu đề hoặc summary < 100 ký tự
df = df.dropna(subset=["paper_id", "title"])
df = df[(df["paper_id"].str.strip() != "") & (df["title"].str.strip() != "")]
df = df[df["summary_chars"] >= 100]

# 2. Khử trùng lặp paper_id & Sắp xếp ngày giảm dần
df = df.drop_duplicates(subset=["paper_id"], keep="first")
df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **`df.dropna(subset=[...])`**: Loại bỏ các dòng chứa giá trị `NaN` / `None` trong các cột quan trọng.
2. **`df["summary_chars"] >= 100`**: Đảm bảo tóm tắt bài báo có độ dài tối thiểu 100 ký tự để có đủ nội dung thông tin khoa học.
3. **`df.drop_duplicates(subset=["paper_id"], keep="first")`**:
   - Giữ lại bản ghi xuất hiện đầu tiên và xóa bỏ mọi bản ghi trùng lặp mã `paper_id` (DOI).
   - **Lý do**: Bài báo trùng lặp sẽ làm phình to Vector Store ChromaDB và gây lãng phí chi phí tính toán embedding.
4. **`df.sort_values(by="published", ascending=False)`**: Sắp xếp DataFrame sao cho các bài báo mới nhất nằm ở trên cùng.

---

## 💻 3. MÃ NGUỒN MẪU HOÀN CHỈNH CHO `src/ingestion/cleaning.py`

```python
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
```

---

## ❓ CÂU HỎI TỰ KIỂM TRA KIẾN THỨC CHẶNG 2 (QUIZ)

1. **Câu 1**: Tại sao chúng ta cần lọc bỏ các bài báo có phần tóm tắt quá ngắn (`summary_chars < 100`)?
   - *Trả lời*: Vì tóm tắt quá ngắn cung cấp quá ít ngữ cảnh khoa học, làm mô hình Vector Search dễ bị tính toán sai khoảng cách vector và gây nhiễu cho RAG Agent.
2. **Câu 2**: Việc gán `age_days = 9999` khi bài báo thiếu ngày xuất bản (`published = ""`) có tác dụng gì đối với Data Observability?
   - *Trả lời*: Giúp hệ thống Observability ở Chặng 4 nhận biết đây là bài báo thiếu/mốc ngày, tránh bị đánh lừa là bài báo mới 100%.
3. **Câu 3**: Tại sao phải dùng `drop_duplicates(subset=["paper_id"])` trước khi xuất file clean?
   - *Trả lời*: Để tránh lưu trữ các bài báo trùng mã DOI vào ChromaDB, tiết kiệm bộ nhớ RAM/Disk và tăng tốc độ tìm kiếm Vector.

---

Chúc mừng bạn đã làm chủ kiến thức của **CHẶNG 2**!
