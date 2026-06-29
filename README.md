# 🚀 HirOps – AI Resume Evaluation & Hiring Assistance System

### **An AI-Powered Recruitment Platform for Intelligent Resume Screening & Hiring**

*Built with Python Flask • Supabase • OpenAI • HTML • CSS • JavaScript*

## 📖 Overview

**HirOps** is an AI-powered web application developed to modernize the recruitment process by automating resume evaluation and candidate screening. Instead of manually reviewing hundreds of resumes, recruiters can use HirOps to analyze resumes against job requirements using Artificial Intelligence and identify the most suitable candidates efficiently.

The system provides dedicated modules for **Candidates**, **Recruiters**, and **Administrators**, allowing complete management of the hiring workflow from job posting to AI-based candidate evaluation and ranking.

This project was developed as my **Final Year BCA Project** with a focus on combining AI with modern web technologies to build a practical recruitment solution.

---

# ✨ Key Features

### 👤 Candidate Module

* Secure Registration & Login
* Resume Upload (PDF/DOCX)
* Browse Available Jobs
* Apply for Jobs
* AI Resume Evaluation
* View Evaluation Results

### 🏢 Recruiter Module

* Recruiter Authentication
* Create & Manage Job Posts
* View Candidate Applications
* Candidate Comparison
* AI-based Candidate Evaluation
* Candidate Ranking Dashboard

### 🛠 Admin Module

* Manage Users
* Manage Recruiters
* Manage Job Listings
* Monitor System Activities
* View Recruitment Analytics

### 🤖 AI Features

* Resume Parsing
* Skill Extraction
* Job Requirement Matching
* Candidate Scoring
* AI-generated Evaluation
* Intelligent Resume Analysis

---

# 🏗 System Architecture

```
Candidate / Recruiter / Admin
            │
            ▼
HTML • CSS • JavaScript
            │
            ▼
      Python Flask
            │
 ┌──────────┼──────────┐
 │          │          │
Authentication  Job Management
Resume Upload   AI Evaluation
Analytics       Dashboard
            │
     ┌──────┴─────────┐
     │                │
Supabase DB      OpenAI API
     │                │
     └──────┬─────────┘
            ▼
   Evaluation Results
            │
            ▼
     Candidate Ranking
```

---

# 🛠 Tech Stack

## Frontend

* HTML5
* CSS3
* JavaScript

## Backend

* Python
* Flask

## Database

* Supabase (PostgreSQL)

## Artificial Intelligence

* OpenAI API

## Tools

* Visual Studio Code
* Git
* GitHub

---

# 📂 Project Structure

```
HirOps
│
├── app.py
│
├── routes
│   ├── auth.py
│   ├── jobs.py
│   ├── candidates.py
│   ├── ai_routes.py
│   ├── analytics.py
│
├── services
│   ├── gpt_service.py
│   ├── resume_parser.py
│   ├── scoring_service.py
│   ├── dashboard_recruiter.py
│   ├── supabase_client.py
│
├── templates
│
├── static
│   ├── css
│   ├── js
│   └── images
│
├── uploads
│
└── requirements.txt
```

---

# 🔄 Workflow

```
Candidate Login
      │
      ▼
Upload Resume
      │
      ▼
Resume Parsing
      │
      ▼
OpenAI Evaluation
      │
      ▼
Skill Matching
      │
      ▼
Candidate Score
      │
      ▼
Store Result
      │
      ▼
Recruiter Dashboard
```

---

# 📊 Core Modules

* Authentication Module
* Job Requirement Module
* Resume Upload Module
* AI Resume Evaluation Module
* Candidate Ranking Module
* Dashboard & Analytics Module
* Admin Module

---

# 🧠 AI Resume Evaluation Process

1. Candidate uploads a resume.
2. Resume content is extracted.
3. Job requirements are retrieved.
4. Resume data is sent to the OpenAI API.
5. AI analyzes skills and experience.
6. Candidate score is generated.
7. Results are stored in Supabase.
8. Recruiters view ranked candidates.

---

# 🎯 Objectives

* Automate resume screening
* Reduce manual recruitment effort
* Improve candidate-job matching
* Provide intelligent hiring assistance
* Generate AI-powered evaluation reports

---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/HirOps-AI-Resume-Evaluation-Hiring-Assistance-System.git
```

Move into the project folder

```bash
cd HirOps-AI-Resume-Evaluation-Hiring-Assistance-System
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

---

# 📸 Screenshots

Add screenshots here after uploading them.

* Login Page
* Candidate Dashboard
* Resume Upload
* Job Listing
* AI Evaluation
* Recruiter Dashboard
* Candidate Comparison
* Analytics Dashboard

---

# 🔮 Future Enhancements

* Resume recommendations
* LinkedIn integration
* Interview scheduling
* Email notifications
* Mobile application
* Advanced analytics
* AI-powered interview assistant

---

# 👨‍💻 Developer

**Mohammed Sahal Bin Zubair**

Bachelor of Computer Applications

Python Developer | AI Enthusiast | Full Stack Developer

---

# ⭐ Support

If you found this project useful, consider giving the repository a **⭐ Star**.

It motivates me to continue building and improving open-source projects.

---

## 📜 License

This project is developed for educational and academic purposes as a Final Year BCA Project.
