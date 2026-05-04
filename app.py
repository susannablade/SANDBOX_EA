import os
import random
import re
import streamlit as st
import requests
import time # Import the time module
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------
# CONFIG
# ---------------------------
# Ensure the API key is loaded from an environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define two different models for different tasks
model_fast = genai.GenerativeModel("gemini-2.5-flash-lite") # Faster model for quick decisions
model_interpret = genai.GenerativeModel("gemini-2.5-flash") # More capable model for detailed interpretations

session = requests.Session()

TAROT_API_URL = "https://tarot-api-3hv5.onrender.com/api/v1/cards/random"
Art_Institute_of_Chicago_API_URL = "https://api.artic.edu/api/v1/artworks/search"

# ---------------------------
# TAROT
# ---------------------------
if "recent_cards" not in st.session_state:
    st.session_state.recent_cards = []
if "recent_artworks" not in st.session_state:
    st.session_state.recent_artworks = []

# New states for optional interpretation
if "current_card_data" not in st.session_state:
    st.session_state.current_card_data = None
if "current_artwork_data" not in st.session_state:
    st.session_state.current_artwork_data = None
if "current_user_input" not in st.session_state:
    st.session_state.current_user_input = ""
if "show_results_display" not in st.session_state:
    st.session_state.show_results_display = False
if "interpretation_text" not in st.session_state:
    st.session_state.interpretation_text = ""
if "interpretation_requested" not in st.session_state:
    st.session_state.interpretation_requested = False

def get_random_cards(n=3):
    cards = []
    for _ in range(n):
        try:
            res = session.get(TAROT_API_URL, timeout=5)
            res.raise_for_status()
            cards.append(res.json()["cards"][0])
        except:
            continue
    return cards

def filter_recent(cards):
    recent = st.session_state.recent_cards
    filtered = [c for c in cards if c["name"] not in recent]
    return filtered if filtered else cards

# ---------------------------
# AI Choose Tarot Card
# ---------------------------
def choose_card(cards, user_input):
    names = [c["name"] for c in cards]
    prompt = f"User input: {user_input}\n\nChoose the tarot card that best fits.\n\nCards:\n{names}\n\nReturn ONLY the card name."

    try:
        response = model_fast.generate_content(prompt)
        text = response.text.strip()
        for c in cards:
            if c["name"].lower() in text.lower():
                return c
    except:
        pass
    return random.choice(cards)


# ---------------------------
# CHICAGO API
# ---------------------------
@st.cache_data(ttl=100)
def get_random_artic_pool(n=4):
    print("Attempting to fetch artworks from Art Institute of Chicago API...")
    try:
        res = session.get(
            "https://api.artic.edu/api/v1/artworks/search",
            params={
                "q": "painting",
                "fields": "id,title,image_id,artist_title,date_display",
                "limit": 40 # Increased limit to get more candidates
            },
            timeout=5
        ).json()

        data = res.get("data", [])
        print(f"API response data length: {len(data)}")

        # Filter out recently displayed artworks
        recent_artwork_ids = st.session_state.recent_artworks
        filtered_data = [obj for obj in data if obj.get("id") and obj.get("id") not in recent_artwork_ids]

        pool = []
        for obj in filtered_data:
            image_id = obj.get("image_id")
            if image_id:
                image_url = f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg"

                pool.append({
                    "id": obj.get("id"), # Add artwork ID
                    "image": image_url,
                    "title": obj.get("title", "Untitled"),
                    "artist": obj.get("artist_title", "Unknown Artist"),
                    "date": obj.get("date_display", "Unknown Date"),
                    "source": "Art Institute of Chicago"
                })
        print(f"Filtered pool length: {len(pool)}")

        if len(pool) >= n:
            return random.sample(pool, n)

        return pool # Return all available unique items if not enough to sample

    except Exception as e:
        print(f"Art Institute API error: {e}") # Log the actual exception
        st.error("Art Institute API error")
        st.exception(e)
        return []
# ---------------------------
# SEARCH ORCHESTRATOR
# ---------------------------
def curate_artwork(pool, card_name, user_input):
    # Fixed indentation for the selection logic
    options = "\n".join([
        f"{i}: {a.get('title','Untitled')} | {a.get('artist','Unknown')} | {a.get('date','')}"
        for i, a in enumerate(pool)
    ])

    prompt = f"""
    You are an intuitive museum curator with a poetic sense of symbolism.
    User: {user_input}
    Tarot: {card_name}
    Choose the artwork that feels most symbolically resonant.
    Options:
    {options}
    Return ONLY the index number of the selection.
    """

    try:
        text = model_fast.generate_content(prompt).text
        match = re.search(r"\d+", text)
        choice = int(match.group()) if match else 0
    except:
        choice = 0

    selected = pool[min(choice, len(pool)-1)]

    return {
        "id": selected["id"], # Return artwork ID
        "image": selected["image"],
        "title": selected["title"],
        "artist": selected["artist"],
        "date": selected["date"],
        "source": selected["source"]}

