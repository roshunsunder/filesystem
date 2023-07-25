import requests
import os
import tiktoken
import openai
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv


class QueryDriver:
    def __init__(self, embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2"), optimizations = False):
        self.embedding_model = embedding_model
        self.master_db = None
        self.llm_optimizations = optimizations
    
    def load_from_memory(self, db_name):
        """Useful for instantiating QD's instance of FAISS vector store if it's already in memory"""
        self.master_db = db_name
    
    def load_from_disk(self, path: str):
        """Instantiate QD's instance of FAISS vectore store if written to persisten storage"""
        self.master_db = FAISS.load_local(path, self.embedding_model)
    
    def _search_database_vanilla(self, query: str, n_results=5):
        """Regular retrieval from vector DB"""
        if self.master_db == None:
            print("Vector store not loaded. Query class needs vector store to be loaded first")
            return
        res = []
        for document in self.master_db.similarity_search(query=query, k=n_results):
            if document.metadata['source'] not in res:
                res.append(document.metadata['source'])
        return res
    
    def _search_database_image(self, query: str):
        prompt = f"""
        This is a query for a database of image captions. Generalize the query \
        so it is more applicable to pictures that it might be similar to. For example:

        Query: Jack and Jill posing for a honeymoon picture in the Bahamas.
        Generalized: A man and a woman standing on a beach.
        Query: {query}
        Generalized:"""

        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0, # this is the degree of randomness of the model's output
        )

        res = self._search_database_vanilla(f'{query}, which is {response.choices[0].message["content"]}', n_results=3)
        regular_retrieval = self._search_database_vanilla(query=query, n_results=2)
        for f in regular_retrieval:
            if f not in res:
                res.append(f)
        return res
    
    def _get_branch_likely(self,query):
        msg = f"""If the following query is looking for an image, output the word Image. \
        If you are not sure or do not think the query is looking for an image, output\
        the word Other.

        Query: {query}.
        Output: """
        messages = [{"role": "user", "content": msg}]
        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0
        )
        return response.choices[0].message["content"]
    
    def _guided_database_search(self, search_string: str):
        """Use LLM optimized searching"""
        branch_likely = self._get_branch_likely(search_string)
        if "Image" in branch_likely:
            return self._search_database_image(search_string)
        else:
            return self._search_database_vanilla(search_string)

    def query(self, search_string: str):
        if not self.llm_optimizations:
            return self._search_database_vanilla(search_string)
        else:
            return self._guided_database_search(search_string)

