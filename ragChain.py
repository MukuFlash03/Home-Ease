import os
from dotenv import load_dotenv
import pymongo
import openai
import pprint
import streamlit as st

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from groq import Groq
from langchain_groq import ChatGroq
from langchain_together.embeddings import TogetherEmbeddings

load_dotenv(override=True)

# Initialize OpenAI
GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))

# MongoDB setup
MONGO_DB_URI = str(os.getenv("MONGO_DB_URI"))
MONGO_DB_NAME = str(os.getenv("MONGO_DB_NAME"))
MONGO_COLLECTION_NAME = str(os.getenv("MONGO_COLLECTION_NAME"))
ATLAS_VECTOR_SEARCH_INDEX_NAME=str(os.getenv("ATLAS_VECTOR_SEARCH_INDEX_NAME"))

mongo = pymongo.MongoClient(MONGO_DB_URI)
db = mongo[MONGO_DB_NAME]
atlas_collection = db[MONGO_COLLECTION_NAME]
vector_search_index = "vector_index"

rag_chain: any
retriever: any


def create_vector_store():
    embeddings = TogetherEmbeddings(model="togethercomputer/m2-bert-80M-8k-retrieval")

    # Vector Store Creation
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string = MONGO_DB_URI,
        namespace = MONGO_DB_NAME + "." + MONGO_COLLECTION_NAME,
        embedding = embeddings,
        index_name = ATLAS_VECTOR_SEARCH_INDEX_NAME,
        text_key="listing_text"
    )

    return vector_store

def query_vector_store(vector_store, query):
    results = vector_store.similarity_search(query)
    # pprint.pprint(results)

def build_rag_chain(vector_store):
    # Instantiate Atlas Vector Search as a retriever
    retriever = vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": 5}
    )

    # Define a prompt template
    template = """

    Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    {context}

    Question: {question}
    """
    custom_rag_prompt = PromptTemplate.from_template(template)

    llm = ChatGroq(api_key=GROQ_API_KEY, temperature=0.2, model="llama3-8b-8192")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    retrieve = { "context": retriever | format_docs, "question": RunnablePassthrough()}

    # Construct a chain to answer questions on your data
    rag_chain = (
        retrieve
        | custom_rag_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain, retriever

def query_rag_chain(rag_chain, retriever, question):
    # Prompt the chain
    answer = rag_chain.invoke(question)

    print("Question: " + question)
    print("Answer: " + answer)

    # Return source documents
    # documents = retriever.get_relevant_documents(question)
    documents = retriever.invoke({"question": question})
    # print("\nSource documents:")
    # pprint.pprint(documents)
    return answer, documents

def invoke_rag_chain(query):
    vector_store = create_vector_store()
    print("Vector store created.")
    
    query_vector_store(vector_store, query)
    print("Vector store queried.")
    
    rag_chain, retriever = build_rag_chain(vector_store)
    print("RAG chain and retriever built.")
    
    print("User query:", query)
    answer, documents = query_rag_chain(rag_chain, retriever, query)
    print("RAG chain queried.")
    
    print("Retrieved documents:", documents)
    return answer, documents
