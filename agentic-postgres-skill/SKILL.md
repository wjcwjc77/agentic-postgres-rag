---
name: postgres-rag-skill
description: PostgreSQL RAG Data Ingestion and Retrieval Operations Tool - supports keyword search (BM25), vector search, and hybrid search
---
version: 1.0.0
author: Generated with Claude Code
tags:
  - postgresql
  - rag
  - search
  - embedding
  - bm25

# Overview
description_long: |
  This skill provides comprehensive data ingestion and retrieval functionality for PostgreSQL RAG (Retrieval-Augmented Generation) systems.
  Supports three search modes:
  - Keyword-based BM25 search
  - Vector similarity search
  - Hybrid search combining both approaches

# Requirements
requirements:
  - python >= 3.8
  - psycopg2
  - openai
  - chonkie

# Script Files
files:
  - path: scripts/insert_data.py
    description: Data ingestion script with document chunking and vector embedding capabilities
    parameters:
      - name: --table
        description: Target database table name
        required: true
        example: articles
      - name: --file
        description: Path to the document file to be ingested
        required: true
        example: ./A-Definition-of-AGI.md
      - name: --name
        description: Document name identifier for record tracking
        required: true
        example: A-Definition-of-AGI.md

  - path: scripts/hybrid_search.py
    description: Search script supporting keyword, vector, and hybrid retrieval modes
    parameters:
      - name: --table
        description: Target database table name
        required: true
        example: articles
      - name: --query
        description: Search query string
        required: true
        example: AGI quantitative definitions
      - name: --index-name
        description: BM25 index name (required for keyword and hybrid modes)
        required: false
        example: articles_content_idx
      - name: --mode
        description: Search mode type
        required: true
        options: [keyword, vector, hybrid]
        example: hybrid

  - path: scripts/delete_table.py
    description: Database table deletion utility

# Usage
usage: |
  ## Environment Initialization
  ```bash
  source .env
  source .venv/bin/activate
  ```

  ## Data Ingestion(template, table_name, file_path, article_name should be changed in practice)
  ```bash
  python scripts/insert_data.py --table articles --file ./A-Definition-of-AGI.md --name A-Definition-of-AGI.md
  ```

  ## Create Index(template, table_name and idx_name should be changed in practice)
  ```sql
  CREATE INDEX articles_embedding_idx ON articles
  USING hnsw (embedding vector_cosine_ops);

  CREATE INDEX articles_content_idx ON articles
  USING bm25(content)
  WITH (text_config='english');
  ```	

  ## Data Retrieval(template, table-name, query, index-name, mode should be changed in practice)
  ```bash
  # Keyword-based BM25 search
  python scripts/hybrid_search.py --table articles --query "AGI quantitative definitions" --index-name articles_content_idx --mode keyword

  # Vector similarity search
  python scripts/hybrid_search.py --table articles --query "AGI quantitative definitions" --mode vector

  # Hybrid search combining both approaches
  python scripts/hybrid_search.py --table articles --query "AGI quantitative definitions" --index-name articles_content_idx --mode hybrid
  ```


# Search Result Processing Guidelines
result_processing: |
  After retrieving search results from the database, synthesize and summarize the information based on the user's original query and retrieved content to provide accurate and concise responses.
  Note: Queries can be reformulated according to user-specific requirements to improve search accuracy and relevance.
