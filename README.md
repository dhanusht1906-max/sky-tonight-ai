# What's in the Sky Tonight

An AI-powered sky-watching assistant that tells you exactly what's visible in the night sky from your location — combining real orbital mechanics with a locally-hosted LLM to generate natural, conversational sky guides.

## Features

-  **Any location worldwide** — searchable dropdown of world cities
-  **Real planet positions** — computed using JPL ephemeris data (Skyfield), not approximations
-  **Moon position and visibility**
-  **Live ISS tracking** — orbital propagation from real TLE data (CelesTrak)
-  **Meteor shower detection** for any given date
-  **AI-generated sky guide** — natural language summary powered by a locally-run LLM (Llama 3.2 via Ollama), no paid API required
-  Custom space-themed UI built with Streamlit

## Tech Stack

| Component | Tool |
|---|---|
| Astronomical calculations | [Skyfield](https://rhodesmill.org/skyfield/) + NASA JPL DE421 ephemeris |
| Satellite tracking | CelesTrak TLE data + orbital propagation |
| Geocoding | Geopy (Nominatim / OpenStreetMap) |
| City database | GeonamesCache |
| LLM inference | Llama 3.2 (3B) via Ollama — runs locally |
| Web UI | Streamlit |

## How It Works

1. User selects a city and date/time
2. The app computes real positions of the Sun, Moon, and visible planets for that exact location and time
3. It checks live ISS orbital data to determine if a pass is visible
4. It cross-references the date against known meteor shower windows
5. All this structured data is fed to a locally-hosted LLM, which generates a warm, accurate, natural-language sky guide

## Setup

\`\`\`bash
# Clone the repo
git clone https://github.com/dhanusht1906-max/sky-tonight-ai.git
cd sky-tonight-ai

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install streamlit skyfield geopy requests geonamescache ollama

# Install Ollama and pull the model (one-time)
# Download from https://ollama.com/download
ollama pull llama3.2

# Run the app
streamlit run streamlit_app.py
\`\`\`

## Why a local LLM?

This project intentionally uses a locally-hosted model (via Ollama) instead of a paid API, demonstrating the ability to run and integrate open-weight LLMs without external dependencies or costs.

