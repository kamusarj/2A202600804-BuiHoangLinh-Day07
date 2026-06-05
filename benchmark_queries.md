# Benchmark Queries & Gold Answers

## Metadata Schema

| # | File | category | language | difficulty | source |
|---|------|----------|----------|------------|--------|
| 1 | embedding_models_comparison.md | embedding | en | advanced | technical-documentation |
| 2 | genAI.md | generative-ai | en | advanced | academic-paper |
| 3 | nlp_pipeline.md | nlp | en | intermediate | huggingface-course |
| 4 | prompt_engineering_fundamentals.txt | prompt-engineering | vi | intermediate | technical-guide |
| 5 | nist_generative_ai_profile.md | ai-risk | en | advanced | nist-framework |

---

## 5 Benchmark Queries

| # | Query | Gold Answer | Chunk nào chứa thông tin? | Yêu cầu metadata? |
|---|-------|-------------|---------------------------|-------------------|
| 1 | OpenAI text-embedding-3-large có bao nhiêu chiều (dimensions) và giá bao nhiêu mỗi 1K tokens? | 3,072 dimensions, $0.00013 per 1K tokens | embedding_models_comparison.md - section "Model Specifications" và "Pricing Structure" | Không |
| 2 | Theo NIST, "Confabulation" là gì và nó gây rủi ro như thế nào trong lĩnh vực y tế? | Confabulation là hiện tượng GAI tạo ra nội dung sai lỗi nhưng được trình bày một cách tự tin (còn gọi là "hallucinations"). Trong y tế, confabulated summary có thể khiến bác sĩ chẩn đoán sai và đề xuất điều trị sai. | nist_generative_ai_profile.md - section 2.2 Confabulation | Không |
| 3 | Thư viện 🤗 Transformers có những tính năng chính nào? | 3 tính năng chính: (1) Ease of use - tải và sử dụng model chỉ trong 2 dòng code, (2) Flexibility - tất cả model là PyTorch nn.Module, (3) Simplicity - "All in one file" concept, forward pass định nghĩa trong 1 file duy nhất | nlp_pipeline.md - section Introduction | Không |
| 4 | Kỹ thuật Chain-of-Thought (CoT) Prompting hoạt động như thế nào và tại sao nó giúp giảm hallucination? | CoT yêu cầu mô hình không đưa ra kết quả ngay mà phải bóc tách và trình bày từng bước suy luận logic trước khi kết luận. Bằng cách ép mô hình "suy nghĩ từng bước một", CoT giúp giảm thiểu đáng kể hiện tượng ảo tưởng (hallucination) trong các bài toán lập luận phức tạp. | prompt_engineering_fundamentals.txt - section 2.3 | Không |
| 5 | Tìm các framework về AI risk management được phát triển bởi tổ chức chính phủ Mỹ. Liệt kê 5 rủi ro chính của Generative AI theo NIST. | Framework: NIST AI 600-1 (AI Risk Management Framework - Generative AI Profile). 5 rủi ro chính: (1) CBRN Information or Capabilities, (2) Confabulation, (3) Dangerous/Violent/Hateful Content, (4) Data Privacy, (5) Environmental Impacts | nist_generative_ai_profile.md - section 2 (Overview of Risks) | **Có** - cần filter theo source=niest hoặc category=ai-risk |

---

## Hướng dẫn sử dụng

1. **Mỗi thành viên** chạy 5 queries trên với strategy chunking riêng
2. **Ghi lại top-3 kết quả** cho mỗi query (chunk content + similarity score)
3. **So sánh** trong nhóm:
   - Strategy nào retrieve đúng chunk chứa gold answer?
   - Có query nào strategy A tốt hơn B nhưng ngược lại?
   - Metadata filtering (query 5) có giúp tăng precision không?

## Đánh giá kết quả

- **Relevant**: Top-3 có chứa chunk thật sự chứa gold answer?
- **Precision**: Score có tách được kết quả tốt và nhiễu không?
- **Chunk Coherence**: Chunk có giữ được ý trọn vẹn không?
- **Metadata Utility**: `search_with_filter()` có giúp tăng độ chính xác không?
