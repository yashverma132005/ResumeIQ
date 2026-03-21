from flask import Flask, render_template, request, redirect, url_for, jsonify
import pdfplumber
import docx
import re
import json
import os
from collections import Counter

app = Flask(__name__)

# ---------- ROLE SKILLS ----------
ROLE_SKILLS = {
    "frontend": {
        "core": ["html", "css", "javascript", "react", "typescript"],
        "tools": ["git", "webpack", "figma", "jest", "tailwind"],
        "bonus": ["vue", "next.js", "graphql", "accessibility", "performance optimization"]
    },
    "backend": {
        "core": ["python", "sql", "rest api", "node.js", "django"],
        "tools": ["git", "docker", "postgresql", "redis", "linux"],
        "bonus": ["flask", "fastapi", "microservices", "ci/cd", "aws"]
    },
    "fullstack": {
        "core": ["javascript", "react", "node.js", "python", "sql"],
        "tools": ["git", "docker", "html", "css", "typescript"],
        "bonus": ["graphql", "aws", "ci/cd", "redis", "next.js"]
    },
    "data": {
        "core": ["python", "sql", "pandas", "numpy", "matplotlib"],
        "tools": ["jupyter", "git", "tableau", "excel", "statistics"],
        "bonus": ["spark", "airflow", "dbt", "power bi", "scikit-learn"]
    },
    "ml": {
        "core": ["python", "tensorflow", "pytorch", "scikit-learn", "deep learning"],
        "tools": ["pandas", "numpy", "git", "jupyter", "mlflow"],
        "bonus": ["hugging face", "langchain", "docker", "aws sagemaker", "cuda"]
    },
    "devops": {
        "core": ["docker", "kubernetes", "ci/cd", "linux", "aws"],
        "tools": ["terraform", "ansible", "git", "bash", "jenkins"],
        "bonus": ["prometheus", "grafana", "helm", "istio", "azure"]
    },
    "mobile": {
        "core": ["react native", "flutter", "swift", "kotlin", "firebase"],
        "tools": ["git", "xcode", "android studio", "figma", "rest api"],
        "bonus": ["redux", "graphql", "push notifications", "app store", "jest"]
    }
}

SECTION_CHECKLIST = [
    "education", "experience", "projects", "skills",
    "certifications", "achievements", "summary", "contact"
]

# ---------- HELPERS ----------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\.\+\#]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_text(file):
    text = ""
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
    elif file.filename.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text

def analyze_skills(resume_text, role):
    role_data = ROLE_SKILLS.get(role, {})
    all_skills = role_data.get("core", []) + role_data.get("tools", []) + role_data.get("bonus", [])
    cleaned = clean_text(resume_text)
    detected, missing = [], []
    for s in all_skills:
        if s in cleaned:
            detected.append(s)
        else:
            missing.append(s)
    core_detected = [s for s in role_data.get("core", []) if s in detected]
    core_missing = [s for s in role_data.get("core", []) if s in missing]
    return detected, missing, core_detected, core_missing

def calculate_score(resume_text, role, detected, all_skills, ats, jd_score):
    weights = {"skills": 0.35, "ats": 0.2, "sections": 0.2, "length": 0.1, "jd": 0.15}
    cleaned = clean_text(resume_text)

    skill_score = (len(detected) / len(all_skills) * 100) if all_skills else 0

    sections_found = sum(1 for s in SECTION_CHECKLIST if s in cleaned)
    section_score = (sections_found / len(SECTION_CHECKLIST)) * 100

    word_count = len(resume_text.split())
    if word_count < 200: length_score = 30
    elif word_count < 350: length_score = 60
    elif word_count < 700: length_score = 100
    elif word_count < 1200: length_score = 90
    else: length_score = 70

    jd_contribution = (jd_score or 50)

    total = (
        skill_score * weights["skills"] +
        ats * weights["ats"] +
        section_score * weights["sections"] +
        length_score * weights["length"] +
        jd_contribution * weights["jd"]
    )
    return round(total, 1)

def ats_check(resume_text, file_ext):
    score = 100
    warnings = []
    info = []

    if any(icon in resume_text for icon in ["★", "●", "→", "◆", "►"]):
        score -= 10
        warnings.append("Special symbols/icons detected — ATS parsers often skip these.")

    if resume_text.count("\n") < 10:
        score -= 15
        warnings.append("Very few line breaks — resume may lack proper structure.")

    word_count = len(resume_text.split())
    if word_count < 250:
        score -= 10
        warnings.append(f"Resume is only ~{word_count} words — aim for 400–800 words.")

    cleaned = clean_text(resume_text)
    if "education" not in cleaned:
        score -= 5
        warnings.append("No 'Education' section detected.")
    if "experience" not in cleaned and "work" not in cleaned:
        score -= 5
        warnings.append("No 'Experience' section detected.")

    if file_ext not in ["pdf", "docx"]:
        score -= 20
        warnings.append("Use PDF or DOCX format for best ATS compatibility.")

    if not any(char.isdigit() for char in resume_text):
        score -= 5
        warnings.append("No numbers found — quantify achievements (%, $, x, #).")

    if score >= 85:
        info.append("Email and contact info format looks clean.")
    if "github" in cleaned or "linkedin" in cleaned:
        info.append("Profile links detected — good for recruiter review.")

    return max(score, 0), warnings, info

