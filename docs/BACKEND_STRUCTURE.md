# Backend Structure Documentation
## COMP3900/9900 Project #14 - Automated Reporting and Insight Generation Tool
**Team: W10A_DONUT**

---

## 📁 Project Structure Overview

Our backend follows a **modular Flask application structure** that separates concerns and makes the codebase maintainable and scalable. Here's what each directory and file does:

```
backend/
├── app/                    # Main application package
│   ├── __init__.py        # Flask app factory and configuration
│   ├── config.py          # Configuration settings (dev, prod, test)
│   ├── api/               # REST API endpoints
│   ├── services/          # Business logic layer
│   ├── models/            # Data models and schemas
│   └── utils/             # Helper functions and utilities
├── tests/                 # Unit and integration tests
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── README.md             # Setup and usage instructions
└── .env.example          # Environment variables template
```

---

## 🏗️ Architecture Pattern

We're using a **3-layer architecture** as outlined in our project proposal:

1. **API Layer** (`app/api/`) - Handles HTTP requests/responses
2. **Service Layer** (`app/services/`) - Contains business logic
3. **Data Layer** (file-based storage) - Manages data persistence

---

## 📂 Detailed Directory Breakdown

### `/app/` - Main Application Package

#### `__init__.py`
- **Purpose**: Flask application factory
- **Contains**: 
  - Flask app initialization
  - Blueprint registration
  - CORS configuration
  - Error handlers

#### `config.py`
- **Purpose**: Configuration management
- **Contains**:
  - Environment-specific settings
  - File upload limits
  - Email SMTP settings
  - Anomaly detection thresholds

### `/app/api/` - REST API Endpoints

This directory contains our **API endpoints** that the desktop GUI will communicate with:

#### `upload.py`
- **Endpoints**: 
  - `POST /api/upload` - File upload and validation
- **Responsibilities**:
  - Accept files (US-1.1)
  - Validate file structure and headers (US-1.2)
  - Return upload confirmation (US-1.3)
  - Log upload events (US-1.4)

#### `report.py`
- **Endpoints**:
  - `POST /api/generate-report` - Trigger report generation
  - `GET /api/reports/<filename>` - Retrieve generated reports
- **Responsibilities**:
  - Coordinate the report generation process
  - Return PDF file locations (US-3.1, US-3.3)

#### `config.py`
- **Endpoints**:
  - `GET /api/config` - Get current settings
  - `PUT /api/config` - Update configuration
- **Responsibilities**:
  - Manage anomaly thresholds (US-6.1)
  - Handle monitored metrics configuration (US-6.2)

#### `email.py`
- **Endpoints**:
  - `POST /api/send-email` - Send report via email
  - `GET /api/email-recipients` - Get recipient list
  - `PUT /api/email-recipients` - Update recipient list
- **Responsibilities**:
  - Email delivery functionality (US-7.1)
  - Recipient management (US-5.6)

### `/app/services/` - Business Logic Layer

This is where the **core functionality** lives:

#### `validation.py`
- **Purpose**: File validation logic
- **Functions**:
  - `validate_file_format()` - Check file type and size
  - `validate_headers()` - Verify required columns exist
  - `validate_data_types()` - Ensure data integrity

#### `cleaning.py`
- **Purpose**: Data cleaning and transformation
- **Functions**:
  - `fill_missing_values()` - Handle empty cells (US-2.1)
  - `standardize_dates()` - Convert to MM-YYYY format (US-2.2)
  - `log_changes()` - Track what was modified (US-2.3)
  - `flag_altered_rows()` - Mark changed data (US-2.4)

#### `visualization.py`
- **Purpose**: Chart generation for reports
- **Functions**:
  - `generate_kpi_charts()` - Create bar, line, pie charts
  - `create_trend_analysis()` - Monthly comparison visuals
  - `format_chart_data()` - Prepare data for visualization

#### `pdf_generator.py`
- **Purpose**: PDF report creation
- **Functions**:
  - `generate_report()` - Main report creation (US-3.1)
  - `add_metadata()` - Include file info and timestamps (US-3.2)
  - `save_with_naming_convention()` - Use MM-YYYY_Report.pdf format

#### `anomaly_detection.py`
- **Purpose**: Rule-based anomaly detection
- **Functions**:
  - `detect_anomalies()` - Compare with previous month (US-4.1)
  - `flag_significant_changes()` - Highlight >30% changes (US-4.2)
  - `generate_explanations()` - Create plain language summaries (US-4.4)

#### `email_service.py`
- **Purpose**: Email functionality
- **Functions**:
  - `send_report()` - Email PDF attachment (US-7.2)
  - `validate_email_config()` - Check SMTP settings
  - `handle_delivery_errors()` - Error reporting (US-7.3)

### `/app/models/` - Data Models

- **Purpose**: Define data structures and validation schemas
- **Contents**: 
  - Report metadata models
  - Configuration schemas
  - API request/response models

### `/app/utils/` - Utility Functions

- **Purpose**: Common helper functions
- **Contents**:
  - Logging utilities
  - File handling helpers
  - Date/time formatting functions

---

## 🔧 Key Files

### `run.py`
- **Purpose**: Application entry point
- **Usage**: `python run.py` to start the Flask server
- **Configuration**: Reads environment variables and starts the app

### `requirements.txt`
- **Purpose**: Python dependencies list
- **Key libraries**:
  - Flask (web framework)
  - pandas (data processing)
  - matplotlib/seaborn (visualization)
  - WeasyPrint (PDF generation)
  - smtplib (email functionality)

### `.env.example`
- **Purpose**: Template for environment variables
- **Contains**:
  - SMTP server settings
  - File upload paths
  - Security configurations

---

## 🚀 Development Workflow

### For Sprint 1 (June 21 - July 5):
1. **Start with**: `/app/api/upload.py` and `/app/services/validation.py`
2. **Then build**: `/app/services/cleaning.py` and `/app/services/pdf_generator.py`
3. **Finally add**: `/app/api/email.py` and `/app/services/email_service.py`

### Testing Strategy:
- 

**Questions?** Reach out to the team on our project communication channels!