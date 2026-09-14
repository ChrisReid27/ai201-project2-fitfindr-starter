"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    query_keywords = set(re.findall(r"[a-z0-9]+", description.lower()))
    matches = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.lower() not in listing["size"].lower():
            continue

        searchable_text = " ".join(
            [
                listing["title"],
                listing["description"],
                listing["category"],
                *listing["style_tags"],
            ]
        ).lower()
        listing_keywords = set(re.findall(r"[a-z0-9]+", searchable_text))
        score = len(query_keywords & listing_keywords)

        if score > 0:
            matches.append((score, listing))

    matches.sort(key=lambda match: match[0], reverse=True)
    return [listing for _, listing in matches]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    wardrobe_items = wardrobe.get("items", [])
    item_details = (
        f"Title: {new_item.get('title', 'Unknown item')}\n"
        f"Description: {new_item.get('description', '')}\n"
        f"Category: {new_item.get('category', '')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}"
    )

    if wardrobe_items:
        wardrobe_details = "\n".join(
            "- "
            + "; ".join(
                part
                for part in (
                    item.get("name", "Unnamed item"),
                    f"category: {item.get('category', '')}",
                    f"colors: {', '.join(item.get('colors', []))}",
                    f"style tags: {', '.join(item.get('style_tags', []))}",
                    f"notes: {item.get('notes')}" if item.get("notes") else "",
                )
                if part
            )
            for item in wardrobe_items
        )
        request = (
            "Suggest 1 or 2 complete outfits using the new item and named pieces "
            "from the user's wardrobe. Include a top, bottom, shoes, and useful "
            "accessories or outerwear when appropriate. Explain briefly why the "
            "colors and proportions work. Do not invent wardrobe pieces."
        )
    else:
        wardrobe_details = "The wardrobe is empty."
        request = (
            "Suggest 1 or 2 complete outfit ideas for the new item using commonly "
            "available pieces. Give practical pairing, color, layering, and "
            "accessory advice, and describe the overall vibe."
        )

    prompt = (
        "You are a helpful personal stylist specializing in thrifted fashion.\n\n"
        f"New item:\n{item_details}\n\n"
        f"User wardrobe:\n{wardrobe_details}\n\n"
        f"{request}\n"
        "Format the response as clear, concise outfit suggestions."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "system",
                "content": "You give specific, wearable outfit advice.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Unable to create a fit card because no outfit suggestion was provided."

    item_title = new_item.get("title", "this thrifted find")
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "the resale platform")
    prompt = (
        "Write a casual, authentic 2-4 sentence social-media outfit caption for "
        "an OOTD post. Mention the item name, its price, and its platform exactly "
        "once each. Capture the outfit's specific vibe using details from the "
        "suggestion. Sound like a real person sharing a thrifted find, not a "
        "product description. Do not add headings or explain your process.\n\n"
        f"Item name: {item_title}\n"
        f"Price: ${item_price}\n"
        f"Platform: {item_platform}\n"
        f"Outfit suggestion:\n{outfit.strip()}"
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "system",
                "content": "You write concise, natural fashion captions.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()
