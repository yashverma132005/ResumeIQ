# ResumeIQ — AI-Powered Resume Analyzer

A B.Tech final year project. Analyzes resumes against job roles and descriptions, provides ATS scores, skill gap analysis, AI-powered feedback, and a 3-month improvement roadmap.

## Features

- **Resume Score** — Weighted score based on skills, ATS compatibility, section completeness, and word count
- **ATS Check** — Detects formatting issues that block automated screening systems
- **Skill Gap Analysis** — Core skills vs. tools vs. bonus skills per role (7 roles supported)
- **JD Keyword Match** — Paste any job description for a keyword match score
- **AI Roadmap** — Personalized 3-month plan powered by Claude AI
- **AI Insights** — Critical fixes, quick wins, bullet point rewrite examples
- **Student Resume Guide** — Comprehensive guide with examples, do/don'ts, and role tips

## Supported Roles

Frontend Developer · Backend Developer · Full Stack Developer · Data Scientist · ML Engineer · DevOps Engineer · Mobile Developer

## Setup & Local Development

```bash
# 1. Clone and enter the project
git clone <your-repo>
cd resume-analyzer

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here
# Windows: set ANTHROPIC_API_KEY=your_key_here

# 5. Run locally
python app.py
# Visit http://localhost:5000
```

## Deployment on Render (Free)

1. Push your code to a GitHub repository
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
5. Add Environment Variable:
   - Key: `ANTHROPIC_API_KEY`
   - Value: your Anthropic API key
6. Click **Deploy**

## Deployment on Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variable: `ANTHROPIC_API_KEY=your_key`
4. Railway auto-detects the Procfile and deploys

## Project Structure

```
resume-analyzer/
├── app.py               # Flask backend — analysis logic + routes
├── requirements.txt     # Python dependencies
├── Procfile             # Gunicorn start command for deployment
├── templates/
│   ├── index.html       # Main analyzer page
│   └── guide.html       # Student resume guide
└── static/
    └── style.css        # All styles
```

## Tech Stack

- **Backend:** Python, Flask, pdfplumber, python-docx, Anthropic Claude API
- **Frontend:** Vanilla HTML/CSS/JS, Google Fonts (DM Sans + Instrument Serif)
- **Deployment:** Render or Railway (Gunicorn)

## Getting an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up / log in
3. Go to API Keys → Create Key
4. Copy and use as `ANTHROPIC_API_KEY`

Note: The app works without an API key — AI Insights and AI Roadmap tabs will be hidden, but all other analysis (ATS, skills, JD match, sections) works without it.
