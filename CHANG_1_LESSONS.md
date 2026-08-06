# 📖 BÀI HỌC VÀ GIẢI THÍCH CHI TIẾT: CHẶNG 1 (DATA INGESTION)

Tài liệu này tổng hợp toàn bộ kiến thức chuyên sâu, giải thích từng dòng cú pháp Python và các bài học kỹ thuật thu được sau khi hoàn thành **Chặng 1 (`src/ingestion/crossref.py`)**.

---

## 🎯 1. TỔNG QUAN CHẶNG 1: VAI TRÒ CỦA DATA INGESTION
Trong kiến trúc **Data Pipeline cho RAG**, **Data Ingestion (Thu nhập dữ liệu)** là chặng đầu tiên chịu trách nhiệm giao tiếp với thế giới bên ngoài (API, Database, File Server).

### 💡 Khái niệm Raw Artifact (File sản vật dữ liệu thô):
- **Artifact**: Trong lập trình, *Artifact* là bất kỳ file dữ liệu/thành phẩm nào được hệ thống tạo ra và lưu trữ lại (như file `.json`, `.csv`, `.pth`, `.md`...).
- **Raw Artifact**: Là file chứa **dữ liệu nguyên bản 100%** thu thập từ API bên ngoài ngay tại thời điểm gọi, chưa qua bất kỳ thao tác làm sạch hay chỉnh sửa nào (ví dụ: `data/raw/crossref_response.json`).

### 🛡️ 4 Lợi ích vàng của Raw Artifact:
1. **Khả năng Tái Tạo & Phục Hồi (Replayability)**: Khi muốn sửa lại logic làm sạch hoặc lấy thêm trường dữ liệu mới, bạn không cần gọi lại API bên ngoài mà chỉ cần đọc lại file Raw Artifact.
2. **Truy Vết Nguồn Gốc & Tìm Lỗi (Auditability & Lineage)**: Phân định rõ lỗi do API gốc trả về sai hay do code cleaning làm hỏng.
3. **Chạy Offline mượt mà (Offline Independence / Caching)**: Giúp chạy lại Pipeline hàng trăm lần mà không sợ rủi ro đứt mạng, sập API hay bị chặn IP (HTTP 429).
4. **Bằng chứng dữ liệu minh bạch (Data Provenance)**: Đảm bảo tính pháp lý và nguồn gốc thu thập dữ liệu.

---

## 🏗️ 2. TẠI SAO LẠI LỌC BỚT CÁC TRƯỜNG METADATA PHỤ TỪ API GỐC?

Crossref API thô trả về rất nhiều trường như `is-referenced-by-count` (số lượt trích dẫn), `publisher` (nhà xuất bản), `ISSN`, `volume`, `page`, `license`, `score`... Nhưng trong `PaperRecord` schema ta lại lọc bỏ chúng. Đây là một **quyết định thiết kế kiến trúc (Data Architecture Design)**:

1. **Giảm từ nhiễu cho mô hình Vector Search (Noise Reduction)**: RAG Agent dùng `all-MiniLM-L6-v2` để tìm kiếm theo **nội dung khoa học**. Các trường kỹ thuật như `ISSN: 2949-1894` hay `Volume: 7` làm "loãng" ngữ cảnh, khiến Vector Search kém chính xác.
2. **Chuẩn hóa Schema đa nguồn (Cross-Source Standardization)**: Các nguồn dữ liệu khác (như arXiv, PubMed) không có trường `ISSN` hay `publisher` như Crossref. Giữ `PaperRecord` gọn nhẹ giúp pipeline dễ dàng tích hợp đa nguồn.
3. **Tối ưu tốc độ ChromaDB Vector Store**: Loại bỏ trường thừa giúp giảm dung lượng RAM/Disk và tăng tốc độ truy vấn Top-K.
4. **Dữ liệu thô VẪN ĐƯỢC GIỮ NGUYÊN trong `crossref_response.json`**: Nếu tương lai hệ thống muốn nâng cấp tính năng lọc theo nhà xuất bản hay trích dẫn, ta chỉ cần đọc lại Raw Artifact mà không cần crawl lại.

---

## 🔬 3. GIẢI THÍCH CHI TIẾT TỪNG HÀM VÀ CÚ PHÁP PYTHON

---

### A. Hàm Trợ Giúp `_clean_xml_tags(text)`

