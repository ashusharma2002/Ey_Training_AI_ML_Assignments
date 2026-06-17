from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

from langchain_groq import ChatGroq

load_dotenv()


def create_pdf_qa(pdf_path):

    print("\nLoading PDF...")

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    print(f"Pages Loaded : {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = splitter.split_documents(docs)

    print(f"Chunks Created : {len(split_docs)}")

    embeddings = FakeEmbeddings(size=768)

    vector_db = FAISS.from_documents(
        split_docs,
        embeddings
    )

    retriever = vector_db.as_retriever()

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )

    return retriever, llm