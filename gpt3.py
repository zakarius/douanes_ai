import pandas as pd
import tiktoken
import numpy as np
from chromadb.api.types import EmbeddingFunction


COMPLETIONS_MODEL = "gpt-3.5-turbo"  # "text-davinci-003"
EMBEDDINGS_MODEL = "text-embedding-ada-002"
ENCODING_MODEL = "gpt-3.5-turbo"
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
MAX_SECTION_LEN = 500
SEPARATOR = "\n\n* "

COMPLETIONS_API_PARAMS = {
    "model": COMPLETIONS_MODEL,
    "max_tokens": MAX_SECTION_LEN,
    "temperature": 0.3,
}


def count_tokens(text: str) -> int:
    return len(encoding.encode(str(text)))


def separator_len():
    return count_tokens(SEPARATOR)


def load_embeddings(df: pd.DataFrame, exclude_columns: list[str] = ["content"]):
    
    max_dim = max([int(c) for c in df.columns if c !=
                  "Unnamed: 0" and c not in exclude_columns])
    try:
        return {
            idx: [row[str(i)] for i in range(max_dim + 1)] for idx, row in df.iterrows()
        }
    except :
        return  {
            idx: [  row[i] for i in range(max_dim + 1)] for idx, row in df.iterrows()
        }

def compute_doc_embeddings(df: pd.DataFrame,embedding_function: EmbeddingFunction, value_key: str = "content"):
    return {
      idx:  embedding_function([r[value_key]])[0]  for idx, r in df.iterrows()
    }

def _compute_or_load_doc_embeddings(embeddings_path: str, df: pd.DataFrame, embedding_function: EmbeddingFunction, value_key: str = "content"):
    assert embeddings_path.endswith(".json")
    try:
        embeddings_df = pd.read_json(embeddings_path, orient='index')
        print(f"Loaded {len(embeddings_df)} embeddings from {embeddings_path}")
        return load_embeddings(embeddings_df)
    except:
        embeddings = compute_doc_embeddings(df, embedding_function, value_key)
        embeddings_df = pd.DataFrame.from_dict(embeddings, orient='index')
        embeddings_df.to_json(embeddings_path, orient='index')
        print(f"Saved {len(embeddings_df)} embeddings to {embeddings_path}")
        return embeddings


def compute_or_load_embeddings(df_name: str, value_key: str = "content") -> dict[tuple[str, str], list[float]]:
    _df = pd.read_json(f'{df_name}.json', orient='index')
    print(f"Computing or loading {df_name} embeddings")
    _embeddings_path = f'{df_name}_embeddings.json'
    embeddings = _compute_or_load_doc_embeddings(
        embeddings_path=_embeddings_path, df=_df, value_key=value_key)
    return embeddings


def vector_similarity(x,  y) -> float:
    return np.dot(np.array(x), np.array(y))


def order_embeddings_similarity(query_embedding: list[float], contexts: dict[(str, str), np.array]) -> list[(float, (str, str))]:
    embedding_similarities = sorted([
        (vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in contexts.items()
    ], reverse=True)

    return embedding_similarities
