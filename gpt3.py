import pandas as pd
import openai
import tiktoken
import numpy as np


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


def load_embeddings(df: pd.DataFrame, exclude_columns: list[str] = ["content"]) -> dict[tuple[str, str], list[float]]:
    max_dim = max([int(c) for c in df.columns if c !=
                  "Unnamed: 0" and c not in exclude_columns])
    return {
        idx: [r[str(i)] for i in range(max_dim + 1)] for idx, r in df.iterrows()
    }


def get_embedding(text: str, api_key: str, model: str = EMBEDDINGS_MODEL) -> list[float]:
    openai.api_key = api_key
    return openai.Embedding.create(
        model=model,
        input=text
    )


def get_doc_embedding(text: str, api_key: str) -> list[float]:
    return get_embedding(text, api_key)


def get_query_embedding(text: str, api_key: str) -> list[float]:
    return get_doc_embedding(text, api_key)


def compute_doc_embeddings(df: pd.DataFrame, api_key: str, value_key: str = "content") -> dict[tuple[str, str], list[float]]:
    embeddings = {}
    for idx, r in df.iterrows():
        try:
            content = r[value_key].replace("\n", " ")
            embeddings[idx] = get_doc_embedding(content, api_key)
        except:
            print(f"Error computing embedding for {idx} : {r.values}")
            try:
                content = r[value_key].replace("\n", " ")
                embeddings[idx] = get_doc_embedding(content, api_key)

            except:
                print(
                    f"Error computing embedding for {idx} : {r.values} for the second time")
                pass
            pass
    return embeddings


def _compute_or_load_doc_embeddings(embeddings_path: str, df: pd.DataFrame, api_key: str, value_key: str = "content") -> dict[tuple[str, str], list[float]]:
    assert embeddings_path.endswith(".json")

    try:
        embeddings_df = pd.read_json(embeddings_path, orient='index')
        print(f"Loaded {len(embeddings_df)} embeddings from {embeddings_path}")
        return load_embeddings(embeddings_df)
    except:
        embeddings = compute_doc_embeddings(df, api_key, value_key)
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