```python
def _clean_xml_tags(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(cleaned)
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **Tại sao Crossref API lại có thẻ XML?**: Các nhà xuất bản khoa học (Elsevier, Springer...) lưu trữ tóm tắt (abstract) theo chuẩn NLM/JATS XML (như `<jats:p>This paper presents...</jats:p>`). Khi đưa vào Vector Embedding, các thẻ này là "từ nhiễu" làm sai lệch khoảng cách vector.
2. **Cú pháp Biểu thức chính quy (Regex) `r"<[^>]+>"`**:
   - `<`: Bắt đầu bằng dấu mở ngoặc nhọn.
   - `[^>]+`: Khớp với 1 hoặc nhiều ký tự **không phải** là dấu đóng ngoặc nhọn `>`.
   - `>`: Kết thúc bằng dấu đóng ngoặc nhọn.
   - `re.sub(pattern, replacement, string)`: Thay thế tất cả các thẻ XML tìm thấy bằng 1 khoảng trắng `" "`.
3. **`normalize_whitespace(cleaned)`**: Hàm utility rút gọn nhiều khoảng trắng liên tiếp (như `"  \n\t  "`) thành 1 khoảng trắng duy nhất `" "`.

---

### B. Hàm Trợ Giúp `_extract_date(date_struct)`

```python
def _extract_date(date_struct: dict[str, Any] | None) -> str:
    fallback = ""  # Nếu thiếu ngày tháng thì trả về chuỗi rỗng "" (không lấy ngày hiện tại)
    if not date_struct or not isinstance(date_struct, dict) or "date-parts" not in date_struct:
        return fallback

    date_parts = date_struct.get("date-parts", [[]])
    if not isinstance(date_parts, list) or not date_parts or not isinstance(date_parts[0], list) or not date_parts[0]:
        return fallback

    parts = date_parts[0]
    try:
        if not parts or parts[0] is None:
            return fallback
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 and parts[1] is not None else 1
        day = int(parts[2]) if len(parts) > 2 and parts[2] is not None else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    except (ValueError, TypeError):
        return fallback
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **Chính sách Fallback Chuỗi Rỗng `""`**:
   - Nếu bài báo không có dữ liệu ngày tháng, ta trả về chuỗi rỗng `""` thay vì lấy ngày hiện tại `today`.
   - **Lý do**: Nếu gắn ngày hôm nay cho một bài báo không rõ ngày xuất bản, hệ thống Observability ở Chặng 4 sẽ coi bài báo đó mới 100% (gây sai lệch chỉ số Freshness).
2. **Cấu trúc dữ liệu không nhất quán trong `date-parts`**:
   - API có thể trả về `[[2024, 5, 12]]` (đủ ngày tháng năm), hoặc `[[2024, 5]]` (chỉ có năm tháng), hoặc `[[2024]]` (chỉ có năm).
   - Nếu có Năm nhưng thiếu Tháng/Ngày, ta tự động chuẩn hóa về ngày đầu tháng/năm (`month=1`, `day=1`).
3. **Kỹ thuật phòng vệ (Defensive Programming)**:
   - Dùng `len(parts) > 0` và `isinstance(..., dict)` để kiểm tra kiểu dữ liệu trước khi truy cập chỉ số, tránh lỗi `AttributeError` hay `IndexError`.
   - Bọc khối `try...except (ValueError, TypeError)` khi ép kiểu `int()` tránh crash khi gặp chuỗi ngày lỗi.

3. **Định dạng chuỗi có chèn số 0 đi kèm (Formatting)**:
   - `f"{year:04d}-{month:02d}-{day:02d}"`:
     - `:04d`: Ép kiểu số nguyên (`d`), nếu ít hơn 4 chữ số thì tự động thêm số 0 vào trước (Ví dụ: `2024`).
     - `:02d`: Ép kiểu số nguyên (`d`), nếu ít hơn 2 chữ số thì tự động thêm số 0 vào trước (Ví dụ: Tháng `5` $\rightarrow$ `"05"`).

---

### C. Hàm Core `parse_crossref_payload(payload)`

```python
def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    if not isinstance(payload, dict):
        return []

    items = payload.get("message", {}).get("items", [])
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    ...
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **An toàn với Dictionary `.get()` lồng nhau**:
   - `payload.get("message", {}).get("items", [])`: Nếu `message` không có trong dict, nó trả về `{}` (dict rỗng) thay vì văng lỗi `KeyError`. Sau đó tiếp tục `.get("items", [])` trả về danh sách rỗng nếu không tìm thấy.
2. **Trích xuất Tác giả (Authors)**:
   ```python
   for author in author_list:
       if not isinstance(author, dict):
           continue
       given = str(author.get("given", "") or "").strip()
       family = str(author.get("family", "") or "").strip()
       name = f"{given} {family}".strip() if given and family else (family or given)
   ```
   - Xử lý các trường hợp tên bài báo: Có cả `given` (Tên) và `family` (Họ), hoặc chỉ có một trong hai.
3. **Đóng gói bằng Dataclass `PaperRecord`**:
   - Dataclass giúp định nghĩa một cấu trúc dữ liệu tường minh (strong typing), bất biến (`frozen=True`), giúp code đọc dễ hơn rất nhiều so với việc dùng dict thuần túy.

---

### D. Hàm Gọi API `fetch_source_records(settings)`

```python
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

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)

    raw_records_data = [asdict(record) for record in records]
    write_json(settings.paths.raw_records_json, raw_records_data)

    return records
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **Khái niệm Polite Pool trong Crossref**:
   - Khi truyền `User-Agent` chứa email `mailto:...`, Crossref API sẽ chuyển request của bạn vào hàng chờ ưu tiên ("polite pool") giúp tốc độ phản hồi nhanh hơn và không bị block IP.
