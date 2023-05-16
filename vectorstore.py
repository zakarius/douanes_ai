from chromadb.config import Settings
from chromadb.server.fastapi import FastAPI
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from chromadb.api import Where, WhereDocument, QueryResult, Collection
from chromadb.api.types import Embedding
import openai
import pandas as pd


from gpt3 import COMPLETIONS_MODEL, SEPARATOR, _compute_or_load_doc_embeddings, count_tokens, separator_len


settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory= ".chromadb_cache",
    chroma_api_impl="local",
    chroma_server_host="localhost",
    chroma_server_http_port="8000",
    chroma_server_cors_allow_origins=["*"]
)
server = FastAPI(settings)
chromadb = server._api


class BaseDouaneData():
    _api_key: str | None = None

    SUFFIX: str = ''
    BASE_COLLECTION = ""
    TEMPERATURE = 0

    pre_prompt = """AGENT0 est un douanier Togolais. Tu est un assistant basé sur GPT3 qui reppond de facon précise, concise et complete aux questions douanières en se basant uniquement sur tes connaissance en matière régimes économiques en douanes des marchandises, dans le style académique. Tu te base sur la liste des régimes et codes additionnels contenus dans SYDONIA++. Tu evites à tout prix de se repeter dans sa réponse et ne fabrique pas de reponse si la liste des régimes ne le permet pas.\n\n"""

    examples : str = ""

    data_frames_path: str 
    embeddings_path: str 
    embedding_functions: OpenAIEmbeddingFunction
    
    def df(
        self,
        data: str = BASE_COLLECTION
    ) -> pd.DataFrame:
        print(f"No DataFrame for {data} found")
        return None

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self._api_key = api_key
        self.embedding_functions = OpenAIEmbeddingFunction(api_key)

    def load_embeddings(self, data: str, _df: pd.DataFrame | None = None):
        root = f"{self.embeddings_path}{self.SUFFIX}"
        if _df is None:
            _df = self.df(data)
        return _compute_or_load_doc_embeddings(
            embeddings_path=f"{root}_{data}.json",
            df=_df,
            embedding_function=self.embedding_functions,
            value_key="content",
        )

    def collection(self, name: str) -> Collection:
        try:
            collection = chromadb.get_collection(
                name, embedding_function=self.embedding_functions,)
        except:
            collection = chromadb.create_collection(
                name=name,
                embedding_function=self.embedding_functions,
                get_or_create=True,
            )
            df = self.df(name)
            embeddings = self.load_embeddings(name, _df=df)
            collection.add(
                ids=[str(index) for index in df.index.values.tolist()],
                embeddings=[value for (_, value) in embeddings.items()],
                documents=df.content.values.tolist(),
                increment_index=True,
            )
        return collection

    def search(self,
               question: str | None = None,
               query_embeddings: Embedding | None = None,
               collection: str = BASE_COLLECTION, n_result: int = 10,
               where: Where | None = None,
               where_document: WhereDocument | None = None,
               ) -> QueryResult:
        return self.collection(collection).query(
            query_embeddings=query_embeddings,
            query_texts=question if query_embeddings is None else None,
            n_results=n_result,
            where=where,
            where_document=where_document,
        )

    def construct_prompt(self, question: str, n_result: int = 5
                         ) -> str:
        header_prefix = self.pre_prompt

        query_embedding = self.embedding_functions([question])[0]

        header = ""

        source = self.BASE_COLLECTION

        MAX_PROMPT_LEN = 2024 - \
            count_tokens(header_prefix) - \
            count_tokens("\n\n AGENT0: ""\n Reponse:")

        chosen_items = []
        chosen_item_len = 0

        query_result = self.search(
            collection=source,
            query_embeddings=query_embedding,
            n_result=n_result
        )
        best_items: list[str] = query_result["documents"][0]
        for item in best_items:
            item = item.replace("\n", " ").replace("##LINE## ", "\n")
            chosen_item_len += count_tokens(item) + separator_len()

            if chosen_item_len < MAX_PROMPT_LEN:
                try:
                    chosen_items.append(SEPARATOR + item)
                except:
                    pass

        if len(chosen_items) > 0:
            header += f"\n\n{source}".upper()
            header += "\n" + "".join(chosen_items)
        
        header+= self.examples

        print(count_tokens(header))

        return header_prefix + header + "\n\nAGENT0: " + question + "\nReponse:"


    def answer(self,
               question: str,
               show_prompt: bool = False,
               prompt_only: bool = False,
               n_result: int = 5,
               stream: bool = False,
               ):
        prompt = self.construct_prompt(
            question,
            n_result=n_result,
        )

        if show_prompt:
            print(prompt)

        if prompt_only:
            return prompt
        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model=COMPLETIONS_MODEL,
            temperature=self.TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
            stream=stream,
            max_tokens=3000 - count_tokens(prompt),
        )
        if(stream):
            return response
        else:
            return response["choices"][0]["message"]["content"]

    
