# Backend – Automated Reporting and Insight Generation Tool

This is the backend component of the W10A_DONUT Capstone Project, powered by **Python** and **Flask**.

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                 # Blueprint route handlers (upload, report, config, email)
│   ├── services/            # Business logic (data validation, cleaning, visualization, etc.)
│   ├── models/              # (Optional) ORM models
│   ├── utils/               # Utility functions
│   └── __init__.py          # Flask app factory
├── tests/                   # Backend unit and integration tests
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point to start the backend server
└── .env.example             # Example of environment variable config
```

---

## 🔧 Prerequisites

- Python 3.8+
- `pip` installed
- (Recommended) Virtual environment tools: `venv` or `virtualenv`

---

## ⚙️ Setup Instructions

1. **Navigate to the backend folder**:

```bash
cd backend
```

2. **Create a virtual environment (optional but recommended)**:

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows PowerShell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Server

By default, the backend runs on http://127.0.0.1:5050. To start:

```bash
python run.py
```

If port 5050 is occupied, change it using:

```bash
# macOS/Linux
export FLASK_PORT=5070

# Windows PowerShell
$env:FLASK_PORT=5070
```

---

## 🔍 Testing the API

Visit this in your browser or Postman:

```
http://127.0.0.1:5050/health
```

Expected response:

```json
{
  "status": "healthy",
  "message": "Reporting service is running"
}
```

---

## 👥 Contributors

- **Scrum Master**: Binglin Yan

UNSW COMP3900/9900 Capstone Project