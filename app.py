import os
import PyPDF2
from docx import Document

from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------- APP SETUP ---------------- #

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- DATABASE ---------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    score = db.Column(db.Float)
    skills = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- CORE LOGIC ---------------- #

skills_list = [
    "python", "flask", "html", "css", "javascript",
    "sql", "machine learning", "git", "github",
    "api", "django", "react"
]


def extract_text(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
    except:
        return ""
    return text.lower()


def extract_docx_text(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs]).lower()


def calculate_score(resume, job):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume, job])
    return round(cosine_similarity(vectors)[0][1] * 100, 2)


def extract_skills(text):
    return [s for s in skills_list if s in text.lower()]


def find_missing_skills(resume, job):
    return [
        s for s in skills_list
        if s in job.lower() and s not in resume.lower()
    ]


def skill_match(resume_skills, missing_skills):
    total = len(resume_skills) + len(missing_skills)
    if total == 0:
        return 0
    return round((len(resume_skills) / total) * 100, 2)


# ---------------- SIMPLE AI (RULE BASED) ---------------- #

def generate_ai_feedback(text):
    feedback = []

    if "project" not in text:
        feedback.append("Add more project details.")

    if "github" not in text:
        feedback.append("Include GitHub profile.")

    if "internship" not in text:
        feedback.append("Add internship experience.")

    if len(text.split()) < 200:
        feedback.append("Resume is too short.")

    return "\n".join(feedback) if feedback else "Good resume structure."


# ---------------- ROUTES ---------------- #

latest_report = {}


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            login_user(user)
            return redirect('/dashboard')

        return "Invalid credentials"

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    global latest_report

    if request.method == 'POST':

        file = request.files['resume']
        job_description = request.form['job_description']
        email = request.form['email']

        path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)

        if file.filename.endswith('.pdf'):
            resume_text = extract_text(path)
        elif file.filename.endswith('.docx'):
            resume_text = extract_docx_text(path)
        else:
            return "Only PDF or DOCX allowed"

        score = calculate_score(resume_text, job_description)
        detected = extract_skills(resume_text)
        missing = find_missing_skills(resume_text, job_description)
        match = skill_match(detected, missing)
        ai_feedback = generate_ai_feedback(resume_text)

        latest_report = {
            "score": score,
            "skills": detected,
            "missing": missing,
            "suggestions": [ai_feedback]
        }

        analysis = Analysis(
            username=current_user.username,
            score=score,
            skills=", ".join(detected)
        )

        db.session.add(analysis)
        db.session.commit()

        return render_template(
            "result.html",
            score=score,
            detected_skills=detected,
            missing_skills=missing,
            match_percent=match,
            ai_feedback=ai_feedback
        )

    return render_template("index.html")


@app.route('/download_report')
@login_required
def download_report():
    pdf_path = "report.pdf"
    c = canvas.Canvas(pdf_path)

    c.drawString(100, 800, "AI Resume Report")
    c.drawString(100, 780, f"User: {current_user.username}")
    c.drawString(100, 760, f"Score: {latest_report.get('score', 0)}")

    c.save()
    return send_file(pdf_path, as_attachment=True)


# ---------------- INIT DB ---------------- #

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)