import itertools
import json
import uuid
from sseclient import SSEClient
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction, EmbeddingFunction
from chromadb.api import Where, WhereDocument, QueryResult, Collection
from chromadb.api.types import Embedding
import openai
import pandas as pd
import requests
from gpt3 import COMPLETIONS_MODEL, SEPARATOR, _compute_or_load_doc_embeddings, count_tokens, separator_len
from vectorstore import chromadb
from os.path import sep


class BaseDouaneAI():
    _api_key: str | None = None
    _access_token: str | None = None

    PREFIX: str = ''
    BASE_COLLECTION = ""
    TEMPERATURE = 0

    TITLE = "Base Douanes AI"

    pre_prompt = """Tu est un assistant basé sur GPT3 qui reppond de facon précise, concise et complete aux questions douanières en se basant uniquement sur tes connaissance en matière régimes économiques en douanes des marchandises, dans le style académique. Tu te base sur la liste des régimes et codes additionnels contenus dans SYDONIA++. Tu evites à tout prix de se repeter dans sa réponse et ne fabrique pas de reponse si la liste des régimes ne le permet pas.\n\n"""

    DONNEES_FICIVES: str | None = None
    EXEMPLES_FICTIFS: str | None = None

    data_frames_path: str
    embeddings_path: str
    embedding_functions: EmbeddingFunction

    def __init__(self, data_frames_path: str = f"data{sep}",  embeddings_path: str = f"embeddings{sep}"):
        super().__init__()
        base = sep.join(__file__.split(sep)[:-3]) + sep

        self.data_frames_path = base + data_frames_path + self.PREFIX
        self.embeddings_path = base + embeddings_path + self.PREFIX
        self.DONNEES_FICIVES = "" if self.DONNEES_FICIVES is None else "DONNEES FICTIVES (JUSTE POUR DES EXEMPLES FICTIFS)" + \
            self.DONNEES_FICIVES

        self.EXEMPLES_FICTIFS = "" if self.EXEMPLES_FICTIFS is None else "EXEMPLES FICTIFS" + \
            self.EXEMPLES_FICTIFS

    def df(
        self,
        data: str = BASE_COLLECTION
    ) -> pd.DataFrame:
        print(data)
        ...

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self._api_key = api_key
        self.embedding_functions = OpenAIEmbeddingFunction(api_key)

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @access_token.setter
    def access_token(self, access_token: str):
        self._access_token = access_token

    def load_embeddings(self, data: str, _df: pd.DataFrame | None = None):
        root = self.embeddings_path
        if _df is None:
            _df = self.df(data)
        return _compute_or_load_doc_embeddings(
            embeddings_path=f"{root}_{data}.json",
            df=_df,
            embedding_function=self.embedding_functions,
            value_key="content",
        )

    def collection(self, name: str) -> Collection:
        collection_name = self.PREFIX + name
        try:
            collection = chromadb.get_collection(
                collection_name, embedding_function=self.embedding_functions,)
        except:
            collection = chromadb.create_collection(
                name=collection_name,
                embedding_function=self.embedding_functions,
                get_or_create=False,
            )
            df = self.df(name)
            embeddings = self.load_embeddings(name, _df=df)
            collection.add(
                ids=[str(index) for index in df.index.values.tolist()],
                embeddings=[value for (_, value) in embeddings.items()],
                documents=[content.replace("\n", "##LINE##")
                           for content in df.content.values.tolist()],
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
            include=["documents"],
        )

    def construct_prompt(
        self,
        question: str,
        n_result: int = 5,
        content_items: dict[str, list[str]] | None = None,
    ) -> str:
        header_prefix = self.pre_prompt + (self.DONNEES_FICIVES or "")

        query_embedding = self.embedding_functions([question])[0]

        header = ""

        source = self.BASE_COLLECTION

        MAX_PROMPT_LEN = 2024 - \
            count_tokens(header_prefix) - \
            count_tokens("\n\n Question: ""\n Reponse:")

        chosen_items = []
        chosen_item_len = 0

        if (content_items is not None) and (source in content_items.keys()):
            best_items = content_items[source]
        else:
            query_result = self.search(
                collection=source,
                query_embeddings=query_embedding,
                n_result=n_result
            )
            best_items: list[str] = query_result["documents"][0]

        for item in best_items:
            item = item.replace("\n", " ").replace("##LINE##", "\n")
            chosen_item_len += count_tokens(item) + separator_len()

            if chosen_item_len < MAX_PROMPT_LEN:
                try:
                    chosen_items.append(SEPARATOR + item)
                except:
                    pass

        if len(chosen_items) > 0:
            # header += f"\n\n{source}".upper()
            header += "\n" + "".join(chosen_items)

        header += self.EXEMPLES_FICTIFS
        return header_prefix + header + "\n\nQuestion: " + question + "\nReponse:"

    def answer(self,
               question: str,
               show_prompt: bool = False,
               prompt_only: bool = False,
               n_result: int = 5,
               stream: bool = False,
               completor: str = "open_ai",
               content_items: dict[str, list[str]] | None = None,
               use_gpt4: bool = False
               ):
        prompt = self.construct_prompt(
            question,
            n_result=n_result,
            content_items=content_items,
        )

        if show_prompt:
            print(prompt)

        if prompt_only:
            return prompt

        if (completor == "open_ai"):
            openai.api_key = self.api_key
            response = openai.ChatCompletion.create(
                model=COMPLETIONS_MODEL,
                temperature=self.TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
                stream=stream,
                max_tokens=3000 - count_tokens(prompt),
            )
            if (stream):
                return response
            else:
                return response["choices"][0]["message"]["content"]
        elif completor == "chat_gpt":
            token = self.access_token

            response = requests.post(
                "https://chat.openai.com/backend-api/conversation",
                stream=stream,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": stream and "text/event-stream" or "application/json",
                    "Content-Type": "application/json",
                },
                json={
                    "action": "next",
                    "message": [
                        {
                            "id": uuid.uuid4().hex,
                            "author": {
                                "role": "user",
                            },
                            "content": {
                                "content_type": "text",
                                "parts": [prompt],
                            },
                        },
                    ],
                    "model": "text-davinci-002-render-sha",
                    "parent_message_id": uuid.uuid4().hex,
                },
            )

            # sse_client = SSEClient(response)
            return response
            # return sse_client.events()

        elif completor == "gpt4all":
            return ""
        return ""

    def get_info(self,
                 question: str,
                 show_prompt: bool = False,
                 prompt_only: bool = False,
                 n_result: int = 5,
                 stream: bool = False,
                 completor: str = "open_ai",
                 use_gpt4: bool = False,
                 content_items: dict[str, list[str]] | None = None,
                 ):
        return self.answer(
            question=question,
            show_prompt=show_prompt,
            prompt_only=prompt_only,
            n_result=n_result,
            stream=stream,
            completor=completor,
            use_gpt4=use_gpt4,
            content_items=content_items,
        )

    async def asyncAnswer(self,
                          question: str,
                          show_prompt: bool = False,
                          prompt_only: bool = False,
                          n_result: int = 5,
                          stream: bool = False,
                          completor: str = "open_ai",
                          use_gpt4: bool = False,
                          content_items: dict[str, list[str]] | None = None,
                          ):
        return self.answer(
            question=question,
            show_prompt=show_prompt,
            prompt_only=prompt_only,
            n_result=n_result,
            stream=stream,
            completor=completor,
            use_gpt4=use_gpt4,
            content_items=content_items,
        )
