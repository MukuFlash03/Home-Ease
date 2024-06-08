import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = str(os.getenv("GROQ_API_KEY"))
RENT_CAST_API_KEY = str(os.getenv("RENT_CAST_API_KEY"))

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

def main():
    st.title("Home Ease: Your Personalized Housing Homie!")

    user_input = st.text_input("Rental Query", "Please enter your rental query")

    if user_input:
        response = generate_response(user_input)
        st.write(response)

if __name__ == "__main__":
    main()



