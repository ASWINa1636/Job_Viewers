### Job Viewers

## Overview

Job Viewers is a web-based application that allows users to upload their resumes, extract relevant information, and get job recommendations based on their skills. The platform also includes a job posting system and user authentication.

## Features

Resume Upload & Parsing: Supports PDF, DOCX, and images with OCR.

Skill Extraction: Uses NLP (spaCy, PhraseMatcher) to extract skills.

User Authentication: Signup, login, and logout system.

Database: SQLite for job-related data and user authentication.

## Tech Stack

Backend: Flask (Python)

Frontend: HTML, CSS, JavaScript (Jinja templates)

Database: SQLite (by own)

NLP: spaCy, PhraseMatcher

File Processing: PyMuPDF, python-docx, Tesseract OCR

## Usage

Upload your resume to get skill-based job recommendations.

Search for jobs based on skills extracted from your resume.

Post job listings if you're an employer.

Sign up & log in for job posts.

## Contributing

Feel free to submit pull requests or open issues if you find bugs or have feature requests.

## License

MIT License