def jd_match(resume_text, jd_text):
    if not jd_text or len(jd_text.strip()) < 20:
        return None, [], []
    cleaned_jd = clean_text(jd_text)
    cleaned_resume = clean_text(resume_text)
    stop_words = {"and","the","to","of","in","a","for","with","is","are","you","we","our","will","be","as","or","an","at","on","that","this","by","from","your","have","it","they","their","can","not","but","all","more","about","if","which"}
    jd_words = set(w for w in cleaned_jd.split() if len(w) > 3 and w not in stop_words)
    resume_words = set(cleaned_resume.split())
    matched = sorted(list(jd_words & resume_words))[:20]
    missing_raw = list(jd_words - resume_words)
    word_freq = Counter(cleaned_jd.split())
    missing = sorted(missing_raw, key=lambda w: -word_freq.get(w, 0))[:15]
    score = round((len(matched) / len(jd_words)) * 100, 1) if jd_words else 0
    return score, matched, missing

def check_sections(resume_text):
    cleaned = clean_text(resume_text)
    found = [s for s in SECTION_CHECKLIST if s in cleaned]
    missing = [s for s in SECTION_CHECKLIST if s not in cleaned]
    return found, missing

import google.generativeai as genai

def get_ai_insights(resume_text, role, missing_skills, jd_text=""):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    model = genai.GenerativeModel("gemini-1.5-flash")  # free tier model

    jd_note = f"\nJob Description provided:\n{jd_text[:800]}" if jd_text else ""

    prompt = f"""You are an expert resume coach. Analyze this resume for a {role} role.

Resume (first 1500 chars): {resume_text[:1500]}
Missing skills: {', '.join(missing_skills[:8])}{jd_note}

Return a JSON object with these exact keys:
{{
  "headline_feedback": "One sentence on the resume's biggest strength",
  "critical_fixes": ["fix1", "fix2", "fix3"],
  "quick_wins": ["win1", "win2", "win3"],
  "roadmap": [
    {{"week": "Week 1-2", "title": "Foundation fixes", "tasks": ["task1", "task2"]}},
    {{"week": "Week 3-4", "title": "Skill building", "tasks": ["task1", "task2"]}},
    {{"week": "Month 2", "title": "Portfolio & projects", "tasks": ["task1", "task2"]}},
    {{"week": "Month 3", "title": "Application ready", "tasks": ["task1", "task2"]}}
  ],
  "rewrite_tip": "One specific bullet point rewrite example showing before/after with a number metric",
  "interview_angle": "One unique talking point this candidate can highlight"
}}
Return only valid JSON, no markdown."""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)

# ---------- ROUTES ----------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", result=None)

@app.route("/analyze", methods=["POST"])
def analyze():
    resume = request.files.get("resume")
    role = request.form.get("job_role")
    jd = request.form.get("jd", "")

    if not resume or not role:
        return redirect(url_for("index"))

    resume_text = extract_text(resume)
    file_ext = resume.filename.split(".")[-1].lower()

    role_data = ROLE_SKILLS.get(role, {})
    all_skills = role_data.get("core", []) + role_data.get("tools", []) + role_data.get("bonus", [])

    detected, missing, core_detected, core_missing = analyze_skills(resume_text, role)
    ats, ats_warnings, ats_info = ats_check(resume_text, file_ext)
    jd_score, jd_matched, jd_missing = jd_match(resume_text, jd)
    sections_found, sections_missing = check_sections(resume_text)
    score = calculate_score(resume_text, role, detected, all_skills, ats, jd_score)
    word_count = len(resume_text.split())

    ai_insights = None
    try:
        ai_insights = get_ai_insights(resume_text, role, missing, jd)
    except Exception as e:
        print(f"AI insights error: {e}")

    result = {
        "score": score,
        "role": role,
        "word_count": word_count,
        "detected": detected,
        "missing": missing,
        "core_detected": core_detected,
        "core_missing": core_missing,
        "ats_score": ats,
        "ats_warnings": ats_warnings,
        "ats_info": ats_info,
        "jd_score": jd_score,
        "jd_matched": jd_matched,
        "jd_missing": jd_missing,
        "sections_found": sections_found,
        "sections_missing": sections_missing,
        "ai_insights": ai_insights
    }

    return render_template("index.html", result=result)

@app.route("/guide")
def guide():
    return render_template("guide.html")

if __name__ == "__main__":
    app.run(debug=True)
