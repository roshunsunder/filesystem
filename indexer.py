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

class Indexer:
    """
    Class for indexing the file system.

    Constructor:
        --root: a relative (or absolute) path to the root folder that you wish to index
    
    Environment Requirement:
        --requires a .env containing OPENAI_API_KEY and HF_BEARER_TOKEN to function
    """
    def __init__(self, root: str):
        try:
            load_dotenv()
        except:
            print(".env file not found, no api functionality will be available")
        
        self.base_folder = root
        self.master_db = None
        self.sentence_embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.code_descriptions = []
        self.code_files = []
        self.regular_files = []
        self.image_files = [[],[]]
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.hf_bearer_token = os.getenv('HF_BEARER_TOKEN')
        self.image_file_types = ['.jpg', '.jpeg', '.png']
        self.code_file_types = {
            ".py": "Python source code",
            ".js": "JavaScript source code",
            ".c": "C source code",
            ".h": "C header file",
            ".java": "Java source code",
            ".cpp": "C++ source code",
            ".hpp": "C++ header file",
            ".html": "HTML file",
            ".css": "CSS file",
            ".xml": "XML file",
            ".json": "JSON file",
            ".md": "Markdown file",
            ".csv": "CSV file",
            ".xls": "Excel file",
            ".xlsx": "Excel file (modern format)",
            ".php": "PHP source code",
            ".rb": "Ruby source code",
            ".swift": "Swift source code",
            ".go": "Go source code",
            ".sql": "SQL script",
            ".pl": "Perl source code",
            ".asm": "Assembly language source code",
            ".sh": "Shell script",
            ".lua": "Lua script",
            ".r": "R script",
            ".scala": "Scala source code",
            ".kt": "Kotlin source code",
            ".cs": "C# source code",
            ".vb": "Visual Basic .NET source code",
            ".fs": "F# source code",
            ".coffee": "CoffeeScript source code",
            ".jl": "Julia source code",
            ".swift": "Swift source code",
            ".ts": "TypeScript source code",
            ".dart": "Dart source code",
            ".rs": "Rust source code",
            ".groovy": "Groovy source code",
            ".d": "D source code",
            ".hs": "Haskell source code",
            ".erl": "Erlang source code",
            ".clj": "Clojure source code",
            ".elm": "Elm source code"
        }

    
    def image_insertion(self, filename: str):
        """Generate and save VIT-GPT2 image caption + metadata for an image"""
        API_URL = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"
        headers = {"Authorization": f"Bearer {self.hf_bearer_token}"}
        def query(fname):
            with open(fname, "rb") as f:
                data = f.read()
            response = requests.post(API_URL, headers=headers, data=data)
            return response.json()
        hf_response = query(filename)[0]['generated_text']
        if os.path.splitext(filename)[1] in self.image_file_types:
            hf_response = "A picture of " + hf_response
        self.image_files[0].append(hf_response)
        self.image_files[1].append({"source" : f"{filename}"})
    
    def num_tokens_from_string(self, string: str, encoding_name: str = "cl100k_base") -> int:
        """Get the number of tokens for an input string"""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    def process_code(self, file_path: str, file_type: str):
        """Generate and save GPT-3.5-turbo's understanding of what a source code file does"""
        loader = TextLoader(file_path)
        code_doc = loader.load()
        code = "".join([i.page_content for i in code_doc])
        if self.num_tokens_from_string(code, "cl100k_base") < 5000:
            prompt = query = f"Summarize the purpose of the following code:\n```\n{code}\n```"
            messages = [{"role": "user", "content": prompt}]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0
            )
            code_doc[0].page_content = f'{file_type} {response.choices[0].message["content"]}'
            self.code_descriptions.append(code_doc[0])
    
    def _walk(self, base_folder: str):
        """Crawl the filesystem and do file-type-dependent behavior"""
        openai.api_key = self.openai_api_key
        for root, dirnames, filenames in os.walk(base_folder):
            for filename in filenames:
                extension = os.path.splitext(filename)[1]
                abs_path = f'{root}/{filename}'
                if extension == '':
                    continue
                elif extension in self.image_file_types:
                    self.image_insertion(abs_path)
                else:
                    # insert try/catch here
                    loader = TextLoader(abs_path)
                    documents = loader.load()
                    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
                    intermediate_docs = text_splitter.split_documents(documents)
                    if extension in self.code_file_types:
                        self.process_code(abs_path, self.code_file_types[extension])
                        self.code_files += intermediate_docs
                    else:
                        self.regular_files += intermediate_docs
    
    def _clear_doclists(self):
        """Resets the lists of langchain documents"""
        self.code_descriptions = []
        self.code_files = []
        self.regular_files = []
        self.image_files = [[],[]]
    
    def index(self):
        """Public driver to index the file system"""
        self._walk(self.base_folder)
    
    def render_db(self):
        """Set instance's master_db to be a FAISS database"""
        code_description_db = FAISS.from_documents(self.code_descriptions, self.sentence_embedding_function)
        code_file_db = FAISS.from_documents(self.code_files, self.sentence_embedding_function)
        master_db = FAISS.from_documents(self.regular_files, self.sentence_embedding_function)
        master_db.add_texts(texts=self.image_files[0],metadatas=self.image_files[1])
        master_db.merge_from(code_description_db)
        master_db.merge_from(code_file_db)
        self.master_db = master_db
    
    def save_db(self):
        if self.master_db != None:
            self.master_db.save_local("faiss_index")
        else:
            print("No vector store deteced")
