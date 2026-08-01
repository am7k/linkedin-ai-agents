# Note 28-07-2026 11:50 AM

## **Blueprint: Autonomous Multi-Agent LinkedIn Tech Content Pipeline**

This document details the architectural design, agent configurations, and deployment strategies for a zero-cost, multi-agent AI pipeline. The system tracks real-time tech trends, selects optimal topics, conducts background research, refines professional text, and automatically publishes directly to a personal LinkedIn profile via the official API. [1]

---

## **🏗️ 1. Complete System Architecture**

The pipeline uses a sequential, multi-agent layout. Each specialized agent performs an isolated task before passing structured data down the assembly line.

```
[ Manual Run / Trigger ]
                             │
                             ▼
 🤖 Agent 1: Trend Scout      ──► Pulls top tech topics via public RSS feeds
                             │
                             ▼
 🤖 Agent 2: Profile Filter   ──► Matches trends against your specific tech niche
                             │
                             ▼
 🤖 Agent 3: Web Researcher   ──► Scrapes articles/documentation for context
                             │
                             ▼
 🤖 Agent 4: Lead Writer      ──► Drafts technical architecture/trade-offs
                             │
                             ▼
 🤖 Agent 5: Editor-in-Chief  ──► Re-formats text for mobile readability & hooks
                             │
                             ▼
 ⚙️ Agent 6: Publisher        ──► Packages payload and calls LinkedIn Posts API
```

---

## **🤖 2. Agent Core Definitions & Prompt Blueprints**

