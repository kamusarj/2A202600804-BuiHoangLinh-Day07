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
| 1 | What are the dimensions and pricing of OpenAI text-embedding-3-large per 1K tokens? | 3,072 dimensions, $0.00013 per 1K tokens | embedding_models_comparison.md - section "Model Specifications" và "Pricing Structure" | Không |
| 2 | What is "Confabulation" according to NIST and how does it pose risks in healthcare? | Confabulation is a phenomenon where GAI systems generate and confidently present erroneous or false content (also known as "hallucinations"). In healthcare, confabulated summaries could cause doctors to make incorrect diagnoses and recommend wrong treatments. | nist_generative_ai_profile.md - section 2.2 Confabulation | Không |
| 3 | What are the main features of the 🤗 Transformers library? | 3 main features: (1) Ease of use - download, load, and use state-of-the-art NLP models in just two lines of code, (2) Flexibility - all models are simple PyTorch nn.Module classes, (3) Simplicity - "All in one file" concept, forward pass defined in a single file | nlp_pipeline.md - section Introduction | Không |
| 4 | Kỹ thuật Chain-of-Thought (CoT) Prompting hoạt động như thế nào và tại sao nó giúp giảm hallucination? | CoT yêu cầu mô hình không đưa ra kết quả ngay mà phải bóc tách và trình bày từng bước suy luận logic trước khi kết luận. Bằng cách ép mô hình "suy nghĩ từng bước một", CoT giúp giảm thiểu đáng kể hiện tượng ảo tưởng (hallucination) trong các bài toán lập luận phức tạp. | prompt_engineering_fundamentals.txt - section 2.3 | Không |
| 5 | Find the AI risk management framework developed by a US government organization. List 5 main risks of Generative AI according to NIST. | Framework: NIST AI 600-1 (AI Risk Management Framework - Generative AI Profile). 5 main risks: (1) CBRN Information or Capabilities, (2) Confabulation, (3) Dangerous/Violent/Hateful Content, (4) Data Privacy, (5) Environmental Impacts | nist_generative_ai_profile.md - section 2 (Overview of Risks) | **Có** - cần filter theo source=niest hoặc category=ai-risk |

---

## Hướng dẫn sử dụng

1. **Mỗi thành viên** chạy 5 queries trên với strategy chunking riêng
2. **Ghi lại top-3 kết quả** cho mỗi query (chunk content + similarity score)
3. **So sánh** trong nhóm:
   - Strategy nào retrieve đúng chunk chứa gold answer?
   - Có query nào strategy A tốt hơn B nhưng ngược lại ở query khác?
   - Metadata filtering có giúp ích không?

## Đánh giá kết quả

- **Relevant**: Top-3 có chứa chunk thật sự liên quan không?
- **Precision**: Score có tách được kết quả tốt và nhiễu không?
- **Chunk Coherence**: Chunk có giữ được ý trọn vẹn không?
- **Metadata Utility**: `search_with_filter()` có giúp tăng độ chính xác không?
- **Grounding Quality**: Câu trả lời của agent có thật sự dựa trên retrieved context không?
