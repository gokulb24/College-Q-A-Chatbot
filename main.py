import streamlit as st
import tempfile
import os
from rag import process_all, generate_answer

st.title("Vels College Chatbot")

# --- Sidebar: URL inputs ---
st.sidebar.header("📎 URLs")
url1 = st.sidebar.text_input("URL 1")
url2 = st.sidebar.text_input("URL 2")
url3 = st.sidebar.text_input("URL 3")

# --- Sidebar: PDF uploads ---
st.sidebar.header("📄 PDF Files")
uploaded_pdfs = st.sidebar.file_uploader(
    "Upload PDF documents",
    type=["pdf"],
    accept_multiple_files=True
)

placeholder = st.empty()

# --- Sidebar: Process button ---
process_button = st.sidebar.button("Process Sources")

if process_button:
    urls = [url for url in (url1, url2, url3) if url.strip()]
    pdf_paths = []

    # Save uploaded PDFs to temp files
    temp_files = []
    if uploaded_pdfs:
        for pdf in uploaded_pdfs:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(pdf.read())
            tmp.close()
            pdf_paths.append(tmp.name)
            temp_files.append(tmp.name)

    if len(urls) == 0 and len(pdf_paths) == 0:
        placeholder.text("You must provide at least one URL or upload a PDF")
    else:
        try:
            for status in process_all(urls=urls, pdf_paths=pdf_paths):
                placeholder.text(status)
        except Exception as e:
            placeholder.text(f"❌ Error during processing: {str(e)}")

        # Clean up temp files
        for tmp_path in temp_files:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

query = placeholder.text_input("Enter your question")

if query:
    try:
        answer, sources = generate_answer(query)
        st.header("Answer:")
        st.write(answer)

        if sources:
            st.subheader("Sources:")
            # Deduplicate sources
            seen = set()
            for source in sources:
                if source not in seen:
                    seen.add(source)
                    st.write(source)
    except RuntimeError as e:
        placeholder.text("You must process sources first")