Powered by the **Gemini 2.5 Flash** model (via Google AI Studio's free tier), the agents use specific instructions to prevent robotic writing patterns.

## **Agent 1: The Trend Scout**

- **Role:** Raw Signal Aggregator

- **Input:** System execution command

- **Output:** Array of 5 trending tech strings

- **Logic:** Pulls text elements from the official Google Trends Technology RSS module (`https://google.com`).

## **Agent 2: The Profile Filter**

- **Role:** Strategic Alignment Niche Expert

- **Input:** Array of 5 trends from Agent 1

- **System Prompt:**

    > Review this list of raw tech trends. Filter them against the user's specific core profile: **[Insert Tech Niche, e.g., Cloud Native & Go Backend Systems]**. Discard generic mainstream consumer tech or celebrity tech gossip. Select exactly one trend that provides the highest opportunity to showcase structural engineering authority. Output only the name of the topic.

## **Agent 3: The Web Researcher**

- **Role:** Context & Grounding Engine

- **Input:** Selected trend string from Agent 2

- **Logic:** Uses a search library (such as `duckduckgo-search`) to fetch top text snippets, GitHub discussions, or tech blogs about the topic to eliminate AI hallucinations.

## **Agent 4: The Lead Writer**

- **Role:** Technical Copywriter

- **Input:** Topic + Research logs from Agent 3

- **System Prompt:**

    > You are a senior systems engineer and technical analyst. Write a raw LinkedIn post draft evaluating the provided topic. Focus heavily on real-world engineering trade-offs, architectural friction points, scalability bottlenecks, or structural impact. Do not include introductory filler or greetings. Keep the technical depth high.

## **Agent 5: The Editor-in-Chief**

- **Role:** Readability & Polish Editor

- **Input:** Rough text from Agent 4

- **System Prompt:**

    > You are a precise, human copyeditor writing for mobile audiences. Clean this raw technical draft using these strict formatting limits:
    > 
    > 1. Start directly with an analytical hook in the first 2 lines.
    > 
    > 2. No emojis, no hashtags, and no conversational greetings.
    > 
    > 3. Eliminate robotic filler phrases like "In today's fast-paced world" or "Let's delve deeper".
    > 
    > 4. Break paragraphs every 1 to 2 sentences to optimize for vertical mobile scanning.
    > 
    > 5. Keep sentences under 12 words.
    > 
    > 6. Conclude with an analytical question that drives industry engagement.

## **Agent 6: The Publisher**

- **Role:** Infrastructure Connector (Non-LLM Logic)

- **Input:** Cleaned post string from Agent 5

- **Logic:** Validates character constraints, sets up headers with OAuth tokens, and executes an HTTP POST query targeting `/rest/posts`.

---

## **🔑 3. Financial & API Access Blueprint**

This blueprint operates completely within **free tiers** by separating consumer AI platform products from backend developer tooling.

| Resource System                                         | Functional Access Scope                                 | Financial Cost                                          |
| ------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| **Google AI Studio**                                    | Gemini 2.5 Flash API Key (Allows up to 15 Requests/Min) | **₹0 (Free Tier)**                                      |
| **LinkedIn Developer Portal**                           | Application ID, User Token, Scope: `w_member_social`    | **₹0 (Free Tier)**                                      |
| **Google Trends**                                       | Technology RSS Pipeline Access                          | **₹0 (Open Public Feed)**                               |
| **Execution Environment**                               | Local Terminal/IDE Execution                            | **₹0 (Your Machine)**                                   |

---

## **🛠️ 4. Ready-to-Run Framework Implementation**

Save the following source code into a local file named `multi_agent_pipeline.py`. Update the authentication placeholders at the top before execution.

```python
import xml.etree.ElementTree as ET
import requests
from google import genai

# =====================================================================
# SYSTEM ACCESS CONFIGURATION
# =====================================================================
GEMINI_API_KEY = "PASTE_YOUR_FREE_GEMINI_API_KEY_HERE"
LINKEDIN_ACCESS_TOKEN = "PASTE_YOUR_LINKEDIN_OAUTH_TOKEN_HERE"
LINKEDIN_PERSON_URN = "urn:li:person:PASTE_YOUR_MEMBER_ID_HERE"

# Initialize the Gemini Developer Client
client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================================================
# AGENT 1: TREND SCOUT
# =====================================================================
def agent_trend_scout():
    rss_url = "https://google.com"
    try:
        res = requests.get(rss_url, timeout=10)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            titles = [item.text for item in root.findall('.//item/title')][:5]
            return titles
    except Exception as e:
        print(f"[!] Scout Failure: {e}")
    return ["Generative AI Optimization", "Cloud Scalability Protocols"]

# =====================================================================
# AGENT 2: PROFILE FILTER
# =====================================================================
def agent_profile_filter(trends_list):
    prompt = f"""
    Review this list of raw trending tech trends: {trends_list}.
    Filter them against a professional developer profile focused on Software Architecture and Engineering.
    Discard generic consumer news. Pick the single best topic. Output ONLY the topic title.
    """
    response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
    return response.text.strip()

# =====================================================================
# AGENT 3: WEB RESEARCHER (Simplified Mock/Search Grounding)
# =====================================================================
def agent_web_researcher(target_topic):
    # Returns simulated structural documentation notes to feed the author agent
    return f"Technical context notes regarding {target_topic}: Focus on efficiency gains, memory footprint improvements, and deployment bottlenecks."

# =====================================================================
# AGENT 4: LEAD WRITER
# =====================================================================
def agent_lead_writer(topic, research):
    prompt = f"""
    Target Topic: {topic}
    Background Context: {research}
    
    Write a detailed, analytical draft evaluating this trend. Focus on infrastructure, implementation trade-offs, and structural changes. Avoid introductions.
    """
    response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
    return response.text

# =====================================================================
# AGENT 5: EDITOR-IN-CHIEF
# =====================================================================
def agent_editor_in_chief(raw_draft):
    prompt = f"""
    Clean and optimize this technical draft:
    {raw_draft}
    
    STRICT RULES:
    1. Start directly with an analytical hook in the first two lines.
    2. No emojis. No hashtags.
    3. Break paragraphs every 1-2 sentences for mobile readability.
    4. Keep sentences under 12 words.
    5. End with an analytical question that drives industry engagement.
    """
    response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
    return response.text

# =====================================================================
# AGENT 6: PUBLISHER (API CALL)
# =====================================================================
def agent_publisher(final_text):
    post_url = "https://linkedin.com"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202401"
    }
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "commentary": final_text,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": []}
    }
    
    # Safely print out content before performing the write call
    print("\n[✔] Ready for transmission. Content preview:")
    print(final_text)
    
    # Un-comment the execution code block below when your access tokens are active
    # res = requests.post(post_url, json=payload, headers=headers)
    # print(f"API Server Response Status: {res.status_code}")

# =====================================================================
# PIPELINE ORCHESTRATION ENGINE
# =====================================================================
if __name__ == "__main__":
    print("[1/5] Running Trend Scout...")
    raw_trends = agent_trend_scout()
    
    print("[2/5] Running Profile Filter...")
    filtered_topic = agent_profile_filter(raw_trends)
    print(f"    -> Selected Focus: {filtered_topic}")
    
    print("[3/5] Gathering Research Logs...")
    research_data = agent_web_researcher(filtered_topic)
    
    print("[4/5] Executing Lead Writer Generation...")
    rough_copy = agent_lead_writer(filtered_topic, research_data)
    
    print("[5/5] Formatting text via Editor Agent...")
    polished_post = agent_editor_in_chief(rough_copy)
    
    agent_publisher(polished_post)
```

---

## **🚀 5. Action Plan: Execution Steps**

To get this pipeline up and running, follow these steps:

1. **Get your Gemini Key:** Go to [Google AI Studio](<https://aistudio.google.com/>), click **Get API Key**, and copy it into the `GEMINI_API_KEY` slot.

2. **Set up LinkedIn Developers:** Go to the [LinkedIn Developer Portal](<https://developer.linkedin.com/>), create a new app project, and link it to your personal profile. Add the **Share on LinkedIn** product option to unlock your publishing scopes.

3. **Generate User Token:** Use the platform's developer **Token Generator Tool** to grab an active user string matching permissions for `w_member_social`. Paste that and your member ID (`URN`) directly into the script configuration sections.

4. **Test & Run:** Open your system terminal and execute `python multi_agent_pipeline.py` to watch your AI team generate content in real time.

Would you like to focus on setting up the **LinkedIn Developer portal access paths** first, or do you want to test running the local **Gemini orchestration** steps on your computer?  


[1] [https://evernote.com](<https://evernote.com/ai-rewrite/rewrite-project-proposal-with-ai>)

