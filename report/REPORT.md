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
- Sentence B: "Python is a high-level programming language"
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

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Generative AI & Natural Language Processing (GAI + NLP)

**Tại sao nhóm chọn domain này?**
> Nhóm chọn đa domain (GAI risks + NLP fundamentals + Prompt Engineering) để kiểm tra khả năng retrieval cross-domain. Bộ tài liệu cover từ technical guide (embedding models comparison, prompt engineering), academic paper (genAI conceptualization), đến government framework (NIST AI 600-1). Điều này giúp benchmark đánh giá được: (1) retrieval precision khi câu trả lời nằm trong đúng document, (2) khả năng metadata filtering để tách domain, (3) chunking strategy nào xử lý tốt tài liệu đa dạng.

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
| difficulty | str | intermediate, advanced | Phân cấp độ phức tạp, hữu ích cho hệ thống adaptive retrieval |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (chunk_size=200):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| genAI.md | FixedSizeChunker | 317 | 200 | Không — cắt cứng giữa câu |
| genAI.md | SentenceChunker | 108 | 585 | Có — giữ ranh giới câu |
| genAI.md | RecursiveChunker | 478 | 131 | Kém — separator " " cắt quá sớm |
| embedding_models_comparison.md | FixedSizeChunker | 58 | 198 | Không |
| embedding_models_comparison.md | SentenceChunker | 30 | 381 | Có |
| embedding_models_comparison.md | RecursiveChunker | 101 | 112 | Kém |
| nist_generative_ai_profile.md | FixedSizeChunker | 1026 | 200 | Không — quá nhiều chunk |
| nist_generative_ai_profile.md | SentenceChunker | 343 | 571 | Khá — nhưng vẫn nhiều |
| nist_generative_ai_profile.md | RecursiveChunker | 1562 | 130 | Kém — quá nhiều chunk nhỏ |

### Strategy Của Tôi

**Loại:** RecursiveChunker (chunk_size=1000)

**Mô tả cách hoạt động:**
> RecursiveChunker tách văn bản theo thứ tự ưu tiên separator: `\n\n` → `\n` → `. ` → ` ` → force-split. Ở mỗi mức, các phần được merge greedy từ trái sang phải sao cho mỗi chunk ≤ chunk_size. Phần vượt quá được đệ quy xuống separator tiếp theo. Base case: (1) text ≤ chunk_size → return [text], (2) hết separators → cắt cứng theo chunk_size.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Bộ tài liệu có cấu trúc đa dạng: academic paper (paragraphs, headings), technical guide (sections, bullet points), framework document (tables, subsections). RecursiveChunker bảo toàn ranh giới ngữ nghĩa tự nhiên — paragraphs và sentence boundaries không bị cắt ngang. Chọn chunk_size=1000 (thay vì 200) để mỗi chunk chứa đủ ngữ cảnh cho câu hỏi phức tạp về GAI risks và technical concepts, đồng thời giảm ~73% số chunk so với FixedSize(200), giảm nhiễu đáng kể.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | FixedSize(200) | Sentence(3) | Recursive(200) | **Recursive(1000) — My** |
|----------|---------------|-------------|----------------|--------------------------|
| genAI.md | 317 | 108 | 478 | **94** |
| nist_generative_ai_profile.md | 1026 | 343 | 1562 | **275** |
| embedding_models_comparison.md | 58 | 30 | 101 | **14** |
| nlp_co_ban.md | 13 | 6 | 19 | **4** |
| prompt_engineering_fundamentals.txt | 11 | 5 | 19 | **3** |
| **Tổng** | 1425 | 492 | 2179 | **390** |

### So Sánh 3 Strategies Với Embedder Thật (OpenRouter)

Chạy benchmark OpenRouter (`openai/text-embedding-3-small`, 1536 dims) với 3 strategies:

| Query | FixedSize (500, overlap=100) | Sentence (max 5) | **Recursive (1000) — My** |
|-------|------------------------------|-------------------|--------------------------|
| Q1 (OpenAI embedding) | 0.77 — embedding_models ✓ | **0.83** — embedding_models ✓ | 0.79 — embedding_models ✓ |
| Q2 (Confabulation) | 0.47 — nist ✓ | 0.47 — nist ✓ | **0.69** — nist ✓ |
| Q3 (HF Transformers) | 0.47 — nlp_co_ban ✓ | **0.39** — nlp_co_ban ✓ (đúng chunk features) | 0.54 — nlp_co_ban ✓ |
| Q4 (CoT — tiếng Việt) | **0.64** — prompt_eng ✓ | 0.60 — prompt_eng ✓ | 0.62 — prompt_eng ✓ |
| Q5 (filtered) | 0.74 — nist ✓ | 0.67 — nist ✓ | **0.75** — nist ✓ |

