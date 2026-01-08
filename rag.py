from uuid import uuid4
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from langchain.chains import RetrievalQA
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from prompt import PROMPT, EXAMPLE_PROMPT
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate
# ---------------- CONFIG ----------------
CHUNK_SIZE = 600
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTORSTORE_DIR = Path(__file__).parent / "resources/vectorstore"
COLLECTION_NAME = "college_chatbot"

llm: Optional[ChatGroq] = None
vector_store: Optional[Chroma] = None


# ---------------- INIT ----------------
from chromadb.config import Settings

def initialize_components():
    global llm, vector_store

    if llm is None:
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=500
        )

    ef = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=ef,
        persist_directory=str(VECTORSTORE_DIR),
        client_settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
# ---------------- INGEST ----------------
import shutil

def process_urls(urls):
    global vector_store

    yield "Initializing components..."
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)

    initialize_components()

    yield "Loading web pages..."
    loader = WebBaseLoader(web_paths=urls)
    data = loader.load()

    yield "Splitting text..."
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=150
    )
    docs = splitter.split_documents(data)

    yield "Embedding and storing documents..."
    ids = [str(uuid4()) for _ in docs]
    vector_store.add_documents(docs, ids=ids)

    yield "Done ✅ URLs processed successfully"


# ---------------- QUERY ----------------
def generate_answer(query: str):
    if vector_store is None or llm is None:
        raise RuntimeError("Components not initialized")

    retriever = vector_store.as_retriever(search_kwargs={"k": 12})

    combine_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=PROMPT
    )

    rag_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=combine_chain
    )

    result = rag_chain.invoke({"input": query})

    answer = result["answer"]
    sources = [
        doc.metadata.get("source", "unknown")
        for doc in result["context"]
    ]

    return answer, sources


# ---------------- MAIN ----------------
if __name__ == "__main__":
    urls = [
        "https://vistas.ac.in/overview-2/",
        "https://vistas.ac.in/school-of-engineering-technology/"
    ]

    # IMPORTANT: exhaust the generator
    for _ in process_urls(urls):
        pass

    answer, sources = generate_answer(
        "who is the founder of vels university"
    )

    print("\nANSWER:\n", answer)
    print("\nSOURCES:\n", sources)