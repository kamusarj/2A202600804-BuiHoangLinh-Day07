# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Hoàng Linh
**Nhóm:** [Tên nhóm]
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai đoạn văn bản có high cosine similarity khi vector embedding của chúng cùng hướng trong không gian vector, tức là chúng có nội dung ngữ nghĩa gần giống nhau. Điểm similarity ≈ 1 nghĩa là hoàn toàn tương đồng về hướng.

**Ví dụ HIGH similarity:**
- Sentence A: "Python là ngôn ngữ lập trình bậc cao"
- Sentence B: "Python là một high-level programming language"
- Tại sao tương đồng: Cả hai câu đều nói về Python là ngôn ngữ lập trình, chỉ khác ngôn ngữ diễn đạt (Việt vs Anh). Embedding bắt được ý nghĩa bất kể ngôn ngữ.

**Ví dụ LOW similarity:**
- Sentence A: "Hà Nội là thủ đô của Việt Nam"
- Sentence B: "Con mèo đang ngủ trên ghế sofa"
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (địa lý vs sinh hoạt hàng ngày), không có từ khóa chung, hướng vector gần như trực giao.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity chỉ đo góc giữa hai vector, bỏ qua độ lớn (magnitude). Với text embeddings đã được chuẩn hóa hoặc sinh ra từ các mô hình như all-MiniLM, hướng của vector quan trọng hơn độ dài. Euclidean distance bị ảnh hưởng bởi magnitude — hai văn bản cùng ý nghĩa nhưng độ dài khác nhau sẽ có vector khác magnitude, dẫn đến Euclidean distance lớn dù cùng hướng.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`
> Đáp án: 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`. Số chunk tăng từ 23 lên 25. Overlap nhiều hơn giúp đảm bảo thông tin không bị cắt mất ở ranh giới giữa các chunk, giúp retrieval tìm được ngữ cảnh đầy đủ hơn, đặc biệt khi câu trả lời nằm ở vùng giao giữa hai chunk.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `re.split(r"(?<=[.!?])\s+", text)` để tách văn bản thành các câu dựa trên dấu kết thúc câu (`.!?`) kèm khoảng trắng. Chú ý: dùng positive lookbehind `(?<=...)` để giữ dấu câu trong câu gốc. Các câu được strip whitespace và lọc bỏ câu rỗng, sau đó nhóm theo `max_sentences_per_chunk`. Kết quả đảm bảo mỗi chunk là một chuỗi câu liền mạch, không làm vỡ ranh giới câu.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy thử từng separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`). Mỗi bước: tách văn bản hiện tại bằng separator, merge các phần nhỏ thành chunk vừa ≤ chunk_size, các phần lớn hơn được đệ quy xử lý với separator tiếp theo. Base case: (1) text ≤ chunk_size → return [text], (2) hết separators → force-split theo chunk_size. Cách merge "greedy" từ trái sang phải giúp giữ tối đa ngữ cảnh trong mỗi chunk.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `_make_record` tạo bản ghi gồm id, content, metadata (kèm `doc_id`) và embedding từ hàm `embedding_fn`. `add_documents` lặp qua từng Document, tạo record và append vào `self._store` (in-memory) hoặc gọi `collection.add()` (ChromaDB). `search` embed query, tính dot product giữa query embedding và tất cả stored embeddings, sắp xếp giảm dần và trả về top-k bản ghi gồm `content`, `metadata`, `score`.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` lọc trước (pre-filter): lọc toàn bộ `_store` theo metadata_filter (tất cả key-value phải khớp), sau đó chạy similarity search trên tập đã lọc. Nếu không có filter thì fallback sang `search` thông thường. `delete_document` xóa tất cả bản ghi có `metadata["doc_id"] == doc_id`, trả về True nếu có ít nhất một bản ghi bị xóa.

### KnowledgeBaseAgent

