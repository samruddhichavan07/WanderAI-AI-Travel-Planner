# AI Travel Planner

An AI-powered travel planner that creates a personalised, day-by-day itinerary from your destination, number of days, budget and interests. It uses a **local LLM (Ollama Llama 3.2)** together with **ChromaDB vector search (RAG)** so the plan is built from real places in our dataset.

> Mini project for the subject **Agentic AI and LLM**.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Features](#features)
4. [Working Flow](#working-flow)
5. [Agentic AI Workflow](#agentic-ai-workflow)
6. [Technology Stack](#technology-stack)
7. [Project Structure](#project-structure)
8. [Installation](#installation)
9. [Ollama Setup](#ollama-setup)
10. [Run the App](#run-the-app)
11. [Screenshots](#screenshots)
12. [Future Scope](#future-scope)
13. [Team](#team)

---

## Project Overview
Planning a trip usually means searching many websites and blogs. **AI Travel Planner** brings this into one simple app. You enter where you want to go, for how many days, your budget and what you enjoy. The app finds matching places and the LLM arranges them into a clear, day-wise plan.

The LLM runs **locally on your computer through Ollama**, so no cloud AI service is needed.

## Problem Statement
In traditional travel planning:
- Information is scattered across many websites, blogs and maps.
- Comparing places, routes and timings takes a lot of time.
- Generic plans ignore personal interests and travel style.
- It is hard to fit a plan into a fixed budget.

This project solves these problems with an AI assistant that plans the trip for you.

## Features
- Destination search with suggestions from known cities
- Interest-based planning (history, nature, beaches, food, adventure and more, plus custom interests)
- Budget, currency (INR, USD, EUR) and travel style (Budget, Comfort, Luxury)
- Day-wise itinerary with an "all days" or "single day" view
- Destination photos using the Wikipedia API
- Explore Destinations page with Indian and international places
- Packing checklist with progress
- Download the itinerary as a `.txt` file
- Recent trips and a Regenerate button

## Working Flow
```
User Input  ->  LLM Understanding  ->  AI Agent searches / analyzes places
            ->  Recommendations    ->  Personalized Itinerary
```
1. **User Input** - destination, days, budget, travel style and interests.
2. **LLM Understanding** - the local Llama 3.2 model understands the request.
3. **Search and Analysis** - matching places are retrieved from ChromaDB.
4. **Recommendations** - the best-fit places are selected for the interests and budget.
5. **Personalized Itinerary** - a day-by-day plan is shown in the Streamlit app.

## Agentic AI Workflow
The project follows a simple **Retrieve -> Reason -> Present** pattern:

| Step | What happens | Tool used |
|------|--------------|-----------|
| Retrieve | Places that match the destination and interests are found using vector search (**RAG**) | ChromaDB |
| Reason | The local LLM arranges the retrieved places into days that fit the budget | Ollama Llama 3.2 + LangChain |
| Present | The plan, photos, packing list and export option are shown | Streamlit + Wikipedia API |

- **Ollama Llama 3.2 is a local LLM.** It runs on your own machine, not on a cloud server.
- **ChromaDB is the vector database used for RAG (Retrieval-Augmented Generation).** The LLM gets real places from our dataset instead of guessing.

## Technology Stack
| Technology | Purpose |
|------------|---------|
| Python | Core language |
| Streamlit | Web interface |
| LangChain | LLM integration and agent logic |
| Ollama Llama 3.2 | Local LLM |
| ChromaDB | Vector database for RAG / vector search |
| Wikipedia API | Destination information and photos / content |

## Project Structure
```
ai-travel-planner/
|-- app.py                 # Streamlit web app (user interface)
|-- agent.py               # LLM + retrieval logic that generates the itinerary
|-- build_vectorstore.py   # Builds the ChromaDB vector store from the place data
|-- merge_data.py          # Merges the place datasets into one file
|-- image_utils.py         # Fetches destination photos
|-- data/
|   |-- Top Indian Places to Visit.csv
|   |-- international_places.csv
|   `-- merged_places.csv
|-- requirements.txt       # Python packages
|-- .env.example           # Example settings (copy to .env)
|-- .gitignore
`-- README.md
```
`chroma_db/` (the generated vector store), `.env` and `venv/` are not uploaded to GitHub. You create them on your own computer using the steps below.

## Installation
**Prerequisites:** Python 3.10 or newer, Git, and Ollama (see [Ollama Setup](#ollama-setup)).

```bash
# 1. Clone the repository (use your repository's URL)
git clone https://github.com/samruddhichavan07/ai-travel-planner.git
cd ai-travel-planner

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 3. Install the packages
pip install -r requirements.txt

# 4. Create your settings file
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux

# 5. Build the vector store (creates the chroma_db folder)
python build_vectorstore.py
```
If `data/merged_places.csv` is missing, run `python merge_data.py` before step 5.

## Ollama Setup
Ollama lets you run LLMs on your own computer.

1. Download and install Ollama from https://ollama.com/download
2. Download the Llama 3.2 model:
   ```bash
   ollama pull llama3.2
   ```
3. Check that it works:
   ```bash
   ollama run llama3.2
   ```
   Type `/bye` to exit. Keep Ollama running while you use the app.

## Run the App
```bash
streamlit run app.py
```
Your browser opens the app (usually at `http://localhost:8501`).

## Screenshots
> Add your own screenshots in a `screenshots/` folder and link them here.

> **Home / Plan a Trip page** - screenshot placeholder
>
> **Generated itinerary** - screenshot placeholder
>
> **Explore Destinations page** - screenshot placeholder

Example (use after adding the image): `![Home page](screenshots/home.png)`

## Future Scope
- Real-time weather information in the plan
- Map and route view
- Support for more destinations and larger datasets
- Voice input and multiple languages
- Saving and sharing trips


