import os
import random
import re
import streamlit as st
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------
# CONFIG
# ---------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

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
        response = model.generate_content(prompt)
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

        if len(pool) >= n:
            return random.sample(pool, n)

        return pool # Return all available unique items if not enough to sample

    except Exception as e:
        st.error("Art Institute API error")
        st.exception(e)
        return []
# ---------------------------
# SEARCH ORCHESTRATOR
# ---------------------------
def curate_artwork(pool, card_name, user_input):
    # Fixed indentation for the selection logic
    options = "\n".join([
        f"{i}: {a.get('title','Untitled')} | {a.get('creators',[{}])[0].get('description','Unknown')} | {a.get('creation_date','')}"
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
        text = model.generate_content(prompt).text
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
    You are a profound and poetic oracle, deeply connecting symbolism across tarot and art.
    Your task is to craft an insightful interpretation that weaves together:
    1. The user's provided context or query.
    2. The deep symbolism and meaning of the tarot card.
    3. The visual and thematic elements of the selected artwork.

    Guidelines for your interpretation:
    - Explore the deeper, resonant connections between all three elements.
    - Use evocative and thought-provoking language.
    - Provide an interpretation that feels insightful, personal, and offers a unique perspective.
    - Aim for a length of 5-8 sentences, providing rich detail without excessive verbosity.

    User's Context: {user_input}
    Tarot Card: {card}
    Tarot Card Meaning: {meaning}
    Selected Artwork: {artwork['title']} by {artwork['artist']}

    Output: A profound interpretation, 5-8 sentences in length.
    """

    try:
        response = model.generate_content(prompt)
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
st.write("*Echo your data into the halls of history.*")

user_input = st.text_input(
    "Enter your last 3 google searches:",
    placeholder="e.g. banana peels, gardening, organic soil"
)

if st.button("Consult the Archive"):
    if not user_input:
        st.warning("Please enter some search history first.")
        st.stop()

    with st.spinner("The Librarian is searching the vaults..."):
        all_cards = get_random_cards(3)
        cards = filter_recent(all_cards)
        card = choose_card(cards, user_input)

    st.subheader(f"Your Card: {card['name']}")
    st.info(card["meaning_up"])

    with st.spinner("🖼️ Curation in progress..."):
        pool = get_random_artic_pool(4)

    if not pool:
        st.error("The archive is empty.")
        st.stop()

    artwork = curate_artwork(pool, card["name"], user_input)
    st.image(artwork["image"], use_container_width=True)
    st.markdown(f"**{artwork['title']}**")
    st.caption(f"{artwork['artist']}, {artwork['date']}")
    st.caption(f"Source: {artwork['source']}")

    interpretation = generate_interpretation(
        card["name"],
        card["meaning_up"],
        user_input,
        artwork
    )
    st.markdown("**The Oracle's Insight:**")
    st.write(interpretation)

    st.session_state.recent_cards.append(card["name"])
    st.session_state.recent_cards = st.session_state.recent_cards[-5:]

    # Add artwork ID to recent_artworks to avoid repetition
    st.session_state.recent_artworks.append(artwork["id"])
    st.session_state.recent_artworks = st.session_state.recent_artworks[-10:] # Keep a history of the last 10 artworks