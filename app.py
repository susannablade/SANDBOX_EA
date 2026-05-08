import os
import random
from io import BytesIO

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from google import genai



# ---------------------------
# LOAD ENV
# ---------------------------
load_dotenv()

# ---------------------------
# CONFIG
# ---------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

TAROT_API_URL = (
    "https://tarot-api-3hv5.onrender.com/api/v1/cards/random"
)

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(
    page_title="Echo Arcana",
    page_icon="🔮",
    layout="centered"
)

# ---------------------------
# SESSION STATE
# ---------------------------
if "recent_cards" not in st.session_state:
    st.session_state.recent_cards = []

# ---------------------------
# TAROT FUNCTIONS
# ---------------------------
def get_random_cards(n=3):
    """
    Pull random tarot cards from API.
    """

    cards = []

    try:
        for _ in range(n):

            response = requests.get(
                TAROT_API_URL,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if "cards" in data:
                cards.append(data["cards"][0])

        return cards

    except Exception as e:
        st.error(f"Tarot Error: {e}")
        return []


def filter_recent(cards, recent_cards):
    """
    Prevent recent repeats.
    """

    filtered = [
        card for card in cards
        if card["name"] not in recent_cards
    ]

    return filtered if filtered else cards


def choose_card(cards, user_input):
    """
    Use Gemini to select the most relevant card.
    """

    card_names = [card["name"] for card in cards]

    prompt = f"""
You are selecting the most symbolically appropriate tarot card.

USER SEARCHES:
{user_input}

AVAILABLE CARDS:
{card_names}

RULES:
- Choose ONE card from the list
- Favor symbolic resonance
- If the searches are chaotic or vague, choose intuitively
- Output ONLY the card name
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        chosen_name = response.text.strip()

        for card in cards:
            if card["name"].lower() == chosen_name.lower():
                return card

    except Exception as e:
        st.error(f"Card Selection Error: {e}")

    return random.choice(cards)


# ---------------------------
# IMAGE GENERATION
# ---------------------------
def generate_oracle_image(card, meaning, user_input):
    """
    Generate surreal oracle imagery.
    """

    prompt = f"""
Create a surreal symbolic oracle image.

The image should feel:
- mystical
- dreamlike
- psychologically symbolic
- cinematic
- emotionally charged
- painterly
- strange but beautiful

USER SEARCHES:
{user_input}

TAROT CARD:
{card}

CARD MEANING:
{meaning}

STYLE INSPIRATION:
- occult symbolism
- surrealism
- prophetic visions
- ancient mythology
- alchemy
- forgotten dreams
- soft dramatic lighting

IMPORTANT:
- no text
- no typography
- no modern graphic design
- highly detailed composition
- cohesive color palette
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=prompt
        )

        for part in response.candidates[0].content.parts:

            if part.inline_data is not None:

                image = Image.open(
                    BytesIO(part.inline_data.data)
                )

                return image

    except Exception as e:
        st.error(f"Image Generation Error: {e}")

    return None


# ---------------------------
# INTERPRETATION
# ---------------------------
def generate_interpretation(card, meaning, user_input):
    """
    Generate oracle interpretation.
    """

    prompt = f"""
You are an oracle interpreting symbolic patterns.

USER SEARCHES:
{user_input}

TAROT CARD:
{card}

CARD MEANING:
{meaning}

TASK:
Interpret the emotional and symbolic connection between
the searches and the tarot archetype.

STYLE:
- poetic
- psychologically insightful
- mystical but readable
- concise
- thoughtful
- slightly uncanny

RULES:
- 3 to 5 sentences
- avoid generic spirituality
- do not sound like a horoscope
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        st.error(f"Interpretation Error: {e}")
        return meaning


# ---------------------------
# UI
# ---------------------------
st.title("Echo Arcana")
st.caption(
    "Transform your recent searches into symbolic visions."
)

st.write(
    """
Echo Arcana interprets search history as a snapshot
of symbolic consciousness.

The oracle selects a tarot archetype,
generates a dream-image,
and returns a reading shaped by your digital traces.
"""
)

user_input = st.text_area(
    "Enter your last few searches:",
    placeholder=(
        "e.g. banana peels for skin, "
        "dog ate sweet potato, "
        "how long do crows remember faces"
    ),
    height=120
)

# ---------------------------
# MAIN BUTTON
# ---------------------------
if st.button("Consult the Oracle"):

    if not user_input.strip():
        st.warning("The oracle requires something to interpret.")
        st.stop()

    # ---------------------------
    # CARD SELECTION
    # ---------------------------
    with st.spinner("Shuffling the archive..."):

        cards = get_random_cards(3)

        if not cards:
            st.error("The cards could not be retrieved.")
            st.stop()

        filtered_cards = filter_recent(
            cards,
            st.session_state.recent_cards
        )

        card = choose_card(
            filtered_cards,
            user_input
        )

    # ---------------------------
    # DISPLAY CARD
    # ---------------------------
    st.markdown("---")

    st.subheader(card["name"])

    st.write(card["meaning_up"])

    # ---------------------------
    # IMAGE GENERATION
    # ---------------------------
    with st.spinner("The oracle is dreaming..."):

        generated_image = generate_oracle_image(
            card["name"],
            card["meaning_up"],
            user_input
        )

    if generated_image:

        st.image(
            generated_image,
            use_container_width=True
        )

    # ---------------------------
    # INTERPRETATION
    # ---------------------------
    with st.spinner("Interpreting the vision..."):

        interpretation = generate_interpretation(
            card["name"],
            card["meaning_up"],
            user_input
        )

    st.markdown("### Interpretation")

    st.write(interpretation)

    # ---------------------------
    # RECENT CARD MEMORY
    # ---------------------------
    st.session_state.recent_cards.append(
        card["name"]
    )

    st.session_state.recent_cards = (
        st.session_state.recent_cards[-5:]
    )