#----------------------------
# AI INTERPRETATION
#----------------------------
def generate_interpretation(card, meaning, user_input, artwork):
    prompt = f"""
    You are an oracle connecting symbolism across tarot and art.

    Your task:
    Explain how the selected artwork relates to BOTH:
    1. The user's input
    2. The tarot card meaning

    Guidelines:
    - Connect the symbolism of the card to the user's situation
    - Make the artist come to life for the reader by including notes on the style, school of art, differentiators of the artist.
    - 5-6 sentences max
    - Make it feel insightful, not random

    User's Context: {user_input}
    Tarot Card: {card}
    Tarot Card Meaning: {meaning}

    Artwork:
    Title: {artwork['title']}
    Artist: {artwork['artist']}
    Date: {artwork['date']}


    Output: A short interpretation.
    """

    try:
        response = model_interpret.generate_content(prompt)
        generated_text = response.text.strip()
        if not generated_text:
            return f"The Oracle is silent. (AI failed to generate interpretation due to empty response) Card Meaning: {meaning}"
        return generated_text.replace("\n\n", "\n")
    except Exception as e:
        print(f"Error generating interpretation: {e}")
        return f"The Oracle is silent. (AI failed to generate interpretation due to error: {e}) Card Meaning: {meaning}"

#---------------------------
# UI
# ---------------------------
st.title("Echo Arcana: The Curated Oracle")
st.write("**Echo your data into the halls of history. Transform your search history into a symbolic visual reading, retrieved from centuries of art by an intelligent oracle.**")

with st.form("oracle_form"):
    user_input = st.text_input(
        "Enter your last 3 google searches:",
        placeholder="e.g. banana peels, gardening, organic soil"
    )
    submitted = st.form_submit_button("Consult the Archive")

if submitted:
    if not user_input:
        st.warning("Please enter some search history first.")
        st.stop()

    # Reset interpretation flags and data when new submission occurs
    st.session_state.interpretation_requested = False
    st.session_state.interpretation_text = ""
    st.session_state.show_results_display = False # Hide old results until new ones are ready

    with st.spinner("Pulling your Card..."):
        all_cards = get_random_cards(3)
        cards = filter_recent(all_cards)
        card = choose_card(cards, user_input)
        st.session_state.current_card_data = card

    with st.spinner("Searching the Archives for resonant art..."):
        # Add a short delay to make the spinner more visible
        time.sleep(1)
        pool = get_random_artic_pool(4)

    if not pool:
        st.error("The archive is empty.")
        st.stop()

    artwork = curate_artwork(pool, card["name"], user_input)
    st.session_state.current_artwork_data = artwork
    st.session_state.current_user_input = user_input # Store user input for interpretation

    # Set flags to display the card and artwork
    st.session_state.show_results_display = True

    # Update recent cards/artworks list
    st.session_state.recent_cards.append(card["name"])
    st.session_state.recent_cards = st.session_state.recent_cards[-5:]
    st.session_state.recent_artworks.append(artwork["id"])
    st.session_state.recent_artworks = st.session_state.recent_artworks[-10:] # Keep a history of the last 10 artworks

# Display results and optional interpretation outside the form submission block
if st.session_state.get('show_results_display', False):
    card = st.session_state.current_card_data
    artwork = st.session_state.current_artwork_data
    user_input_for_interp = st.session_state.current_user_input

    if card and artwork:
        st.subheader(f"{card['name']}")
        st.info(card["meaning_up"])

        st.image(artwork["image"], use_container_width=True)
        st.markdown(f"**{artwork['title']}**")
        st.caption(f"{artwork['artist']}, {artwork['date']}")
        st.caption(f"Source: {artwork['source']}")

        interpret_button_clicked = st.button("Request Oracle's Insight", key="interpret_button")

        if interpret_button_clicked or st.session_state.interpretation_requested:
            # Generate interpretation only if button is clicked AND it hasn't been requested yet for this session
            if interpret_button_clicked and not st.session_state.interpretation_requested:
                st.session_state.interpretation_requested = True # Mark as requested
                with st.spinner("Interpreting Meaning..."):
                    interpretation = generate_interpretation(
                        card["name"],
                        card["meaning_up"],
                        user_input_for_interp,
                        artwork
                    )
                st.session_state.interpretation_text = interpretation

            # Display the interpretation if it has been generated
            if st.session_state.interpretation_text:
                st.markdown("**The Oracle's Insight:**")
                st.write(st.session_state.interpretation_text)