**Nhận xét:**
- **SentenceChunker**: Precision cao nhất (Q3 hit đúng chunk "main features"), nhưng score thấp hơn
- **FixedSize(500)**: Recall cao nhất (714 chunks), score tốt cho Q1, Q4
- **RecursiveChunker(1000)**: Cân bằng tốt nhất — score cao nhất cho Q2, Q5; số chunk vừa phải (390)

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | RecursiveChunker(1000) + OpenRouter | 8 | Giữ ngữ cảnh tốt, score cao cho query phức tạp | Chưa tối ưu cho document nhỏ |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> RecursiveChunker(1000) là lựa chọn tốt nhất vì bảo toàn ranh giới ngữ nghĩa và cung cấp đủ context. SentenceChunker có precision cao hơn ở query ngắn nhưng thua ở query phức tạp do chunk nhỏ hơn. FixedSize phù hợp nếu cần recall cao nhưng tạo nhiều chunk gây nhiễu.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `re.split(r"(?<=[.!?])\s+", text)` để tách văn bản thành các câu dựa trên dấu kết thúc câu (`.!?`) kèm khoảng trắng. Dùng positive lookbehind `(?<=...)` để giữ dấu câu trong câu gốc. Các câu được strip whitespace và lọc bỏ câu rỗng, sau đó nhóm theo `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy thử từng separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`). Mỗi bước: tách văn bản hiện tại bằng separator, merge greedy các phần thành chunk vừa ≤ chunk_size, các phần lớn hơn được đệ quy xử lý với separator tiếp theo. Base case: (1) text ≤ chunk_size → return [text], (2) hết separators → force-split theo chunk_size.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `_make_record` tạo bản ghi gồm id, content, metadata (kèm `doc_id`) và embedding từ hàm `embedding_fn`. `add_documents` lặp qua từng Document, tạo record và append vào `self._store` (in-memory) hoặc gọi `collection.add()` (ChromaDB). `search` embed query, tính dot product giữa query embedding và tất cả stored embeddings, sắp xếp giảm dần và trả về top-k.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` lọc trước (pre-filter): lọc toàn bộ `_store` theo metadata_filter (tất cả key-value phải khớp), sau đó chạy similarity search trên tập đã lọc. `delete_document` xóa tất cả bản ghi có `metadata["doc_id"] == doc_id`, trả về True nếu có ít nhất một bản ghi bị xóa.

### KnowledgeBaseAgent

**`answer`** — approach:
> Triển khai RAG pattern: (1) Gọi `store.search(question, top_k)` để lấy top-k chunks liên quan. (2) Xây dựng prompt với context từ các chunk đánh số `[Chunk 1] ... [Chunk 2] ...`. (3) Gọi `llm_fn(prompt)` để sinh câu trả lời. Prompt structure gồm context blocks, question, và nhắc "Answer:" để LLM biết cần trả lời.

### Test Results

```
============================== 42 passed in 0.57s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Python là ngôn ngữ lập trình" | "Python is a programming language" | high | -0.1162 | Không |
| 2 | "Chó là động vật trung thành" | "Mèo thích bắt chuột" | low | 0.0123 | Có |
| 3 | "AI đang thay đổi thế giới" | "Trí tuệ nhân tạo biến đổi ngành công nghiệp" | high | 0.1024 | Không |
| 4 | "Hôm nay trời đẹp" | "Cấu trúc dữ liệu và giải thuật" | low | -0.0223 | Có |
| 5 | "Vector database lưu embeddings" | "Embedding store dùng cho similarity search" | high | -0.0844 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Bất ngờ nhất: Cả 3 cặp dự đoán HIGH similarity (1, 3, 5) đều cho kết quả gần 0 hoặc âm với mock embedder. Cặp 1 ("Python" trong 2 ngôn ngữ) và cặp 3 ("AI" vs "Trí tuệ nhân tạo") lẽ ra phải có similarity >0.8 với embedder thật. Mock embedder dùng hash-based deterministic, không capture được ngữ nghĩa. **Kết luận:** Embedding quality quyết định toàn bộ chất lượng retrieval — code đúng nhưng embedder sai thì kết quả vẫn vô nghĩa. Cần LocalEmbedder hoặc OpenRouter để có similarity có ý nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm với strategy cá nhân: **RecursiveChunker(chunk_size=1000)** + **OpenRouter (`openai/text-embedding-3-small`)**.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What are the dimensions and pricing of OpenAI text-embedding-3-large per 1K tokens? | 3,072 dimensions, $0.00013 per 1K tokens |
| 2 | What is "Confabulation" according to NIST and how does it pose risks in healthcare? | Confabulation = GAI generates & confidently presents false content. In healthcare → wrong diagnoses & treatments |
| 3 | What are the main features of the Hugging Face Transformers library? | Ease of use (2 lines of code), Flexibility (PyTorch nn.Module), Simplicity (All in one file) |
| 4 | Kỹ thuật Chain-of-Thought (CoT) Prompting hoạt động như thế nào và tại sao nó giúp giảm hallucination? | CoT yêu cầu mô hình trình bày từng bước suy luận logic trước khi kết luận, giúp giảm hallucination |
| 5 | Find the AI risk management framework developed by a US government organization. List 5 main risks of Generative AI according to NIST. | NIST AI 600-1. 5 risks: CBRN, Confabulation, Dangerous Content, Data Privacy, Environmental |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | OpenAI embedding dimensions & pricing | embedding_models: "Both models support a maximum input of 8,191 tokens..." | **0.79** | Có — đúng document, gần gold answer | [LLM] từ embedding_models chunk, có context về pricing |
| 2 | NIST Confabulation & healthcare | nist: "2.2. Confabulation — a phenomenon in which GAI systems generate and confidently present erroneous or false content..." | **0.69** | Có — đúng section Confabulation | [LLM] từ NIST Confabulation section |
| 3 | Hugging Face Transformers features | nlp_co_ban: "Introduction — The 🤗 Transformers library was created to solve this problem..." | **0.54** | Có — đúng document, intro chunk | [LLM] từ HF Transformers intro |
| 4 | Chain-of-Thought prompting | prompt_engineering: "Zero-shot Prompting — Kỹ thuật này đưa thẳng yêu cầu..." | **0.62** | Có — đúng document (gần CoT section) | [LLM] từ prompt engineering doc |
| 5 | AI risk framework + 5 risks (filtered source=nist-framework) | nist: "NIST Trustworthy and Responsible AI — NIST AI 600-1..." | **0.75** | Có — đúng framework, metadata filter OK | N/A (query 5 metadata filter) |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

