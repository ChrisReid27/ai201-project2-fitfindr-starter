# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The mock secondhand listings is loaded and then is searched to find items whose text matches the user's requested description. Next it applies the size and max-price filters, and then it sorts the remaining matches by keyword relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing the item the user wants. The matching process uses keywords from the listing title, description, category, and style tags.
- `size` (str (or None)): The requested size. The matching is case-insensitive and can match combined listing sizes.`None` gets used when the user doesn't mention a specific size.
- `max_price` (float (or None)): The inclusive maximum price in dollars. `None` gets used when the user doesn't specify a price limit.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
Returns `list[dict]`. Each dictionary is one matching listing with its `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`. The list is sorted with the highest keyword-overlap score first.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If no listing passes the optional filters and has at least one relevant keyword, return an empty list. The planning loop stores that list, sets `session["error"]` to a no-results message, and returns before calling the later tools.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Uses the selected listing and the user's wardrobe to ask the language model for one or two complete outfit suggestions. With an empty wardrobe, it asks for general styling advice based on the new item.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dictionary from `search_listings`, including its title, description, category, style tags, size, condition, price, colors, brand, platform, and ID.
- `wardrobe` (dict): A dictionary with an `items` key containing wardrobe items. Each item has `id`, `name`, `category`, `colors`, `style_tags`, and optional `notes`.

**What it returns:**
<!-- Describe the return value -->
Returns a non-empty `str` containing one or two outfit combinations or styling suggestions. A populated wardrobe produces suggestions using named wardrobe pieces; an empty wardrobe produces general pairing, color, and vibe advice.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
An empty wardrobe is supported and is not an error. If the model call fails or produces empty text, the planning loop stores an error and returns before creating a fit card.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Uses the selected listing and generated outfit suggestion to ask the language model for a short, shareable social-media outfit caption.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The non-empty outfit suggestion returned by `suggest_outfit`.
- `new_item` (dict): The selected listing dictionary, including at least its `title`, `price`, and `platform`.

**What it returns:**
<!-- Describe the return value -->
Returns a `str` containing a casual 2–4 sentence caption that mentions the item's name, price, and platform and describes the outfit's style or vibe.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If `outfit` is missing, empty, or whitespace-only, return a descriptive error string without calling the language model. The planning loop records the error and doesn't report the fit card as successful.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
1. First, create a new session with `_new_session(query, wardrobe)`.
2. Parse the query into `description`, `size`, and `max_price`, and store those values in `session["parsed"]`. Missing optional values become `None`.
3. Then call `search_listings(description, size, max_price)` and store its result in `session["search_results"]`.
4. A check gets done to see whether `session["search_results"]` is empty. If it's empty, set `session["error"]` to a helpful message explaining that no listings matched and return the session immediately. Do not call either later tool.
5. If results do exist, set `session["selected_item"]` to `session["search_results"][0]`, the highest-ranked listing.
6. Then call `suggest_outfit(session["selected_item"], session["wardrobe"])` and store the returned string in `session["outfit_suggestion"]`. If the call fails or returns empty text, set `session["error"]` and return early.
7. Otherwise call `create_fit_card(session["outfit_suggestion"], session["selected_item"])` and store the returned string in `session["fit_card"]`. Set an error if the result is unusable but otherwise leave `session["error"]` as `None` and return the completed session.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The session dictionary is where all relevant information gets stored during a session. It contains the original `query`, parsed search values in `parsed`, all listing dictionaries in `search_results`, the first listing in `selected_item`, the input wardrobe in `wardrobe`, the outfit text in `outfit_suggestion`, the final caption in `fit_card`, and an `error` value that is `None` on success. The selected listing and wardrobe are passed to `suggest_outfit`; then the saved outfit text and the same selected listing are passed to `create_fit_card`.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |`[]` is returned. The agent should store it and set a no-results message in `session["error"]`, and then return early without calling the other next in line tools. |
| suggest_outfit | Wardrobe is empty | It should ask the LM for general styling advice for the selected item instead of requiring wardrobe pieces. If the call fails or returns empty text, set `session["error"]` and return early. |
| create_fit_card | Outfit input is missing or incomplete |Return a descriptive error string without calling the LM. It should record the error and the fit card shouldn't be reported as a successful result. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

ASCII Diagram:

    User query and wardrobe
             |
             v
    Planning Loop --------------------------------------------------+
             |                                                     |
             +--> search_listings(description, size, max_price)    |
             |        |                                            |
             |        +--> results = []                             |
             |                 |                                   |
             |                 +--> [ERROR] "No listings found..." |
             |                           -> set error and return   |
             |                                                     |
             |        +--> results = [item, ...]                    |
             |                 |                                   |
             |                 v                                   |
             |        Session: selected_item = results[0]          |
             |                 |                                   |
             +--> suggest_outfit(selected_item, wardrobe)          |
             |                 |                                   |
             |        Session: outfit_suggestion = "..."           |
             |                 |                                   |
             |                 +--> [ERROR] empty or failed text   |
             |                           -> set error and return   |
             |                                                     |
             +--> create_fit_card(outfit_suggestion, selected_item)|
                      |                                              |
                 Session: fit_card = "..."                          |
                      |                                              |
                      +--> [ERROR] empty or failed card            |
                                -> set error and return             |
                      |                                              |
                      v                                              |
                 Return completed session --------------------------+

    Session state stores: query, parsed values, search_results,
    selected_item, wardrobe, outfit_suggestion, fit_card, and error.

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I'll use Copilot/Claude my Tool 1, Tool 2, and Tool 3 specifications one at a time for function implementation. After each tool is implemented, I'll check it over and ask Copilot/Claude about anything that seems unusual or that is clearly wrong. I'll test each tool function with the agents before I start implementation of the next one using pytests in my created tests folder.
**Milestone 4 — Planning loop and state management:**
I'll use Copilot/Claude to implement the planning loop function using my planning loop and state management specifications from planning.md. I'll look over the code that is produced to make sure it matches my original specifications, unless the change is actually warranted. The wiring to agent.py will also be aided with AI agents, where I'll use it to test whether the no-results path returns the error message in session["error"] and leaves session["fit_card"] as None like it's supposed to.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The `search_listings` tool starts by parsing the query into `description` (vintage graphic tee), `size` (None because no size was requested), and `max_price` (30.0) from the itemss in the listings json. It then calls `search_listings(description="vintage graphic tee", size=None, max_price=30.0)`. The tool returns a list of matching listing dictionaries, sorted by keyword relevance. Each dictionary includes the listing ID, title, description, category, style tags, size, condition, price, colors, brand, and platform.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
If the search list is empty, then the agent stores a no-results message in `session["error"]` and returns without calling another tool. If the search list has stuff in it, then it selects the first, highest-ranked listing as `session["selected_item"]` and calls `suggest_outfit(new_item=selected_item, wardrobe=the user's wardrobe)`. The wardrobe contains named pieces close to what the user asked for so results close to baggy jeans and chunky sneakers. The tool returns a non-empty string with one or two outfits that use those pieces and the selected graphic tee.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The agent stores the outfit string in `session["outfit_suggestion"]` and calls the third tool, `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`. This tool returns a caption that mentions the tee's title, price, platform, and outfit vibe. The agent stores it in `session["fit_card"]` and returns the completed session with `session["error"]` set to `None`.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user is presented with fit card caption, the recommended outfit using the items they mentioned (baggy jeans and chunky sneakers), and a graphic tee from the listings that best matches what the user initially described, along with its price. If no listings are matched, then the user instead sees a message explaining that no results were found and that a new broader or different criteria should net better results.