2. **Thuật toán Exponential Backoff (Thử lại tăng dần)**:
   - Lần 1 lỗi: Chờ `1.0` giây.
   - Lần 2 lỗi: Chờ `2.0` giây (`backoff *= 2`).
   - Lần 3 lỗi: Chờ `4.0` giây.
   - Việc này giúp giảm tải áp lực cho server khi dịch vụ API bên ngoài đang bị quá tải (HTTP 429 / 503).
3. **Lưu trữ 2 Dạng Raw Artifacts**:
   - `write_json(settings.paths.raw_api_response, payload)`: Lưu file JSON thô chuẩn cấu hình API gốc.
   - `asdict(record)`: Chuyển đối tượng `PaperRecord` (Dataclass) thành Dictionary Python để có thể ghi ra file JSON `crossref_records.json`.

---

### E. Hàm Khôi Phục `load_raw_records(path)`

```python
def load_raw_records(path: Path) -> list[PaperRecord]:
    raw_data = read_json(path)
    records: list[PaperRecord] = []
    for item in raw_data:
        records.append(PaperRecord(**item))
```

#### 🔍 Giải thích cú pháp & Kiến thức:
1. **Khái niệm Deserialization (Giải tuần tự hóa)**: Đọc chuỗi văn bản JSON từ đĩa và khôi phục thành các đối tượng Python mạnh (`PaperRecord`).
2. **Cú pháp Unpacking Kwargs `PaperRecord(**item)`**:
   - Nếu `item` là `{"paper_id": "10.123/x", "title": "ABC", ...}`, cú pháp `**item` tương đương với `PaperRecord(paper_id="10.123/x", title="ABC", ...)`.

---

## 🛡️ 4. BÀI HỌC VỀ LẬP TRÌNH PHÒNG THỦ (DEFENSIVE PROGRAMMING & EDGE CASES)

| Edge Case | Rủi ro | Giải pháp Lập trình Phòng thủ |
| :--- | :--- | :--- |
| **1. Payload bị `None` hoặc không phải dict** | `payload.get(...)` sẽ quăng lỗi `AttributeError` | `if not isinstance(payload, dict): return []` |
| **2. Mảng chứa phần tử `None`** | `author.get(...)` sẽ văng lỗi khi gặp phần tử `None` | `if not isinstance(author, dict): continue` |
| **3. Ngày tháng bị lỗi kiểu dữ liệu** | `f"{year:04d}"` sẽ văng `TypeError` nếu `year` là `None` | `try...except (ValueError, TypeError)` kèm giá trị fallback |
| **4. Tiêu đề bài báo biến thành chuỗi `"None"`** | Hàm `str(None)` chuyển `None` thành chuỗi `"None"` hợp lệ | Thêm bộ lọc `if not doi or not title or title.lower() == "none": continue` |

---

## ❓ CÂU HỎI TỰ KIỂM TRA KIẾN THỨC CHẶNG 1 (QUIZ)

1. **Câu 1**: Tại sao chúng ta cần lưu cả 2 file `crossref_response.json` và `crossref_records.json` thay vì chỉ lưu 1 file?
   - *Trả lời*: File `crossref_response.json` là Raw Artifact để audit API gốc và bảo tồn 100% trường dữ liệu. File `crossref_records.json` là mảng phẳng đã parse để ứng dụng load nhanh offline.
2. **Câu 2**: Biểu thức Regex `re.sub(r"<[^>]+>", " ", text)` xử lý chuỗi `<jats:p>Hello World</jats:p>` như thế nào?
   - *Trả lời*: Thay thế các thẻ XML bằng khoảng trắng, tạo thành `" Hello World "`, sau đó qua `normalize_whitespace()` thành `"Hello World"`.
3. **Câu 3**: Lý do kỹ thuật tại sao ta lại loại bỏ các trường `ISSN`, `volume`, `page`, `license` khi đưa vào `PaperRecord` schema?
   - *Trả lời*: Để giảm từ nhiễu cho mô hình Vector Search, chuẩn hóa schema đa nguồn và tiết kiệm dung lượng lưu trữ ChromaDB.
4. **Câu 4**: Tại sao phải sử dụng `isinstance(..., dict)` trước khi gọi `.get()` trong xử lý JSON thô từ bên ngoài?
   - *Trả lời*: Phòng trường hợp phần tử JSON bị `None` hoặc biến thành mảng/chuỗi không có phương thức `.get()`.

---

Chúc mừng bạn đã hoàn thiện 100% cuốn giáo trình thu nhỏ cho **CHẶNG 1**!