**Phân tích:**
- Với OpenRouter embedder (1536 dims), tất cả 5 queries đều retrieve từ đúng document trong top-1
- Score dao động 0.54–0.79, cho thấy embedding phân biệt tốt giữa các domain khác nhau
- Q2 (Confabulation) hit chính xác section "2.2. Confabulation" trong NIST document
- Q5 metadata filter (`source=nist-framework`) hoạt động chính xác, giới hạn tìm kiếm trong 275 NIST chunks
- Q4 (tiếng Việt) vẫn retrieve đúng document prompt_engineering nhờ embedder đa ngôn ngữ

### So Sánh Mock vs LocalEmbedder vs OpenRouter

| Embedder | Q1 | Q2 | Q3 | Q4 | Q5 | Đúng doc? |
|----------|----|----|----|----|----|-----------|
| Mock (hash) | NIST ✗ | NIST ✗ | NIST ✗ | NIST ✗ | NIST △ | 0/5 |
| LocalEmbedder (384d) | embedding ✓ | nist ✓ | nlp ✓ | prompt ✓ | nist ✓ | 5/5 |
| **OpenRouter (1536d)** | **embedding ✓** | **nist ✓** | **nlp ✓** | **prompt ✓** | **nist ✓** | **5/5** |

> OpenRouter có score cao hơn LocalEmbedder trên hầu hết queries (đặc biệt Q2: 0.69 vs 0.51), nhờ dimensionality cao hơn (1536 vs 384). Tuy nhiên LocalEmbedder vẫn đủ tốt cho retrieval cơ bản và không tốn API cost.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Sẽ điền sau khi thảo luận nhóm.*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Sẽ điền sau khi demo.*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> (1) Sẽ chuẩn hóa metadata schema ngay từ đầu — dùng YAML front matter thống nhất cho tất cả file trước khi bắt đầu chunking. (2) Với document quá lớn như NIST (206K chars), sẽ pre-split thành các sections riêng trước khi chunk để tăng precision. (3) Sẽ thử SentenceChunker thay vì RecursiveChunker cho các document ngắn (<5000 chars) vì SentenceChunker cho precision cao hơn ở query cụ thể (Q3). (4) Metadata filter nên được dùng cho nhiều query hơn, không chỉ Q5, để giảm không gian tìm kiếm và tăng precision.

### Failure Analysis

**Failure Case #1: Mock Embedder — Semantic Blindness**
- Query nào thất bại? Tất cả 5 queries với mock embedder — top-1 không chứa gold answer
- Tại sao? Mock embedder dùng `hash()` deterministic, không capture ngữ nghĩa. NIST document quá lớn (275 chunks) chiếm ưu thế ngẫu nhiên
- Đề xuất: Dùng LocalEmbedder hoặc OpenRouter embedder — kết quả khác biệt hoàn toàn (5/5 đúng doc)

**Failure Case #2: NIST Document Size Imbalance**
- Vấn đề: NIST (206K chars) gấp 3x genAI, gấp 80x nlp_co_ban — chunk count imbalance (275 vs 3-94)
- Đề xuất: Dùng metadata filter để giới hạn phạm vi khi biết trước document; hoặc giới hạn số chunk tối đa mỗi document

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | _ / 5 |
| **Tổng** | | **83 / 100** (chờ demo nhóm) |
