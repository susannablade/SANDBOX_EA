# Digital Reflection Tarot

A Streamlit app that draws a random tarot card and generates a unique AI image based on the card's meaning and user input.

## Features

- Draw random tarot cards using the Tarot API
- Generate AI images with Hugging Face Inference API (FLUX.1-dev model)
- Secure API key management with python-dotenv

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file and add your Hugging Face API token:
   ```
   HUGGINGFACE_API_TOKEN=your_token_here
   ```
4. Run the app: `streamlit run app.py`

## APIs Used

- [Tarot API](https://github.com/ekelen/tarot-api)
- [Hugging Face Inference API](https://huggingface.co/inference-api)