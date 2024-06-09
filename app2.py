import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import together
import pymongo
from typing import List
from ragChain import invoke_rag_chain

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
TOGETHER_API_KEY = str(os.getenv("TOGETHER_API_KEY"))
together.api_key = TOGETHER_API_KEY
MODEL=str(os.getenv("MODEL"))

# Set up MongoDB connection
MONGO_DB_URI = str(os.getenv("MONGO_DB_URI"))
MONGO_DB_NAME = str(os.getenv("MONGO_DB_NAME"))
MONGO_COLLECTION_NAME = str(os.getenv("MONGO_COLLECTION_NAME"))

mongo_client = pymongo.MongoClient(MONGO_DB_URI)
db = mongo_client[MONGO_DB_NAME]
listings_collection = db[MONGO_COLLECTION_NAME]

together_client = together.Together()

def generate_response(prompt):
    client = Groq()
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192",
        temperature=0.2,
        max_tokens=1024,
        top_p=0.5,
        stop=None,
        stream=False,
    )

    return chat_completion.choices[0].message.content

def generate_embeddings():
    listings = list(listings_collection.find())

    try:
        for listing in listings:
            listing_text = ""
            for key, value in listing.items():
                if key != '_id' and key != 'embedding':  # Exclude '_id' and 'embedding' keys
                    listing_text += f"{key}: {value}\n"

            embedding_outputs = together_client.embeddings.create(
                input=listing_text,
                model=MODEL,
            )
            listing['listing_text'] = listing_text
            listing['embedding'] = [x.embedding for x in embedding_outputs.data]
            listings_collection.replace_one({'_id': listing['_id']}, listing)
    except Exception as e:
        print(f"Exception: {e}")

    print("Embeddings created and stored in MongoDB.")

def handle_query():
    user_query = st.session_state.user_query
    if user_query:  # Check if there is a query
        answer, documents = invoke_rag_chain(user_query)

        # Store the RAG chain results in the session state
        st.session_state.rag_answer = answer
        st.session_state.rag_documents = documents

        # Append both user query and bot response to the conversation
        # st.session_state.conversation.append(f"User: {user_query}")
        # st.session_state.conversation.append(f"Bot: {response}")

        # Store the RAG chain results in the session state
        st.session_state.rag_answer = answer
        st.session_state.rag_documents = documents

        # Clear the input after processing
        st.session_state.user_query = ""

    else:
        # Clear the previous results if no query is entered
        if 'rag_answer' in st.session_state:
            del st.session_state.rag_answer
        if 'rag_documents' in st.session_state:
            del st.session_state.rag_documents

def main():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["Chatbot", "Rental Listings Search"])

    if app_mode == "Chatbot":
        st.title("Housing Recommendation Chatbot")
        user_input = st.text_input("Enter your query:", "")
        if user_input:
            response = generate_response(user_input)
            st.write(response)
    
    elif app_mode == "Rental Listings Search":
        st.title("Rental Listings Search")
        if 'embedding' not in listings_collection.find_one():
            generate_embeddings()

        st.session_state.user_query = st.text_input("Enter your search query:")
        search_button = st.button("Search")

        if search_button and st.session_state.user_query:
            handle_query()
    
        if 'rag_answer' in st.session_state and 'rag_documents' in st.session_state:
            st.write("RAG Answer:")
            st.write(st.session_state.rag_answer)

            documents = st.session_state.rag_documents

            for result in documents:
                with st.container():
                    if 'formattedAddress' in result.metadata:
                        st.write(f"### {result.metadata['formattedAddress']}")

                    col1, col2 = st.columns(2)

                    with col1:
                        for key, value in result.metadata.items():
                            if key in ['city', 'state', 'zipCode', 'propertyType', 'bedrooms', 'bathrooms', 'squareFootage']:
                                st.write(f"**{key.capitalize()}:** {value}")

                    with col2:
                        for key, value in result.metadata.items():
                            if key in ['yearBuilt', 'status', 'price', 'listedDate', 'lastSeenDate', 'daysOnMarket']:
                                st.write(f"**{key.capitalize()}:** {value}")

                    st.write("---")

if __name__ == "__main__":
    main()