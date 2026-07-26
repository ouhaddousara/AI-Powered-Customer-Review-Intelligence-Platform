# AI-Powered Customer Review Intelligence Platform

End-to-end NLP + RAG pipeline for e-commerce review analysis:
ingestion, cleaning, OCR, sentiment analysis, semantic search, and
conversational Q&A with source citation.

> Personal AI Engineering project — learning by doing.
> Status: in progress (Phase 1)

## Architecture

The pipeline is made of 5 independent layers:

1. **Ingestion** — scraping, CSV, JSON, PDF
2. **Preprocessing** — text cleaning and normalization
3. **OCR** — text extraction from image reviews
4. **NLP Analysis** — sentiment and aspect extraction
5. **RAG Q&A** — vector index + conversational answers with sources

## Tech stack

Python 3.10+, Scrapy, HuggingFace Transformers, LlamaIndex, FAISS/ChromaDB,
Groq (LLaMA 3), Gradio. Full details in `docs/`.

## Repo structure

```
src/            source code, one subfolder per layer
notebooks/      exploration notebooks, one per layer
app/            Gradio interface
evaluation/     performance metrics
docs/           architecture, reports
```

## Progress

- [ ] Phase 1 — Ingestion & cleaning
- [ ] Phase 2 — OCR
- [ ] Phase 3 — PDF parsing
- [ ] Phase 4 — NLP analysis
- [ ] Phase 5 — RAG core
- [ ] Phase 6 — LLM benchmark
- [ ] Phase 7 — Gradio interface
- [ ] Phase 8 — Final evaluation

## Installation

```bash
git clone https://github.com/<your-username>/review-intel-platform.git
cd review-intel-platform
pip install -r requirements.txt
```
