# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

## Video Demo
https://drive.google.com/file/d/1_6kRDGDOFBbgYdtG2tI7_MVygu8TaMl3/view?usp=sharing

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**
"polo shirt, size M, with sneakers or buckled boots"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `description="polo shirt", size="M", max_price=None`
- Why this tool: Search the listings json for a polo shirt, restrict the results to size M, and the price filter gets left open because the user did not specify a budget.
- Output: Vintage Polo Shirt — Forest Green
     Price: $18.00
     Platform: thredUp
     Category: tops
     Size: M
     Condition: good
     Colors: green, forest green
     Brand: Ralph Lauren

     Classic polo in forest green. Short sleeve, ribbed collar. Slightly boxy. The kind of piece that goes with everything.

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `new_item=<the Vintage Polo Shirt — Forest Green listing from Step 1>, wardrobe=<the user's wardrobe dictionary>`
- Why this tool: The selected polo and the user's existing wardrobe get used to create complete outfit combinations that include the requested sneakers or buckled boots if applicable. This was a new wardrobe input so, the finder only goes off the found polo.
- Output: **Outfit 1 – Casual Weekend Vibe**  
     - **Top:** Vintage Polo Shirt – Forest Green (the piece)  
     - **Bottom:** High‑waisted straight‑leg denim in a light‑wash (or a thrifted pair of faded black skinny jeans if you prefer a darker base). The denim’s cool blue contrasts nicely with the earthy green.  
     - **Layer:** Open‑front, short‑sleeve chambray shirt or a lightweight white button‑down left unbuttoned for extra texture.  
     - **Shoes:** White low‑top canvas sneakers (easily found in thrift bins or discount stores).  
     - **Accessories:** Brown leather belt (matching the shoe tone), a simple canvas tote or canvas backpack in a neutral tan, and a pair of round‑frame sunglasses.  
     - **Vibe:** Laid‑back preppy‑retro. The forest‑green polo anchors the look while the denim and white sneakers keep it relaxed and easy‑going—perfect for brunch, a farmers’ market, or a park stroll.

     ---

     **Outfit 2 – Smart‑Casual / Work‑Ready Vibe**  
     - **Top:** Vintage Polo Shirt – Forest Green (the piece

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `outfit=<the suggestion returned by suggest_outfit>, new_item=<the Vintage Polo Shirt — Forest Green listing>`
- Why this tool: Turn the selected outfit and thrifted item details into a short, casual, social media ready caption for the final fit card which is also the final output.
- Output: Scored this Vintage Polo Shirt — Forest Green for $18.0 on thredUp and paired it with high‑waisted light‑wash denim and white canvas kicks. Loving the laid‑back preppy vibe for a weekend brunch stroll.

**Final output to user:**
Your fit card
- Scored this Vintage Polo Shirt — Forest Green for $18.0 on thredUp and paired it with high‑waisted light‑wash denim and white canvas kicks. Loving the laid‑back preppy vibe for a weekend brunch stroll.
---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the description, size, or maximum price. | Returns an empty list instead of raising an exception. The caller can tell the user that no matching listings were found. |
| `suggest_outfit` | The wardrobe is empty; `GROQ_API_KEY` is missing, or the LM returns blank content. | Uses general styling advice when the wardrobe has no items. If the API key is missing, it raises a clear `ValueError` explaining how to configure it. If the LM returns no content, it raises a run time error with the completion finish reason. |
| `create_fit_card` | The outfit suggestion is empty, `GROQ_API_KEY` is missing, or the LM returns blank content or repeats the outfit exactly. | Returns a descriptive message for an empty outfit. If the API key is missing, it raises a clear value error. If the LM response is empty or identical to the outfit suggestion, raises a run time error rather than returning an unusable caption. |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**
Planning.md helped greatly during tool implementation, especially when prompting Copilot to do each implementation in isolation, following the specific layed out in there. It also helped me to remember what to do when it came to implementing the planning loop and being able to get the agent to follow each step.

**One divergence from your spec, and why:**
I had to change the token amount for fit card and also limit its word count. I had to increase the token count for the tool from 200 to 500 because responses kept getting cut off prematurely or sometimes defaulting to error responses. I then had to limit word count to 80 so that the message caption would retain the specifics of being short and shareable for social media.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
