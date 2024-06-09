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
            listing_text = f"ID: {listing['id']}\nAddress: {listing['formattedAddress']}\nAddress Line 1: {listing['addressLine1']}\nAddress Line 2: {listing['addressLine2']}\nCity: {listing['city']}\nState: {listing['state']}\nZip Code: {listing['zipCode']}\nCounty: {listing['county']}\nLatitude: {listing['latitude']}\nLongitude: {listing['longitude']}\nProperty Type: {listing['propertyType']}\nBedrooms: {listing['bedrooms']}\nBathrooms: {listing['bathrooms']}\nSquare Footage: {listing['squareFootage']}\nLot Size: {listing['lotSize']}\nYear Built: {listing['yearBuilt']}\nStatus: {listing['status']}\nPrice: {listing['price']}\nListed Date: {listing['listedDate']}\nRemoved Date: {listing['removedDate']}\nCreated Date: {listing['createdDate']}\nLast Seen Date: {listing['lastSeenDate']}\nDays on Market: {listing['daysOnMarket']}"
            embedding_outputs = together_client.embeddings.create(
                input=listing_text,
                model=MODEL,
            )
            listing['listing_text'] = listing_text
            listing['embedding'] = embedding_outputs
            listings_collection.replace_one({'_id': listing['_id']}, listing)
    except Exception as e:
        print(f"Exception: {e}")

    print("Embeddings created and stored in MongoDB.")

def handle_query():
    user_query = st.session_state.user_query
    if user_query:  # Check if there is a query
        answer, documents = invoke_rag_chain(user_query)

        # Append both user query and bot response to the conversation
        # st.session_state.conversation.append(f"User: {user_query}")
        # st.session_state.conversation.append(f"Bot: {response}")

        # Store the RAG chain results in the session state
        st.session_state.rag_answer = answer
        st.session_state.rag_documents = documents

        # Clear the input after processing
        st.session_state.user_query = ""

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
    
        # query = st.text_input("Enter your search query:")
        user_query = st.text_input("Enter your search query:", key="user_query", on_change=lambda: handle_query())
        if user_query:
            if 'rag_answer' in st.session_state and 'rag_documents' in st.session_state:
                st.write("RAG Answer:")
                st.write(st.session_state.rag_answer)

                documents = st.session_state.rag_documents

                for result in documents:
                    with st.container():
                        st.write(f"### {result['formattedAddress']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**City:** {result['city']}")
                            st.write(f"**State:** {result['state']}")
                            st.write(f"**Zip Code:** {result['zipCode']}")
                            st.write(f"**Property Type:** {result['propertyType']}")
                            st.write(f"**Bedrooms:** {result['bedrooms']}")
                            st.write(f"**Bathrooms:** {result['bathrooms']}")
                            st.write(f"**Square Footage:** {result['squareFootage']}")
                        with col2:
                            st.write(f"**Year Built:** {result['yearBuilt']}")
                            st.write(f"**Status:** {result['status']}")
                            st.write(f"**Price:** {result['price']}")
                            st.write(f"**Listed Date:** {result['listedDate']}")
                            st.write(f"**Last Seen Date:** {result['lastSeenDate']}")
                            st.write(f"**Days on Market:** {result['daysOnMarket']}")
                        st.write("---")
if __name__ == "__main__":
    main()