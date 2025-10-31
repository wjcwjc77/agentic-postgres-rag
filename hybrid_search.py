import os
import argparse

import psycopg2
from openai import OpenAI

# --- Database Connection Details ---
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# --- OpenAI API Details ---
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL"),
)


def get_query_embedding(query):
    """
    Gets the embedding for the query.
    """
    completion = client.embeddings.create(model="text-embedding-v4", input=query)
    return completion.data[0].embedding


def hybrid_search(query, query_embedding, table_name: str, content_index_name: str, mode: str):
    """
    Performs search with one of three modes:
    - keyword: BM25 only
    - vector: vector similarity only
    - hybrid: combine BM25 and vector
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            sslmode="require",
        )
        cur = conn.cursor()

        if mode == "vector":
            sql = f"""
            SELECT id,
                   content,
                   (1.0 / (60 + ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector))) AS score
            FROM {table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT 10;
            """
            cur.execute(sql, (str(query_embedding), str(query_embedding)))
        elif mode == "keyword":
            sql = f"""
            SELECT id,
                   content,
                   (1.0 / (60 + ROW_NUMBER() OVER (ORDER BY content <@> to_bm25query(%s, '{content_index_name}')))) AS score
            FROM {table_name}
            ORDER BY content <@> to_bm25query(%s, '{content_index_name}')
            LIMIT 10;
            """
            cur.execute(sql, (query, query))
        else:  # hybrid
            sql = f"""
            WITH vector_search AS (
                SELECT id,
                       content,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS rank
                FROM {table_name}
                ORDER BY embedding <=> %s::vector
                LIMIT 20
            ),  
            keyword_search AS (
                SELECT id,
                       content,
                       ROW_NUMBER() OVER (ORDER BY content <@> to_bm25query(%s, '{content_index_name}')) AS rank
                FROM {table_name}
                ORDER BY content <@> to_bm25query(%s, '{content_index_name}')
                LIMIT 20
            )
            SELECT
                COALESCE(v.id, k.id) as id,
                COALESCE(v.content, k.content) as content,
                COALESCE(1.0 / (60 + v.rank), 0.0) + COALESCE(1.0 / (60 + k.rank), 0.0) AS combined_score
            FROM {table_name} d
            LEFT JOIN vector_search v ON d.id = v.id
            LEFT JOIN keyword_search k ON d.id = k.id
            WHERE v.id IS NOT NULL OR k.id IS NOT NULL
            ORDER BY combined_score DESC
            LIMIT 10;
            """
            cur.execute(sql, (str(query_embedding), str(query_embedding), query, query))
        results = cur.fetchall()

        for row in results:
            print(f"ID: {row[0]}\nContent: {row[1]}\nScore: {row[2]}\n---")

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", dest="table_name", default="articles")
    parser.add_argument("--query", dest="search_query", default="如何量化定义AGI")
    parser.add_argument("--index-name", dest="content_index_name", default="articles_content_idx")
    parser.add_argument("--mode", dest="mode", choices=["keyword", "vector", "hybrid"], default="hybrid")
    args = parser.parse_args()

    embedding = None
    if args.mode in ("vector", "hybrid"):
        embedding = get_query_embedding(args.search_query)

    hybrid_search(args.search_query, embedding, args.table_name, args.content_index_name, args.mode)
