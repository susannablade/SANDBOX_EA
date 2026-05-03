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
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #2d0052 0%, #1a0033 50%, #3d1875 100%);
            background-attachment: fixed;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .main {
            background: transparent;
        }
        h1 {
            text-align: center;
            color: #e0b0ff;
            text-shadow: 0 0 20px rgba(138, 43, 226, 0.7), 0 0 40px rgba(138, 43, 226, 0.3);
            font-family: 'Georgia', serif;
            font-size: 3.5em;
            letter-spacing: 2px;
        }
        @keyframes wave {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
            100% { transform: translateY(0px); }
        }
        .stTextInput, .stButton {
            display: flex;
            justify-content: center;
            margin: 20px auto;
            border: 2px solid #8a2be2;
            padding: 15px;
            border-radius: 15px;
            background: linear-gradient(135deg, rgba(138, 43, 226, 0.15) 0%, rgba(75, 0, 130, 0.15) 100%);
            animation: wave 3s ease-in-out infinite;
            box-shadow: 0 0 20px rgba(138, 43, 226, 0.3), inset 0 0 20px rgba(138, 43, 226, 0.1);
        }
        .stTextInput > div > div > input {
            background-color: rgba(75, 0, 130, 0.3);
            color: #e0b0ff;
            border: 2px solid #8a2be2;
            font-size: 16px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #8a2be2, #9370db);
            color: #e0b0ff;
            border: 2px solid #e0b0ff;
            box-shadow: 0 0 15px rgba(138, 43, 226, 0.5);
            font-weight: bold;
            padding: 10px 30px;
        }
        .stButton > button:hover {
            box-shadow: 0 0 30px rgba(138, 43, 226, 0.8), 0 0 50px rgba(138, 43, 226, 0.4);
            background: linear-gradient(135deg, #9370db, #8a2be2);
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