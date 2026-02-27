```
README.md
```

---

# 🚀 KLH Hackathon – Smart Prescription OCR & AI Analyzer

> 🏥 AI-powered Prescription OCR + NLP + Risk Analysis System
> Transforming handwritten prescriptions into structured medical insights.

---

## 📌 Problem Statement

Manual prescription handling leads to:

* ❌ Misinterpretation of handwritten text
* ❌ Medicine entry errors
* ❌ Fraud in insurance claims
* ❌ No structured digital records

We built a system that converts prescriptions into structured, analyzable data using AI.

---

## 💡 Our Solution

This project:

1. 📸 Takes prescription images
2. 🔍 Extracts text using OCR
3. 🧠 Processes text using Gemini AI
4. 📊 Converts it into structured JSON
5. ⚠️ Generates risk insights
6. 🖥️ Displays results via a Streamlit dashboard

---

## 🏗️ System Architecture

```
User Upload
     ↓
OCR Engine (Tesseract / Google Vision)
     ↓
Extracted Raw Text
     ↓
Gemini AI Processing
     ↓
Structured JSON Output
     ↓
Risk Analysis Engine
     ↓
Dashboard Display
```

---

## 🔄 Workflow

### 1️⃣ Image Upload

User uploads prescription image (`.jpg / .png`).

---

### 2️⃣ OCR Processing

* Extracts text from handwritten/printed prescriptions.
* Uses Tesseract or Google Vision API.

Output:

```
Raw extracted medical text
```

---

### 3️⃣ AI Structuring (Gemini API)

Gemini processes raw OCR text and converts it into:

```json
{
  "patient_name": "",
  "age": "",
  "diagnosis": "",
  "medicines": [],
  "dosage": [],
  "tests": []
}
```

---

### 4️⃣ Risk Analysis

System checks for:

* 🚨 High-risk diseases
* 🚨 Duplicate medicines
* 🚨 Long-term chronic patterns
* 🚨 Insurance fraud indicators

---

### 5️⃣ Dashboard Output

User sees:

* 📋 Structured prescription
* 📊 Risk score
* ⚠️ Alerts
* 📁 JSON export option

---

## 🛠️ Tech Stack

| Component        | Technology                |
| ---------------- | ------------------------- |
| 🖥️ Frontend     | Streamlit                 |
| 🔍 OCR           | Tesseract / Google Vision |
| 🤖 AI Processing | Gemini API                |
| 🐍 Backend       | Python                    |
| 📦 Data Format   | JSON                      |

---

## ⚙️ Installation Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/257r1a05j4-code/klhhackathon.git
cd klhhackathon
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Setup Environment Variables

Create a `.env` file:

```
GEMINI_API_KEY=your_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_json
```

⚠️ Do NOT upload this file to GitHub.

---

### 5️⃣ Run the App

```bash
streamlit run app.py
```

---

## 📊 Example Output

✔️ Extracted Patient Details
✔️ Medicines & Dosage
✔️ Diagnosis
✔️ Risk Score
✔️ JSON Structured Data

---

## 🎯 Key Features

✅ AI-powered prescription understanding
✅ Automated medical structuring
✅ Fraud detection assistance
✅ Risk scoring system
✅ Exportable JSON
✅ Easy-to-use dashboard

---

## 🔐 Security Measures

* Environment variables used for API keys
* `.gitignore` protects sensitive files
* No credentials stored in repository

---

## 🌟 Future Improvements

* 🧾 Multi-language prescription support
* 🏥 Hospital database integration
* 📱 Mobile app support
* 📈 Predictive analytics for chronic diseases

---

## 👨‍💻 Team

Built for **KLH Hackathon 2026** 🚀
Passionate about AI in Healthcare 💙

---

## 📬 Contact

For demo or queries:
📧 Contact via GitHub Issues

---

# ⭐ If you like this project, give it a star!

---
