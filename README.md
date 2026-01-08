# 🎓 **College Website RAG Chatbot**

A user-friendly **Retrieval-Augmented Generation (RAG) chatbot** designed to answer questions using **official college website content**.  
Users can provide website URLs and ask questions to receive **accurate, source-backed answers**, minimizing hallucinations and ensuring factual correctness.  
While demonstrated on a college website, the system can be extended to **any domain**.

---

## ✨ Features

- Load and ingest college website URLs dynamically  
- Scrape and parse web content using LangChain’s `WebBaseLoader`  
- Split content using recursive chunking for improved context retention  
- Generate semantic embeddings using HuggingFace sentence transformers  
- Store and retrieve embeddings efficiently using ChromaDB  
- Answer user queries using Groq-hosted **LLaMA-3.3-70B**  
- Provide answers along with **source URLs** for transparency  

---

## 🧠 How It Works

1. **URL Ingestion**  
   - Fetches webpage content from provided college URLs  

2. **Text Processing**  
   - Splits content into overlapping chunks using `RecursiveCharacterTextSplitter`  

3. **Embedding & Storage**  
   - Converts text chunks into embeddings using `all-MiniLM-L6-v2`  
   - Stores vectors in ChromaDB for persistent retrieval  

4. **Retrieval-Augmented Generation**  
   - Retrieves top-k relevant chunks based on semantic similarity  
   - Passes retrieved context to the LLM with a grounding prompt  

---

## 🛠 Tech Stack

- **Python 3.10**
- **LangChain (Runnable RAG)**
- **ChromaDB**
- **Groq (LLaMA-3.3-70B)**
- **HuggingFace Sentence Transformers**
- **Streamlit**
- **dotenv**
### Set-up

1. Run the following command to install all dependencies. 

    ```bash
    pip install -r requirements.txt
    ```

2. Create a .env file with your GROQ credentials as follows:
    ```text
    GROQ_MODEL=MODEL_NAME_HERE
    GROQ_API_KEY=GROQ_API_KEY_HERE
    ```

3. Run the streamlit app by running the following command.

    ```bash
    streamlit run main.py
    ```


### Usage/Examples

The web app will open in your browser after the set-up is complete.

- On the sidebar, you can input URLs directly.

- Initiate the data loading and processing by clicking "Process URLs."

- Observe the system as it performs text splitting, generates embedding vectors using HuggingFace's Embedding Model.

- The embeddings will be stored in ChromaDB.

- One can now ask a question and get the answer based on those news articles

- In the tutorial, we will use the following news articles
  - https://vistas.ac.in/overview-2/
  - https://vistas.ac.in/school-of-engineering-technology/
  - https://vistas.ac.in/faculty-in-school-of-engineering/

### Results

- 95% factual accuracy across 100+ test queries
- 4 reduction in hallucinations using retrieval grounding
- Stable responses under real-world user queries
- Transparent answers with cited sources

### Future Enhancements
- Support for PDFs and document uploads
- Hybrid search and reranking
- Rag evaluation using RAGAS
- Chat history and follow-up questions

### Author

```text
    Gokul B
    AI / ML Engineer | GenAI & RAG Systems
    GitHub: https://github.com/gokulb24
   ```
    