from openai import OpenAI
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, send_file
from reportlab.pdfgen import canvas
import os
import PyPDF2
from docx import Document

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import db

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

# ---------------- APP SETUP ----------------
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'monuvijith726@gmail.com'
app.config['MAIL_PASSWORD'] = 'naoj urvq qxqx bijx'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ---------------- OPENAI (FIXED) ----------------
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- GLOBAL REPORT ----------------
latest_report = {
    "score": 0,
    "skills": [],
    "missing": [],
    "suggestions": []
}

# ---------------- MODELS ----------------
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

# ---------------- SKILLS ----------------
skills_list = [
    "python", "flask", "html", "css", "javascript",
    "sql", "machine learning", "git", "github",
    "api", "django", "react"
]

# ---------------- HELPERS ----------------
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
        return "Could not read PDF"
    return text.lower()


def extract_docx_text(docx_path):
    doc = Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text.lower()


def calculate_score(resume, job):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume, job])
    similarity = cosine_similarity(vectors)[0][1]
    return round(similarity * 100, 2)


def find_missing_skills(resume_text, job_description):
    missing = []
    for skill in skills_list:
        if skill in job_description.lower() and skill not in resume_text.lower():
            missing.append(skill)
    return missing


def extract_skills(resume_text):
    found = []
    for skill in skills_list:
        if skill in resume_text.lower():
            found.append(skill)
    return found


def skill_match(resume_skills, missing_skills):
    total = len(resume_skills) + len(missing_skills)
    if total == 0:
        return 0
    return round((len(resume_skills) / total) * 100, 2)


def generate_ai_feedback(resume_text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional ATS resume reviewer."},
            {"role": "user", "content": f"Review this resume and give improvement suggestions:\n\n{resume_text}"}
        ]
    )
    return response.choices[0].message.content

# ---------------- ROUTES ----------------
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

        return "Invalid Username or Password"

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


@app.route('/history')
@login_required
def history():
    data = Analysis.query.filter_by(username=current_user.username).all()
    return render_template('history.html', history=data)


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':

        file = request.files['resume']
        job_description = request.form['job_description']
        email = request.form['email']

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        if file.filename.endswith('.pdf'):
            resume_text = extract_text(filepath)
        elif file.filename.endswith('.docx'):
            resume_text = extract_docx_text(filepath)
        else:
            return "Only PDF and DOCX allowed"

        if resume_text == "Could not read PDF":
            return "Invalid PDF"

        score = calculate_score(resume_text, job_description)
        missing_skills = find_missing_skills(resume_text, job_description)
        detected_skills = extract_skills(resume_text)
        match_percent = skill_match(detected_skills, missing_skills)

        suggestions = []
        ai_feedback = generate_ai_feedback(resume_text)

        if score < 50:
            suggestions.append("Add more technical skills")
            suggestions.append("Improve projects section")

        if "github" not in resume_text:
            suggestions.append("Add GitHub profile")

        if "sql" not in resume_text:
            suggestions.append("Mention SQL skills")

        suggestions.append("Add measurable achievements")

        latest_report["score"] = score
        latest_report["skills"] = detected_skills
        latest_report["missing"] = missing_skills
        latest_report["suggestions"] = suggestions

        analysis = Analysis(
            username=current_user.username,
            score=score,
            skills=", ".join(detected_skills)
        )

        db.session.add(analysis)
        db.session.commit()

        if email:
            msg = Message(
                'ATS Resume Report',
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )

            msg.body = f"""
ATS Resume Report

Score: {score}%

Detected Skills:
{", ".join(detected_skills)}

Missing Skills:
{", ".join(missing_skills)}

Suggestions:
{", ".join(suggestions)}
"""

            mail.send(msg)

        return render_template(
            'result.html',
            score=score,
            missing_skills=missing_skills,
            detected_skills=detected_skills,
            suggestions=suggestions,
            match_percent=match_percent,
            ai_feedback=ai_feedback
        )

    return render_template('index.html')


@app.route('/download_report')
@login_required
def download_report():
    pdf_path = "ATS_Report.pdf"
    c = canvas.Canvas(pdf_path)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(120, 800, "AI Resume Analyzer Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, 760, f"User: {current_user.username}")

    score = latest_report["score"]
    skills = latest_report["skills"]
    missing = latest_report["missing"]
    suggestions = latest_report["suggestions"]

    c.drawString(50, 720, f"Score: {score}%")

    y = 680
    for section, items in [
        ("Skills", skills),
        ("Missing Skills", missing),
        ("Suggestions", suggestions)
    ]:
        c.drawString(50, y, section)
        y -= 20
        for i in items:
            c.drawString(70, y, f"- {i}")
            y -= 20

    c.save()
    return send_file(pdf_path, as_attachment=True)


@app.route('/admin')
@login_required
def admin():

    if current_user.username != "admin":
        return "Access Denied"

    total_users = User.query.count()
    total_analysis = Analysis.query.count()
    all_analysis = Analysis.query.all()

    scores = [a.score for a in all_analysis]

    if scores:
        plt.figure(figsize=(6,4))
        plt.plot(scores)
        plt.title("ATS Score Analytics")
        plt.xlabel("Analysis Count")
        plt.ylabel("ATS Score")
        plt.savefig("static/chart.png")
        plt.close()

    return render_template(
        'admin.html',
        total_users=total_users,
        total_analysis=total_analysis,
        all_analysis=all_analysis
    )


# ---------------- DB INIT ----------------
with app.app_context():
    db.create_all()

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)