**`answer`** — approach:
> Triển khai RAG pattern: (1) Gọi `store.search(question, top_k)` để lấy top-k chunks liên quan. (2) Xây dựng prompt với context từ các chunk đánh số `[Chunk 1] ... [Chunk 2] ...`. (3) Gọi `llm_fn(prompt)` để sinh câu trả lời. Prompt structure gồm 3 phần: context blocks, question, và nhắc "Answer:" để LLM biết cần trả lời.

### Test Results

```
============================== 42 passed in 0.63s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Python là ngôn ngữ lập trình" | "Python is a programming language" | high | | |
| 2 | "Chó là động vật trung thành" | "Mèo thích bắt chuột" | low | | |
| 3 | "AI đang thay đổi thế giới" | "Trí tuệ nhân tạo biến đổi ngành công nghiệp" | high | | |
| 4 | "Hôm nay trời đẹp" | "Cấu trúc dữ liệu và giải thuật" | low | | |
| 5 | "Vector database lưu embeddings" | "Embedding store dùng cho similarity search" | high | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Sẽ điền sau khi chạy thực tế với compute_similarity(). Dự đoán cặp 3 (AI ↔ Trí tuệ nhân tạo) sẽ gây bất ngờ vì mock embedder dùng hash-based deterministic, không thực sự hiểu ngữ nghĩa, nên similarity có thể thấp hơn mong đợi. Điều này cho thấy embedding quality phụ thuộc hoàn toàn vào backend — mock chỉ để test code, cần embedder thật (local/openai) để đánh giá ngữ nghĩa chính xác.*

---

## 6. Results — Cá nhân (10 điểm)

> *Phần này hoàn thành sau khi nhóm thống nhất benchmark queries và chạy trên implementation cá nhân.*

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 2. Document Selection — Nhóm (10 điểm)

> *Phần này hoàn thành cùng nhóm.*

### Domain & Lý Do Chọn
**Domain:** Generative AI Risk Management & Governance (Quản trị rủi ro AI sinh tạo)
**Tại sao nhóm chọn domain này?**
> Generative AI đang phát triển nhanh chóng kéo theo các vấn đề về rủi ro, đạo đức và quản trị. Tài liệu NIST AI 600-1 là khung quản trị rủi ro AI chính thức từ chính phủ Mỹ, bao gồm các mapping cho GAI risks. Đây là domain giàu nội dung ngữ nghĩa, có cấu trúc rõ ràng, phù hợp để kiểm tra các chiến lược chunking và RAG.

### Data Inventory
| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | NIST AI 600-1: AI RMF Generative AI Profile | NIST (https://doi.org/10.6028/NIST.AI.600-1) | 206,681 | category=framework, source=nist, date=2024-07, type=gai_risk_management |
| 2 | Generative AI Boundaries & Limitations | Academic paper excerpt | 6,728 | category=limitations, source=academic, type=gai_technical_limits |

### Metadata Schema
| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | str | framework, limitations | Phân loại chủ đề tài liệu, giúp filter nhanh khi query theo từng mảng nội dung |
| source | str | nist, academic | Xác định nguồn gốc tài liệu, hỗ trợ filter theo độ tin cậy hoặc loại nguồn |
| type | str | gai_risk_management, gai_technical_limits | Mô tả chi tiết nội dung, giúp truy xuất chính xác loại thông tin cần tìm |
| date | str | 2024-07 | Lọc theo thời gian phát hành, quan trọng với tài liệu có cập nhật định kỳ |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

> *Phần này hoàn thành sau khi chạy benchmark cùng nhóm.*

---

## 7. What I Learned (5 điểm — Demo)

> *Phần này hoàn thành sau khi demo và thảo luận nhóm.*


---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | _ / 10 |
| Chunking strategy | Nhóm | _ / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | _ / 5 |
| Results | Cá nhân | _ / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | _ / 5 |
| **Tổng** | | **45 / 100** (phần cá nhân đã hoàn thành, chờ nhóm) |
