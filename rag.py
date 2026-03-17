from uuid import uuid4
from pathlib import Path
from typing import Optional, List
import os
import ssl
import shutil
import tempfile
from dotenv import load_dotenv

load_dotenv()
os.environ["USER_AGENT"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from langchain_classic.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from prompt import PROMPT, EXAMPLE_PROMPT
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from chromadb.config import Settings

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def load_urls_with_selenium(urls, wait_time=10):
    """Load URLs using Selenium with explicit wait to render JS content."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,10000")
    chrome_options.add_argument("--ignore-certificate-errors")
    # Anti-detection: bypass bot protection
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=chrome_options)
    # Hide the webdriver flag from JavaScript
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": 'Object.defineProperty(navigator, "webdriver", '
                    '{get: () => undefined})'}
    )
    documents = []

    try:
        for url in urls:
            try:
                driver.get(url)
                # Wait for JS to render content
                time.sleep(wait_time)
                # Scroll to load any lazy-loaded content
                for _ in range(3):
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(2)
                # Extract all text from the rendered page
                page_text = driver.find_element("tag name", "body").text
                if page_text.strip():
                    documents.append(
                        Document(
                            page_content=page_text,
                            metadata={"source": url}
                        )
                    )
            except Exception as e:
                print(f"Error loading {url}: {e}")
    finally:
        driver.quit()

    return documents

# ---------------- CONFIG ----------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTORSTORE_DIR = Path(__file__).parent / "resources/vectorstore"
COLLECTION_NAME = "college_chatbot"

llm: Optional[ChatGroq] = None
vector_store: Optional[Chroma] = None


# ---------------- INIT ----------------
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


# ---------------- INGEST: URLs only (backwards compatible) ----------------
def process_urls(urls):
    global vector_store

    yield "Initializing components..."
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)

    initialize_components()

    yield "Loading web pages (with JS rendering, please wait ~15s per page)..."
    data = load_urls_with_selenium(urls)

    yield "Splitting text..."
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    docs = splitter.split_documents(data)

    yield "Embedding and storing documents..."
    ids = [str(uuid4()) for _ in docs]
    vector_store.add_documents(docs, ids=ids)

    yield "Done ✅ URLs processed successfully"


# ---------------- INGEST: PDFs only ----------------
def process_pdfs(pdf_paths: List[str]):
    global vector_store

    yield "Initializing components..."
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)

    initialize_components()

    yield f"Loading {len(pdf_paths)} PDF file(s)..."
    all_docs = []
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(pdf_path)
        all_docs.extend(loader.load())

    yield "Splitting text..."
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    docs = splitter.split_documents(all_docs)

    yield "Embedding and storing documents..."
    ids = [str(uuid4()) for _ in docs]
    vector_store.add_documents(docs, ids=ids)

    yield f"Done ✅ {len(pdf_paths)} PDF(s) processed successfully"


# ---------------- INGEST: URLs + PDFs (unified) ----------------
def process_all(urls: List[str] = None, pdf_paths: List[str] = None):
    global vector_store

    urls = urls or []
    pdf_paths = pdf_paths or []

    yield "Initializing components..."
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)

    initialize_components()

    all_docs = []
    url_doc_count = 0
    pdf_doc_count = 0

    # Load URLs (with JS rendering via Selenium)
    if urls:
        yield f"Loading {len(urls)} web page(s) (with JS rendering, ~15s per page)..."
        try:
            url_docs = load_urls_with_selenium(urls)
            url_doc_count = len(url_docs)
            all_docs.extend(url_docs)
            yield f"✅ Loaded {url_doc_count} document(s) from URLs"
        except Exception as e:
            yield f"⚠️ Error loading URLs: {str(e)}"

    # Load PDFs
    if pdf_paths:
        yield f"Loading {len(pdf_paths)} PDF file(s)..."
        for pdf_path in pdf_paths:
            try:
                loader = PyPDFLoader(pdf_path)
                pdf_docs = loader.load()
                pdf_doc_count += len(pdf_docs)
                all_docs.extend(pdf_docs)
            except Exception as e:
                yield f"⚠️ Error loading PDF {pdf_path}: {str(e)}"
        yield f"✅ Loaded {pdf_doc_count} page(s) from PDFs"

    if not all_docs:
        yield "❌ No documents were loaded. Check your URLs and PDFs."
        return

    yield f"Splitting {len(all_docs)} total documents..."
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    docs = splitter.split_documents(all_docs)

    yield f"Embedding and storing {len(docs)} chunks..."
    ids = [str(uuid4()) for _ in docs]
    vector_store.add_documents(docs, ids=ids)

    parts = []
    if url_doc_count > 0:
        parts.append(f"{url_doc_count} URL doc(s)")
    if pdf_doc_count > 0:
        parts.append(f"{pdf_doc_count} PDF page(s)")
    yield f"Done ✅ {' and '.join(parts)} processed into {len(docs)} chunks"


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
        "https://vistas.ac.in/school-of-engineering-technology/",
        "https://vistas.ac.in/faculty-in-school-of-engineering/",
        "https://vistas.ac.in",
    ]

    pdf_dir = Path(__file__).parent / "pdf_files"
    pdf_paths = [str(p) for p in pdf_dir.glob("*.pdf")]

    # Use unified ingestion
    for status in process_all(urls=urls, pdf_paths=pdf_paths):
        print(status)

    answer, sources = generate_answer(
        "who is the founder of vels university"
    )

    print("\nANSWER:\n", answer)
    print("\nSOURCES:\n", sources)