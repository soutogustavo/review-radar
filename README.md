![Status](https://img.shields.io/badge/status-in%20development-yellow)

# Review Radar

> *"We read your Google reviews for you, identify what's hurting your business, and tell you exactly what to do about it."*

ReviewRadar is an intelligent review monitoring and advisory system for small business owners. It automatically collects Google Maps reviews, identifies recurring negative patterns, and generates specific, actionable recommendations — giving owners the operational insight they previously lacked the time or expertise to produce themselves.


## The Problem

Small business owners rarely have the staff, time, or analytical background to systematically monitor what customers are saying online. A negative pattern mentioned across dozens of reviews (i.e. slow service, untrained staff, inconsistent product quality) can persist for months simply because no one connected the dots. By the time the owner notices, the damage to reputation is already done.

ReviewRadar closes that gap.

## Who Is This For

The primary user is a small business owner or a small team of 1–3 associates. The system is designed for non-technical users who need clear, actionable output — not raw data or generic summaries.


## What the System Does

1. **Collects** Google Maps reviews for a target business via web scraping
2. **Extracts** the specific aspects mentioned in each review (food quality, waiting time, staff attitude, etc.)
3. **Classifies** the sentiment of each aspect as positive, negative, or neutral
4. **Aggregates** negative themes across all reviews by frequency and severity
5. **Generates** specific, context-aware action items for each recurring negative theme
6. **Presents** everything through a clean Streamlit dashboard for the business owner

## Architecture Overview

The initial architecture was designed to be modular and scalable, allowing for future improvements and integrations. It consists of three main components:

1. **Frontend**: A Streamlit dashboard for the business owner
2. **Backend**: A FastAPI application for orchestration and API endpoints
3. **LangGraph Pipeline**: A LangGraph stateful graph for the analysis pipeline

<img width="1672" height="941" alt="Image" src="https://github.com/user-attachments/assets/eab69ed3-1dcd-488e-837c-ea8f4b892bb0" />

## LangGraph Pipeline Design

The analysis pipeline is implemented as a LangGraph stateful graph. Each node is a discrete LangChain step with its own prompt, making each stage independently testable and replaceable.

State should contain the following information:

```
State: { reviews, aspects, sentiments, themes, suggestions }
```

<img width="1693" height="929" alt="Image" src="https://github.com/user-attachments/assets/10a38c58-f1e7-4d7a-b944-5905889a6808" />


**Why LangGraph over a simple LCEL chain?**

The pipeline maintains a shared state object that accumulates progressively richer data across nodes. LangGraph's state management handles this cleanly. It also enables conditional branching, for example, skipping the suggestion generation step entirely if no negative aspects are found in a review set.

**Why separate LLM calls per step?**

Each step has a distinct responsibility and a different prompt structure. Separating them gives better debuggability (via LangSmith), allows independent prompt iteration, and avoids the reliability problems that come from asking a single prompt to do too many things at once.


## Tech Stack

The tech stack was carefully selected to ensure modularity, scalability, and ease of maintenance. Here's a breakdown of the choices made:

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Ecosystem maturity for ML/NLP |
| Package manager | uv | Fast, modern, `pyproject.toml`-based |
| Orchestration | LangGraph | Stateful pipeline with conditional branching |
| LLM | LLaMA 3.3 70B via Groq | Fast inference, free tier, open-source |
| Observability | LangSmith | Trace and debug each LLM call in the pipeline |
| Scraping | Crawl4AI + BeautifulSoup | Validated via POC; reliable for consistent HTML structure |
| Backend | FastAPI | Lightweight, async-ready API layer |
| Frontend | Streamlit | Rapid dashboard development; no frontend expertise required |
| Database | Supabase (PostgreSQL) | Managed Postgres with REST API; supports PROD/DEV project separation |
