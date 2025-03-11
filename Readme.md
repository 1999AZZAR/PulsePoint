# PulsePoint

## 📌 Overview

**PulsePoint** is an advanced Open-Source Intelligence (OSINT) search and analysis tool designed to automatically gather, analyze, and present relevant data from various sources, including Wikipedia, Google, News APIs, Wolfram Alpha, and Semantic Scholar. It employs AI-powered insights to extract key takeaways and perform sentiment analysis on the retrieved content.

---

## Features:

## PulsePoint general knowledge gathering

### 🔍 Intelligent Search

- Automatically queries unused tags for continuous data discovery.
- Supports advanced search filtering (language, date ranges, and exclusions).

### 🤖 AI-Driven Insights

- Uses **Gemini AI** for summarization, cross-referencing, and tagging.
- Extracts **key insights** from aggregated data.
- Generates structured JSON responses for easier integration.

### 📊 Sentiment Analysis

- Implements **VADER** sentiment analysis to determine the tone of articles.
- Helps categorize news and research papers based on positive, negative, or neutral sentiment.

### 🏗️ Scalable and Modular Architecture

- Built with **Flask** and **SQLAlchemy** for database management.
- Supports **automatic search scheduling** using **APScheduler**.
- Easily extendable with additional OSINT sources.

### Other features and capability can be seen at this [document](workflow.md)

---

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Flask
- SQLite (default database)
- API keys for:
  - [NewsAPI](https://newsapi.org/)
  - [Google Search Engine API](https://developers.google.com/custom-search/)
  - [Wolfram Alpha API](https://developer.wolframalpha.com/)
  - [Gemini Api](https://aistudio.google.com/app/apikey)

### Setup Instructions

```bash
# Clone the repository
git clone https://github.com/1999AZZAR/PulsePoint.git
cd PulsePoint

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and add your API keys
echo "NEWSAPI_KEY=your_newsapi_key" >> .env
echo "GSE_API_KEY=your_google_search_api_key" >> .env
echo "GSE_ID=your_google_search_engine_id" >> .env
echo "WOLFRAM_ALPHA_APP_ID=your_wolframalpha_app_id" >> .env
echo "GEMINI_API_KEY=your_gemini_api_key" >> .env

# Run the application
python main.py
```

---

## 🎯 Usage

### 1️⃣ Running the Web Interface

Navigate to `http://localhost:5000/` in your browser to access the search interface.

### 2️⃣ Searching for Data

- Enter your query and optionally configure advanced filters.
- Click **Search**, and the system will gather results from multiple OSINT sources.

### 3️⃣ Viewing AI Insights

- AI-generated summaries and insights will be displayed alongside the search results.
- Sentiment analysis will indicate the overall tone of the content.

### 4️⃣ API Endpoints

You can interact with **PulsePoint** programmatically:

#### ➡️ Perform a Search

```http
POST /search
```

**Parameters:**

```json
{
  "query": "climate change",
  "negative_query": "hoax, conspiracy",
  "from_date": "2024-01-01",
  "to_date": "2024-12-31",
  "language": "en"
}
```

**Response:**

```json
{
  "results": {
    "wikipedia": [{ "title": "Climate Change", "snippet": "Climate change refers to...", "url": "https://en.wikipedia.org/..." }],
    "news_everything": [...],
    "semantic_scholar": [...]
  },
  "summary": "Climate change is a global issue caused by human activities...",
  "insights": "The data suggests that carbon emissions are the primary driver of climate change...",
  "cross_references": "Multiple sources confirm the impact of deforestation on rising temperatures...",
  "tags": ["environment", "global warming", "carbon emissions"]
}
```

---

## 🏗️ Project Structure

```
PulsePoint/
│── main.py               # Flask app initialization & scheduler
│── routes.py             # API endpoints
│── models.py             # Database models
│── osint_helper.py       # OSINT query handling
│── completer.py          # Search validation & re-processing
│── auto_search.py        # Automated background searches
│── mig.py                # missing value fixer
│── instance/
│   └── osint.db          # the database (will auto generated if none)
│── templates/
│   └── index.html        # Web interface (Frontend)
└── static/               # Static assets (CSS, JS, etc.)
```

---

## 🛠️ Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-xyz`)
3. Commit your changes (`git commit -m "Added feature XYZ"`)
4. Push to your branch (`git push origin feature-xyz`)
5. Open a Pull Request

---

## ✨ Credits

Developed with ❤️ by [azzar](https://github.com/1999AZZAR) and the open-source community.

---

## 🌐 Links & Resources

- 📘 Documentation (todo)
- 🐞 [Issue Tracker](https://github.com/1999AZZAR/PulsePoint/issues)
- ✨ [Feature Requests](https://github.com/1999AZZAR/PulsePoint/discussions)
