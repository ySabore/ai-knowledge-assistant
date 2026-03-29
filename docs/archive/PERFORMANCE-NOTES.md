# Performance notes

- **RAG:** Retrieval latency scales with Pinecone query + embedding call; reduce `RAG_RETRIEVAL_LIMIT` if needed.
- **Chat:** LLM latency dominates; use smaller models for dev (`gpt-4o-mini`, local Ollama).
- **Ingestion:** Batch embeddings and Pinecone upserts in the worker (already chunked); large files increase job duration.

Profile in staging before setting SLAs.
