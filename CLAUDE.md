## 环境初始化
1. 执行以下命令，加载环境变量：
   ```bash
   source .env
   ```
2. 激活 Python 虚拟环境：
   ```bash
   source .venv/bin/activate
   ```
  

## 数据入库（insert_data.py）
向数据库中插入数据时必须调用以下脚本
使用 `insert_data.py` 向数据库插入数据，需传入表名、文件路径、文件名。

- 参数说明：
  | 参数           | 作用           | 是否必填 | 示例                          |
  |:--------------|:---------------|:-------|:-----------------------------|
  | --table       | 目标表名       | 是     | articles                     |
  | --file        | 文件路径       | 是     | ./A-Definition-of-AGI.md     |
  | --name        | 文件名（记录） | 是     | A-Definition-of-AGI.md       |

- 示例命令：
  ```bash
  python insert_data.py --table articles --file ./A-Definition-of-AGI.md --name A-Definition-of-AGI.md
  ```

---
## 创建索引（示例）
```sql
CREATE INDEX articles_embedding_idx ON articles
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX articles_content_idx ON articles
USING bm25(content)
WITH (text_config='english');
```

## 数据检索（hybrid_search.py）
使用 `hybrid_search.py` 检索数据库内容，支持三种检索模式，需提供表名、查询内容及索引名（部分模式需要）。

- 参数说明：
  | 参数              | 作用              | 必填   | 示例                       |
  |:------------------|:------------------|:------|:--------------------------|
  | --table           | 目标表名          | 是    | articles                  |
  | --query           | 查询关键词        | 是    | AGI如何量化定义            |
  | --index-name      | BM25索引名        | 可选  | articles_content_idx       |
  | --mode            | 检索模式          | 是    | keyword/vector/hybrid      |

- 检索模式：
  - keyword：仅关键词BM25排序（需 --index-name 参数）
  - vector：仅向量排序
  - hybrid：混合排序（需 --index-name 参数）

- 示例命令：
  - 关键词排序：
    ```bash
    python hybrid_search.py --table articles --query "AGI如何量化定义" --index-name articles_content_idx --mode keyword
    ```
  - 向量排序：
    ```bash
    python hybrid_search.py --table articles --query "AGI如何量化定义" --mode vector
    ```
  - 混合排序：
    ```bash
    python hybrid_search.py --table articles --query "AGI如何量化定义" --index-name articles_content_idx --mode hybrid
    ```

> 注意：可根据用户具体问题适当改写 query 以提升检索准确率。

---

## 查询结果生成建议
得到数据库检索结果后，请结合用户原始提问与结果内容，进行归纳总结并输出精准、简洁的答复。