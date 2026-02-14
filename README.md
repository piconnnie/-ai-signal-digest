# AI & GenAI Signal Digest 🤖

> **An autonomous multi-agent system to digest AI signals and deliver insights via WhatsApp.**

## Overview

This system is designed to help busy professionals stay on top of the rapidly evolving AI landscape. It autonomously:

1. **Acquires** research papers (arXiv) and news.
2. **Filters** content using LLMs (Relevance Decision).
3. **Enriches** data with embeddings and topics.
4. **Prioritizes** high-signal items.
5. **Synthesizes** concise summaries (TL;DR).
6. **Validates** quality with guardrails.
7. **Delivers** a digest via WhatsApp.

---

## Architecture

The system is composed of **7 Autonomous Agents** orchestrated by a central scheduler:

* **Agent 1: Acquisition** - Fetches raw data.
* **Agent 2: Relevance** - Classifies content (LLM-based).
* **Agent 3: Enrichment** - Generates embeddings.
* **Agent 4: Prioritization** - Ranks content.
* **Agent 5: Synthesis** - Generates summaries.
* **Agent 6: Guardrail** - Validates output quality.
* **Agent 7: Delivery** - Sends via Twilio/WhatsApp.

Plus a **Flask Dashboard** for monitoring and manual control.

---

## Quick Start

### Prerequisites

* Python 3.11+
* API Keys: OpenAI/Gemini, Twilio (Optional for delivery)

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/piconnnie/-ai-signal-digest.git
    cd -ai-signal-digest
    ```

2. **Setup Virtual Environment:**

    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configuration:**
    Create a `.env` file in the root directory:

    ```env
    OPENAI_API_KEY=sk-your-key-here
    TWILIO_ACCOUNT_SID=your-sid
    TWILIO_AUTH_TOKEN=your-token
    TWILIO_FROM_NUMBER=whatsapp:+14155238886
    DATABASE_URL=sqlite:///data/signal_digest.db
    ```

### Usage

**Run the Pipeline (Background Service):**

```bash
python -m src.main
```

**Run the Dashboard (UI):**

```bash
python -m src.ui.app
```

Open `http://localhost:5000` to view the dashboard.

---

## License

MIT
