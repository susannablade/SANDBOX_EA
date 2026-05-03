import streamlit as st
import requests
from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

# API Keys
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')

# Tarot API URL
TAROT_API_URL = 'https://tarot-api-3hv5.onrender.com/api/v1/cards/random'

# Hugging Face Model
HF_MODEL = 'black-forest-labs/FLUX.1-dev'

# Initialize HF client
client = InferenceClient(token=HUGGINGFACE_API_TOKEN)

def get_random_card():
    response = requests.get(TAROT_API_URL)
    if response.status_code == 200:
        data = response.json()
        card = data['cards'][0]
        return card
    else:
        st.error("Failed to fetch tarot card.")
        return None

def generate_image(prompt):
    try:
        image = client.text_to_image(prompt, model=HF_MODEL)
        return image
    except Exception as e:
        st.error(f"Failed to generate image: {e}")
        return None

# Custom CSS for purple waves and mystical feel
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #1a0033 0%, #2d0052 50%, #1a0033 100%);
            background-attachment: fixed;
        }
        .main {
            background: linear-gradient(180deg, rgba(138, 43, 226, 0.1) 0%, rgba(75, 0, 130, 0.1) 100%);
        }
        h1 {
            color: #e0b0ff;
            text-shadow: 0 0 20px rgba(138, 43, 226, 0.5);
            font-family: 'Georgia', serif;
        }
        .stTextInput > div > div > input {
            background-color: rgba(75, 0, 130, 0.2);
            color: #e0b0ff;
            border: 2px solid #8a2be2;
        }
        .stButton > button {
            background: linear-gradient(135deg, #8a2be2, #9370db);
            color: white;
            border: 2px solid #e0b0ff;
            box-shadow: 0 0 15px rgba(138, 43, 226, 0.5);
        }
        .stButton > button:hover {
            box-shadow: 0 0 25px rgba(138, 43, 226, 0.8);
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🔮 Echo Arcana")

st.write("*Draw a random tarot card and generate a unique AI image based on its meaning and your input.*")

user_input = st.text_input("Enter your reflection or browsing history summary:")

if st.button("Draw Card and Generate Image"):
    card = get_random_card()
    if card:
        st.subheader(f"Card: {card['name']}")
        st.write(f"Meaning: {card['meaning_up']}")
        
        # Combine card meaning with user input for prompt
        prompt = f"{card['name']}: {card['meaning_up']}. Reflection: {user_input}"
        
        image = generate_image(prompt)
        if image:
            st.image(image, caption="Generated AI Image")