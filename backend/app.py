import os
import sqlite3
import fitz  # PyMuPDF for PDF extraction
import json  # Add this import to parse JSON skill lists
import pytesseract  # OCR for images
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import docx
import spacy
from spacy.matcher import PhraseMatcher
from flask import Flask, render_template, request, redirect, url_for, session, flash , g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io
# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize Flask app
app = Flask(__name__,  template_folder="templates")
app.config['UPLOAD_FOLDER'] = "uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.secret_key = '98745632221478632156321489625'  # Change this in production
AUTH_DATABASE_PATH = r"D:\job_seeker\backend\security.db"  # Stores user authentication data
# Path to SQLite3 database
DATABASE_PATH = r"D:\job_seeker\backend\database.db"  # Use raw string format

def init_db():
    # Auth Database (Users)
    conn = sqlite3.connect(AUTH_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

    # Job Database (Jobs)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            required_skills TEXT NOT NULL,  -- will store JSON string
            salary TEXT NOT NULL,
            date_posted TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(title, company, location),  -- Ensures no duplicate job at the same company & location
            FOREIGN KEY (user_id) REFERENCES users(id)
        )"""
    )
    conn.commit()
    conn.close()

def get_db():
    try:
        db = getattr(g, "_database", None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE_PATH)
            db.row_factory = sqlite3.Row
        return db
    except Exception as e:
        print("Database Connection Error:", e)
        return None

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}

# Comprehensive list of skills
SKILLS = [
    "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "Go", "Swift", "Kotlin", "TypeScript", "PHP", "Rust",
    "Scala", "Perl", "Haskell", "Lua", "Linux", "Windows", "macOS", "UNIX", "MATLAB", "Power Systems", "HTML", 
    "CSS", "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "Spring Boot", "ASP.NET", "Laravel",
    "Machine Learning", "Deep Learning", "Data Science", "TensorFlow", "PyTorch", "Keras", "Pandas", "NumPy", 
    "Scikit-Learn", "R", "Matplotlib", "Seaborn", "OpenAI API", "Natural Language Processing", "Computer Vision",
    "Big Data", "SQL", "PostgreSQL", "MongoDB", "Firebase", "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
    "Ethical Hacking", "Penetration Testing", "Cryptography", "Network Security", "SOC Analyst", "Malware Analysis",
    "Reverse Engineering", "CI/CD", "Jenkins", "Terraform", "Ansible", "Git", "GitHub Actions", "GitLab CI", 
    "Bash Scripting", "PowerShell", "Agile", "Scrum", "Kanban", "JIRA", "Trello", "Confluence", "PCB Design", 
    "Web Development", "Mobile Development", "Word", "Excel", "PowerPoint", "Outlook", "Tableau", "Power BI", 
    "Apache Spark", "Hadoop", "Kafka", "Elasticsearch", "GraphQL", "REST APIs", "SOAP", "Microservices", 
    "DevOps", "System Administration", "Virtualization", "VMware", "Hyper-V", "Cloud Security", "IoT", 
    "Embedded Systems", "Arduino", "Raspberry Pi", "Blockchain", "Solidity", "UI/UX Design", "Figma", "Adobe XD", 
    "Photoshop", "Illustrator", "Blender", "3D Modeling", "Game Development", "Unity", "Unreal Engine", "OpenGL", 
    "WebAssembly", "Quantum Computing", "Statistics", "Probability", "Linear Algebra", "Data Visualization", 
    "ETL Processes", "Data Warehousing", "Snowflake", "Redshift", "DynamoDB", "Cassandra", "Neo4j", "Redis", 
    "Load Balancing", "NGINX", "Apache", "Incident Response", "Forensic Analysis", "Threat Hunting", 
    "Cybersecurity Frameworks", "NIST", "ISO 27001", "GDPR Compliance", "Project Management", "PMP", "Lean Six Sigma", 
    "Technical Writing", "Public Speaking", "Team Leadership", "Conflict Resolution", "Time Management", 
    "Customer Relationship Management (CRM)", "Salesforce", "SAP", "ERP Systems", "Supply Chain Management", 
    "Digital Marketing", "SEO", "SEM", "Content Management Systems (CMS)", "WordPress", "Shopify", "Magento", 
    "Augmented Reality (AR)", "Virtual Reality (VR)", "Robotics", "ROS (Robot Operating System)", "PLC Programming", 
    "AutoCAD", "SolidWorks", "Finite Element Analysis (FEA)", "Computational Fluid Dynamics (CFD)", "Simulink", 
    "VLSI Design", "Verilog", "VHDL", "FPGA Programming", "Signal Processing", "Image Processing", "Audio Engineering", 
    "Penetration Testing Tools (Metasploit, Burp Suite)", "Wireshark", "Nmap", "Splunk", "SIEM", "Log Analysis", 
    "Chaos Engineering", "Site Reliability Engineering (SRE)", "Monitoring Tools (Prometheus, Grafana)", 
    "Version Control Systems", "Subversion (SVN)", "Mercurial", "Test Automation", "Selenium", "Cypress", 
    "Postman", "Unit Testing", "Integration Testing", "Performance Testing", "Load Testing", "Stress Testing", 
    "Behavior-Driven Development (BDD)", "Test-Driven Development (TDD)", "Pair Programming", "Code Review", 
    "Documentation", "API Design", "OAuth", "JWT", "Microfrontend", "Serverless Architecture", "Edge Computing", 
    "Bioinformatics", "Genomics", "Proteomics", "Molecular Modeling", "Chemoinformatics", "Financial Modeling", 
    "Risk Analysis", "Algorithm Design", "Data Structures", "Competitive Programming", "Parallel Computing", 
    "Distributed Systems", "Graph Theory", "Optimization", "Simulation", "Forecasting", "Econometrics", 
    "Geospatial Analysis", "GIS (Geographic Information Systems)", "Remote Sensing", "Satellite Imagery Analysis", 
    "Drone Technology", "Aeronautical Engineering", "Mechanical Design", "Thermodynamics", "Materials Science", 
    "Nanotechnology", "Renewable Energy Systems", "Solar Technology", "Wind Energy", "Battery Systems", 
    "Electrical Engineering", "Control Systems", "Power Electronics", "RF Engineering", "Antenna Design", 
    "Satellite Communications", "5G Technology", "Network Protocols", "TCP/IP", "DNS Management", "VPN Configuration", 
    "Customer Support", "Technical Support", "ITIL", "ServiceNow", "Help Desk Management", "Change Management", 
    "Disaster Recovery", "Business Continuity Planning", "Stakeholder Management", "Negotiation", "Critical Thinking", 
    "Problem Solving", "Emotional Intelligence", "Adaptability", "Cross-Functional Collaboration", "Mentoring", 
    "Training & Development", "Instructional Design", "E-Learning Development", "LMS (Learning Management Systems)"
]

# Initialize PhraseMatcher for skill extraction
phrase_matcher = PhraseMatcher(nlp.vocab)
patterns = [nlp(skill) for skill in SKILLS]
phrase_matcher.add("SKILLS", None, *patterns)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    text = ""
    doc = fitz.open(filepath)
    for page in doc:
        text += page.get_text("text")
    return text

def extract_text_from_docx(filepath):
    """Extracts text from .docx files, including images using OCR if necessary."""
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # OCR on images inside .docx
        for rel in doc.part.rels:
            if "image" in doc.part.rels[rel].target_ref:
                image_data = doc.part.rels[rel].target_part.blob
                image = Image.open(io.BytesIO(image_data))
                text += pytesseract.image_to_string(image) + "\n"
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
    return text.strip()

def extract_resume_text(filepath, ext):
    if ext == "docx":
        return extract_text_from_docx(filepath)
    return ""  # Return empty if format is not supported

def extract_text_from_image(filepath):
    image = Image.open(filepath)
    return pytesseract.image_to_string(image)

def extract_resume_text(filepath, ext):
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext == "docx":
        return extract_text_from_docx(filepath)
    elif ext in {"png", "jpg", "jpeg"}:
        return extract_text_from_image(filepath)
    return ""

def extract_skills(text):
    doc = nlp(text)
    skills = set()
    
    # Use PhraseMatcher to find skills
    matches = phrase_matcher(doc)
    for match_id, start, end in matches:
        skills.add(doc[start:end].text)
    
    return list(skills)


def find_jobs_from_database(skills):
    if not skills:
        print("No skills extracted, skipping job search.")
        return []

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Fetch jobs from the database
        cursor.execute("SELECT id, title, company, location, description, required_skills, salary, date_posted FROM jobs")
        jobs = cursor.fetchall()
        conn.close()

        print("\n All Jobs in Database:")
        for job in jobs:
            print(f"ID: {job[0]}, Title: {job[1]}, Required Skills: {job[5]}")

        # Convert extracted skills to lowercase for case-insensitive matching
        skills = [skill.lower().strip() for skill in skills]
        print("\n Extracted Skills (Cleaned):", skills)  # Debugging skills list

        matched_jobs = []
        for job in jobs:
            try:
                job_skills = json.loads(job[5])  # Convert JSON string to list
                job_skills = [skill.lower().strip() for skill in job_skills]  # Normalize
            except (json.JSONDecodeError, TypeError):
                job_skills = [skill.strip().lower() for skill in job[5].split(",")]  #  Fallback to comma-separated values

                print(f" Warning: Job skills format issue for job ID {job[0]}")
                continue  # Skip this job if parsing fails

            print(f"\n Checking Job: {job[1]}")
            print(f" - Job Skills (DB): {job_skills}")
            print(f" - Candidate Skills: {skills}")

            #  Check if at least one skill matches
            if any(skill in job_skills for skill in skills):
                print(" Match Found!")
                matched_jobs.append({
                    "id": job[0],
                    "title": job[1],
                    "company": job[2],
                    "location": job[3],
                    "description": job[4],
                    "required_skills": job_skills,  #  Show as a proper list
                    "salary": job[6],
                    "date_posted": job[7]
                })
            else:
                print(" No Match - Check Formatting in DB")

        print("\n Final Matched Jobs:", matched_jobs)  # Debugging output
        return matched_jobs
    
    except Exception as e:
        print("Database Error:", e)
        return []
    
@app.route("/")
def index():
    return render_template("index.html")  # This serves index.html from 'templates' folder

@app.route("/search", methods=["GET"])
def search_jobs():
    skills = request.args.get("skills", "")  # Get skills from query parameters
    
    
    skills_list = [skill.strip() for skill in skills.split(",")]  # Convert to list
    jobs = find_jobs_from_database(skills_list)  # Find matching jobs from DB

    # Ensure DATABASE_PATH contains job data (replace with actual dataset)
    return jsonify({"job_recommendations": jobs})  # Return JSON response



@app.route("/upload", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    ext = filename.rsplit('.', 1)[1].lower()
    text = extract_resume_text(filepath, ext)
    skills = extract_skills(text)
    jobs = find_jobs_from_database(skills)

    return jsonify({
        "extracted_skills": skills,
        "job_recommendations": jobs
    })

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(AUTH_DATABASE_PATH)
            cursor = conn.cursor()
            
            #  Check if user exists before inserting
            cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash("Email or username already exists!", "danger")
                return redirect(url_for('signup'))

            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, hashed_password))
            conn.commit()
            conn.close()

            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f"Database error: {e}", "danger")
    
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])

def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect(AUTH_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials, try again.", "danger")
    
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route("/add_job", methods=["GET", "POST"])
def add_job():
    if "user_id" not in session:
        return redirect(url_for("login"))  # Redirect if not logged in

    if request.method == "POST":
        try:
            title = request.form["title"].strip()
            company = request.form["company"].strip()
            location = request.form["location"].strip()
            description = request.form["description"].strip()
            required_skills = request.form["required_skills"].strip()
            salary = request.form["salary"].strip()
            date_posted = datetime.now().strftime("%Y-%m-%d")  # Store the current date
            user_id = session["user_id"]  #  Ensure user_id is included

            #  Convert skills input (comma-separated) into JSON
            skills_list = [skill.strip() for skill in required_skills.split(",")]
            required_skills_json = json.dumps(skills_list)

            db = get_db()
            cursor = db.cursor()

            #  Check if the job already exists
            cursor.execute(
                "SELECT * FROM jobs WHERE title = ? AND company = ? AND location = ?",
                (title, company, location),
            )
            existing_job = cursor.fetchone()

            if existing_job:
                return jsonify({"error": "Job already exists!"}), 400  # Prevent duplicate jobs
            
            #  Corrected SQL query (including user_id)
            cursor.execute(
                """
                INSERT INTO jobs (title, company, location, description, required_skills, salary, date_posted, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, company, location, description, required_skills_json, salary, date_posted, user_id),
            )

            db.commit()
            
            return jsonify({"message": "Job added successfully!"}), 201

        except Exception as e:
            print("Error:", e)  # Debugging
            return jsonify({"error": str(e)}), 500  # Send error message back

    return render_template("add_job.html")

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

