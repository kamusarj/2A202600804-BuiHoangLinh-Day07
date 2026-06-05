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

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | OpenAI text-embedding-3-large có bao nhiêu chiều (dimensions) và giá bao nhiêu mỗi 1K tokens? | 3,072 dimensions, $0.00013 per 1K tokens |
| 2 | Theo NIST, "Confabulation" là gì và nó gây rủi ro như thế nào trong lĩnh vực y tế? | Confabulation là GAI tạo nội dung sai lỗi nhưng trình bày tự tin. Trong y tế gây chẩn đoán sai, điều trị sai |
| 3 | Thư viện Hugging Face Transformers có những tính năng chính nào? | Ease of use (2 dòng code), Flexibility (PyTorch nn.Module), Simplicity (All in one file) |
| 4 | Kỹ thuật Chain-of-Thought (CoT) Prompting hoạt động như thế nào và tại sao nó giúp giảm hallucination? | CoT yêu cầu mô hình trình bày từng bước suy luận logic trước khi kết luận, giảm hallucination đáng kể |
| 5 | Tìm các framework về AI risk management được phát triển bởi tổ chức chính phủ Mỹ. Liệt kê 5 rủi ro chính của Generative AI theo NIST. | NIST AI 600-1. 5 rủi ro: CBRN, Confabulation, Dangerous Content, Data Privacy, Environmental |

### Kết Quả Của Tôi

**Strategy:** RecursiveChunker(chunk_size=1000) — 390 chunks tổng cộng
**Backend:** Mock embedder (no local/OpenAI available)

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | OpenAI embedding dimensions & giá | NIST document chunk về governance principles | 0.365 | No — NIST document dominates due to size | [LLM] trả về context từ NIST chunk, không chứa thông tin về OpenAI embedding |
| 2 | NIST Confabulation & y tế | NIST chunk về explainable AI techniques | 0.363 | No — chunk retrieved không phải section Confabulation | [LLM] trả về context về XAI techniques, không phải Confabulation |
| 3 | Hugging Face Transformers features | NIST chunk về AI system tasks (MAP 2.1) | 0.322 | No — NIST document vẫn chiếm ưu thế | [LLM] trả về context từ NIST, không phải Hugging Face |
| 4 | Chain-of-Thought prompting | NIST chunk về Dangerous/Violent/Hateful Content | 0.448 | No — không chứa thông tin về CoT | [LLM] trả về context về AI safety assessment |
| 5 | AI risk framework của Mỹ + 5 rủi ro | NIST chunk về GAI model behavior visualization | 0.327 | Partial — chunk #2 (score 0.322) chứa "CBRN Information or Capabilities" | N/A (query 5 dùng metadata filter) |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 0 / 5

**Phân tích:**
> Kết quả retrieval không chính xác do đang dùng `_mock_embed` — mock embedder sử dụng hash-based deterministic, không capture được ngữ nghĩa thực. NIST document chiếm 206K chars (~70% tổng corpus) nên mock embedding tạo ra nhiều chunks có dot product cao ngẫu nhiên với hầu hết query. Metadata filter tại query 5 hoạt động chính xác (chỉ trả về chunks từ `source=nist-framework`), chứng minh `search_with_filter()` hoạt động đúng.

**Cần cải thiện:** Chạy lại benchmark với `LocalEmbedder` (all-MiniLM-L6-v2) hoặc `OpenAIEmbedder` để có kết quả semantic retrieval chính xác.

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
| 1 | embedding_models_comparison.md | Technical documentation | 11,739 | category=embedding, source=technical-documentation, language=en, difficulty=advanced |
| 2 | genAI.md | Academic paper (Feuerriegel et al., 2023) | 64,225 | category=generative-ai, source=academic-paper, language=en, difficulty=advanced |
| 3 | nlp_co_ban.md | Hugging Face Course | 2,578 | category=nlp, source=huggingface-course, language=en, difficulty=intermediate |
| 4 | prompt_engineering_fundamentals.txt | Technical guide (Hoang Trung Quan) | 3,182 | category=prompt-engineering, source=technical-guide, language=vi, difficulty=intermediate |
| 5 | nist_generative_ai_profile.md | NIST (https://doi.org/10.6028/NIST.AI.600-1) | 206,554 | category=ai-risk, source=nist-framework, language=en, difficulty=advanced |

### Metadata Schema
| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | str | embedding, generative-ai, nlp, prompt-engineering, ai-risk | Phân loại chủ đề tài liệu, giúp filter nhanh khi query theo từng mảng nội dung |
| source | str | technical-documentation, academic-paper, huggingface-course, technical-guide, nist-framework | Xác định nguồn gốc và độ tin cậy, hỗ trợ filter theo loại nguồn |
| language | str | en, vi | Lọc tài liệu theo ngôn ngữ, quan trọng khi query đa ngôn ngữ |
| difficulty | str | beginner, intermediate, advanced | Phân cấp độ phức tạp, hữu ích cho hệ thống adaptive retrieval |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline: ChunkingStrategyComparator

Kết quả chạy `ChunkingStrategyComparator` trên các tài liệu:

| Document | FixedSize (count/avg_len) | SentenceChunker (count/avg_len) | RecursiveChunker (count/avg_len) |
|----------|--------------------------|--------------------------------|----------------------------------|
| genAI.md | 317 chunks / 200 | 87 chunks / 716 | 65 chunks / 988 |
| nist_generative_ai_profile.md | 1026 chunks / 200 | 211 chunks / 975 | 205 chunks / 1002 |
| embedding_models_comparison.md | 58 chunks / 198 | 16 chunks / 648 | 13 chunks / 855 |

### Strategy Của Tôi: **RecursiveChunker (chunk_size=1000)**

**Lý do chọn:**
> RecursiveChunker ưu tiên giữ nguyên ranh giới ngữ nghĩa (paragraph → sentence → word) thay vì cắt cứng theo kích thước. Với bộ tài liệu đa dạng (academic paper, technical guide, framework document), việc bảo toàn cấu trúc ngữ nghĩa giúp mỗi chunk chứa một ý hoàn chỉnh, cải thiện retrieval quality. Chọn chunk_size=1000 (gấp đôi mặc định 500) để cung cấp đủ ngữ cảnh cho các câu hỏi phức tạp về GAI risks và technical concepts.

**So sánh với baseline:**
> - **FixedSize (chunk_size=200)**: 1026 chunks cho NIST — quá nhiều, mỗi chunk quá nhỏ để chứa đủ ngữ cảnh
> - **SentenceChunker**: Tốt hơn về mặt coherence nhưng vẫn phụ thuộc vào dấu câu, không xử lý tốt với tài liệu có bảng biểu phức tạp như NIST
> - **RecursiveChunker (1000)**: 205 chunks cho NIST, mỗi chunk ~1000 ký tự — đủ lớn cho context nhưng không quá lớn gây nhiễu

**Metadata Strategy:**
> Sử dụng YAML front matter trong mỗi file để lưu metadata. Khi load, parse front matter và merge với schema thống nhất của nhóm (`category`, `source`, `language`, `difficulty`). Metadata được dùng trong `search_with_filter()` cho Query 5 (filter theo `source=nist-framework`).

---

## 7. What I Learned (5 điểm — Demo)

> *Phần này hoàn thành sau khi demo và thảo luận nhóm.*


---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | _ / 5 |
| **Tổng** | | **80 / 100** (chờ demo nhóm) |
