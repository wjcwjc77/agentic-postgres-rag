
import os
import argparse
import psycopg2
from openai import OpenAI
from chonkie import Pipeline

# --- Database Connection Details ---
db_host =os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# --- OpenAI API Details ---
# Make sure to set the DASHSCOPE_API_KEY environment variable
# client = OpenAI()
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL")
)


# --- Chunking Pipeline ---
pipe = (
    Pipeline()
    .chunk_with("recursive", tokenizer="gpt2", chunk_size=2048, recipe="markdown")
    .chunk_with("semantic", chunk_size=512)
)

def process_and_insert(file_path: str, table_name: str, article_name: str | None = None):
    with open(file_path, "r") as f:
        article_text = f.read()
    if not article_name:
        article_name = os.path.basename(file_path)
    doc = pipe.run(texts=article_text)

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            sslmode='require'
        )
        cur = conn.cursor()

        for chunk in doc.chunks:
            completion = client.embeddings.create(
                model="text-embedding-v4",
                input=chunk.text
            )
            embedding = completion.data[0].embedding
            sql = f"INSERT INTO {table_name} (article_name ,content, embedding) VALUES (%s,%s, %s);"
            cur.execute(sql, (article_name, chunk.text, str(embedding)))

        # Commit the transaction
        conn.commit()
        print("Data inserted successfully!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", dest="table_name", default="articles")
    parser.add_argument("--file", dest="article_file_path", default="./A-Definition-of-AGI.md")
    parser.add_argument("--name", dest="article_name", default=None)
    args = parser.parse_args()
    process_and_insert(file_path=args.article_file_path, table_name=args.table_name, article_name=args.article_name)
