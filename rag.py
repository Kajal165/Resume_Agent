# os module import kar rahe hain, environment variables aur file paths
# ke saath kaam karne ke liye
import os

# lru_cache import kar rahe hain, taaki loaded embedding model
# ko baar-baar initialize na karna pade
from functools import lru_cache

# .env file se API key aur configuration load karne ke liye
from dotenv import load_dotenv

# Groq ke LLM ko use karne ke liye ChatGroq import kar rahe hain
from langchain_groq import ChatGroq

# Hugging Face embedding model ko use karne ke liye
from langchain_huggingface import HuggingFaceEmbeddings

# Hugging Face se model ki local cached files ka path check karne ke liye
from huggingface_hub import snapshot_download

# Jab model local cache mein nahi milta, tab aane wali error ko handle karne ke liye
from huggingface_hub.errors import LocalEntryNotFoundError

# FAISS vector database import kar rahe hain,
# jo document embeddings ko store aur search karta hai
from langchain_community.vectorstores import FAISS

# PDF aur TXT files ko read karne ke liye document loaders
from langchain_community.document_loaders import (
    PyPDFLoader,  # PDF file read karne ke liye
    TextLoader   # TXT file read karne ke liye
)

# Bade documents ko chhote text chunks mein divide karne ke liye
from langchain_text_splitters import RecursiveCharacterTextSplitter


# .env file ki values ko environment mein load kar rahe hain
load_dotenv()

# .env file se Groq API key read kar rahe hain
groq_api_key = st.secret("GROQ_API_KEY")

# Check kar rahe hain ki API key available hai ya nahi
if not groq_api_key:
    # API key missing hone par error show hoga
    raise ValueError("GROQ_API_KEY is missing from your .env file")


# Groq LLM initialize kar rahe hain
llm = ChatGroq(
    model=st.secrets["LLM_MODEL"],  # Kaunsa language model use hoga
    api_key=st.secrets["GROQ_API_KEY"],         # API key se Groq ko authenticate karenge
    temperature=0                 # 0 rakhne se answers comparatively consistent hote hain
)


# Hugging Face embedding model ka naam store kar rahe hain
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# Is function ka result cache hoga,
# taaki ek hi Python process mein model baar-baar load na ho
@lru_cache(maxsize=1)
def load_embedding_model():

    # Try block mein pehle local cache check karenge
    try:

        # Internet se download kiye bina local cache check kar rahe hain
        model_path = snapshot_download(
            repo_id=MODEL_NAME,       # Hugging Face model ka naam
            local_files_only=True     # Sirf local files use karo
        )

        # Model local cache mein mil gaya
        print("Using the existing local embedding model.")

    # Agar local cache mein model nahi mila, toh ye error handle hogi
    except LocalEntryNotFoundError:

        # Message show kar rahe hain ki model download karna padega
        print("Embedding model not found locally. Downloading now...")

        # Model ko Hugging Face se download kar rahe hain
        model_path = snapshot_download(
            repo_id=MODEL_NAME
        )

    # Local model files ke path se embedding model initialize kar rahe hain
    return HuggingFaceEmbeddings(
        model_name=model_path
    )


# PDF aur TXT documents ko load karne ke liye function
def load_documents(file_path):

    # File extension nikal rahe hain, jaise .pdf ya .txt
    # lower() se extension lowercase mein ho jayegi
    file_extension = os.path.splitext(file_path)[1].lower()

    # Agar file PDF hai, toh PDF loader use karo
    if file_extension == ".pdf":
        loader = PyPDFLoader(file_path)

    # Agar file TXT hai, toh text loader use karo
    elif file_extension == ".txt":
        loader = TextLoader(
            file_path,          # TXT file ka path
            encoding="utf-8"    # Text ko UTF-8 encoding se read karo
        )

    # Agar file PDF ya TXT nahi hai, toh error show karo
    else:
        raise ValueError(
            "Only PDF and TXT files are supported."
        )

    # File ka content read karke return karo
    return loader.load()


# Documents ko chhote chunks mein divide karne ka function
def split_documents(documents):

    # Text splitter initialize kar rahe hain
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Har chunk mein maximum 1000 characters
        chunk_overlap=200     # Agle chunk mein pichhle chunk ke 200 characters repeat honge
    )

    # Documents ko split karke chunks return karo
    return text_splitter.split_documents(documents)


# Document chunks ko FAISS vector database mein store karne ka function
def create_vector_store(chunks):

    # Embedding model load karo
    # Agar model cache mein hai, toh dobara download nahi hoga
    embeddings = load_embedding_model()

    # Har chunk ka embedding banakar FAISS mein store karo
    vector_store = FAISS.from_documents(
        documents=chunks,       # Store karne wale text chunks
        embedding=embeddings    # Text ko vectors mein convert karne wala model
    )

    # Bana hua FAISS vector store return karo
    return vector_store


# User ke question ke liye relevant document chunks search karne ka function
def get_relevant_documents(vector_store, question):

    # FAISS se search karne ke liye retriever bana rahe hain
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3}   # Sabse relevant 3 chunks retrieve karo
    )

    # Question ke according relevant chunks search karke return karo
    return retriever.invoke(question)


# Retrieved documents ke basis par answer generate karne ka function
def get_answer(vector_store, question):

    # User ke question se related document chunks retrieve karo
    documents = get_relevant_documents(
        vector_store,  # FAISS vector database
        question       # User ka question
    )

    # Retrieved chunks ka text combine karke ek context banao
    context = "\n\n".join(
        document.page_content  # Har chunk ka actual text
        for document in documents
    )

    # LLM ko instructions, document context aur question de rahe hain
    prompt = f"""
You are a helpful AI assistant.

Follow these rules:
1. First, use the provided document context if it contains
   information relevant to the user's question.
2. If the answer is missing from the context, use your
   general knowledge to answer the question.
3. If the question is unrelated to the document, answer it
   normally using your general knowledge.
4. Never claim that information came from the document
   if it was not present in the context.
5. If you are unsure, clearly state the uncertainty.
6. Answer in clear, simple language.

Document context:
{context}

User question:
{question}

Answer:
"""

    # Prompt Groq LLM ko bhejo aur response receive karo
    response = llm.invoke(prompt)

    # Sirf answer ka text return karo
    return response.content


# FAISS vector store mein saved document chunks dekhne ka function
def show_embedded_files(vector_store):

    # FAISS ke document store se saare saved chunks ki list banao
    documents = list(
        vector_store.docstore._dict.values()
    )

    # Total kitne chunks store hue hain, woh print karo
    print(f"Total embedded chunks: {len(documents)}")

    # Har chunk ko number ke saath ek-ek karke display karo
    for index, document in enumerate(documents, start=1):

        # Chunk ka number print karo
        print(f"\n--- Chunk {index} ---")

        # Source file ka naam ya path print karo
        print(
            "Source:",
            document.metadata.get("source", "Unknown")
        )

        # Chunk ke pehle 300 characters print karo
        print("Content:", document.page_content[:300])
