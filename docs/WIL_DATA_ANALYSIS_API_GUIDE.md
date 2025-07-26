# WIL Data Analysis API Guide

**Purpose**: Generate WIL data analysis charts and statistics for PDF reports and frontend dashboards.

## 🚀 Quick Start

### Prerequisites
- Backend service: `cd backend && python run.py`
- Endpoint: `http://localhost:5050`
- Data file: CSV, XLSX, or XLS format

### Basic Workflow
1. **Upload**: POST file to `/upload` → get `file_id`
2. **Analyze**: POST to `/analyze/pdf-ready/<file_id>` → get `analysis_id`
3. **Monitor**: Poll `/status/<analysis_id>` until complete
4. **Download**: GET `/download/<analysis_id>` for ZIP results
5. **Use**: Generate PDF with ReportLab or display in frontend

## 🔄 Key Features

- **Optimized Workflow**: Upload once, analyze multiple times with file_id
- **No Duplicate Uploads**: Eliminates redundant file transmission
- **Async Processing**: Non-blocking analysis with progress tracking
- **Result Persistence**: Download results multiple times using `analysis_id`
- **High-Quality Charts**: 300 DPI PNG images optimized for PDF embedding
- **Ready-to-Use Data**: Pre-formatted JSON for direct template integration

## 📊 API Endpoints

### Upload Endpoints

| Method | Endpoint | Purpose |
|--------|----------|----------|
| POST | `/upload` | Upload file and get file_id |
| GET | `/upload/<file_id>/info` | Get file information |
| GET | `/upload/files` | List all uploaded files |

### Analysis Endpoints

| Method | Endpoint | Purpose |
|--------|----------|----------|
| POST | `/analyze/pdf-ready/<file_id>` | Complete analysis optimized for PDF generation |
| POST | `/analyze/<file_id>` | Standard analysis with charts and summary |
| POST | `/analyze/stats/<file_id>` | Statistics only, no charts |
| POST | `/analyze/preview/<file_id>` | Quick data preview |

### Result Endpoints

| Method | Endpoint | Purpose |
|--------|----------|----------|
| GET | `/status/<analysis_id>` | Check analysis progress |
| GET | `/download/<analysis_id>` | Download ZIP with all results |
| GET | `/results/<analysis_id>` | Get JSON results |

### Request Parameters

**Upload Request:**
- `file`: Data file (CSV/XLSX/XLS, required)

**Upload Response:**
```json
{
  "message": "File uploaded successfully",
  "file_id": "uuid_filename.csv",
  "original_filename": "data.csv",
  "upload_time": "2024-01-01T12:00:00"
}
```

**Analysis Request:**
- `file_id`: File ID from upload (required in URL path)
- `report_title`: Custom title (optional, in JSON body)
- `output_name`: Output name (optional, in JSON body)
- `rows`: Preview rows (1-20, optional, in JSON body)

**Analysis Response:**
```json
{
  "analysis_id": "uuid-string",
  "status": "completed",
  "message": "Analysis completed successfully",
  "download_available": true
}
```

## 💻 Python Usage Examples

### Basic Analysis

```python
import requests
import zipfile
import json
import os
import time

def analyze_wil_data(file_path, report_title="WIL Report"):
    """Complete WIL analysis workflow with optimized file upload"""
    base_url = "http://localhost:5050/api"
    
    # 1. Upload file and get file_id
    with open(file_path, 'rb') as f:
        upload_response = requests.post(
            f"{base_url}/upload", 
            files={'file': f}
        )
    
    if upload_response.status_code != 200:
        raise Exception(f"Upload failed: {upload_response.json()}")
    
    file_id = upload_response.json()['file_id']
    print(f"File uploaded: {file_id}")
    
    # 2. Start analysis using file_id
    analysis_response = requests.post(
        f"{base_url}/visualization/analyze/pdf-ready/{file_id}",
        json={'report_title': report_title},
        headers={'Content-Type': 'application/json'}
    )
    
    if analysis_response.status_code != 200:
        raise Exception(f"Analysis failed: {analysis_response.json()}")
    
    analysis_id = analysis_response.json()['analysis_id']
    print(f"Analysis started: {analysis_id}")
    
    # 3. Poll status
    while True:
        status = requests.get(f"{base_url}/visualization/status/{analysis_id}").json()
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            raise Exception("Analysis failed")
        time.sleep(2)
    
    # 4. Download results
    download_response = requests.get(f"{base_url}/visualization/download/{analysis_id}")
    
    # 5. Extract ZIP
    extract_dir = f"wil_output_{analysis_id[:8]}"
    with open(f"{extract_dir}.zip", 'wb') as f:
        f.write(download_response.content)
    
    with zipfile.ZipFile(f"{extract_dir}.zip", 'r') as zip_file:
        zip_file.extractall(extract_dir)
    
    # 6. Load template data
    with open(f"{extract_dir}/content/pdf_template_data.json", 'r') as f:
        pdf_data = json.load(f)
    
    return extract_dir, pdf_data, analysis_id, file_id

# Usage
output_dir, data, analysis_id, file_id = analyze_wil_data("data.csv", "Monthly Report")
print(f"Charts: {output_dir}/charts/")
print(f"Analysis ID: {analysis_id}")
print(f"File ID: {file_id} (reusable for future analyses)")
```

### Reuse Uploaded Files

```python
def analyze_existing_file(file_id, report_title="WIL Report"):
    """Analyze previously uploaded file without re-uploading"""
    base_url = "http://localhost:5050/api"
    
    # Check if file exists
    file_info = requests.get(f"{base_url}/upload/{file_id}/info")
    if file_info.status_code != 200:
        raise Exception(f"File not found: {file_id}")
    
    print(f"Using existing file: {file_info.json()['original_filename']}")
    
    # Start analysis using existing file_id
    analysis_response = requests.post(
        f"{base_url}/visualization/analyze/pdf-ready/{file_id}",
        json={'report_title': report_title},
        headers={'Content-Type': 'application/json'}
    )
    
    analysis_id = analysis_response.json()['analysis_id']
    print(f"Analysis started: {analysis_id}")
    
    # Poll status and download (same as before)
    while True:
        status = requests.get(f"{base_url}/visualization/status/{analysis_id}").json()
        if status['status'] == 'completed':
            break
        time.sleep(2)
    
    return analysis_id

# Usage - analyze same file multiple times
file_id = "uuid_data.csv"  # From previous upload
monthly_analysis = analyze_existing_file(file_id, "Monthly Report")
quarterly_analysis = analyze_existing_file(file_id, "Quarterly Report")
```

### Download Previous Results

```python
def download_analysis_results(analysis_id):
    """Download results from previous analysis"""
    base_url = "http://localhost:5050/api/visualization"
    
    # Download and extract
    response = requests.get(f"{base_url}/download/{analysis_id}")
    extract_dir = f"wil_output_{analysis_id[:8]}"
    
    with open(f"{extract_dir}.zip", 'wb') as f:
        f.write(response.content)
    
    with zipfile.ZipFile(f"{extract_dir}.zip", 'r') as zip_file:
        zip_file.extractall(extract_dir)
    
    # Load data
    with open(f"{extract_dir}/content/pdf_template_data.json", 'r') as f:
        pdf_data = json.load(f)
    
    return extract_dir, pdf_data

# Usage
output_dir, data = download_analysis_results("your-analysis-id")
```

### Statistics Only

```python
def get_statistics_only(file_id):
    """Get statistics without generating charts using file_id"""
    base_url = "http://localhost:5050/api"
    
    # Start stats analysis using file_id
    response = requests.post(
        f"{base_url}/visualization/analyze/stats/{file_id}",
        headers={'Content-Type': 'application/json'}
    )
    
    analysis_id = response.json()['analysis_id']
    
    # Poll status
    while True:
        status = requests.get(f"{base_url}/visualization/status/{analysis_id}").json()
        if status['status'] == 'completed':
            break
        time.sleep(1)
    
    # Get JSON results
    results = requests.get(f"{base_url}/visualization/results/{analysis_id}").json()
    return results['results'], analysis_id

# Usage with uploaded file
file_id = "uuid_data.csv"  # From previous upload
stats, analysis_id = get_statistics_only(file_id)
print(f"Total students: {stats['key_statistics']['total_students']}")
print(f"Total faculties: {stats['key_statistics']['total_faculties']}")
```


### Data Preview

```python
def preview_data(file_id, rows=5):
    """Preview data structure using file_id"""
    response = requests.post(
        f"http://localhost:5050/api/visualization/analyze/preview/{file_id}",
        json={'rows': rows},
        headers={'Content-Type': 'application/json'}
    )
    return response.json()

# Usage with uploaded file
file_id = "uuid_data.csv"  # From previous upload
preview = preview_data(file_id, 3)
print(f"Rows: {preview['data_info']['total_rows']}")
print(f"Columns: {preview['data_info']['total_columns']}")
```

## 🚀 Optimized Workflow Benefits

### Upload Once, Analyze Multiple Times
```python
# Upload file once
file_id = upload_file("data.csv")

# Run different analyses on same file
monthly_report = analyze_existing_file(file_id, "Monthly Report")
quarterly_report = analyze_existing_file(file_id, "Quarterly Report")
stats_only = get_statistics_only(file_id)
preview = preview_data(file_id, 10)
```

### Performance Improvements
- **⚡ Faster Processing**: No duplicate file uploads
- **📊 Reduced Bandwidth**: File transmitted only once
- **🔄 Efficient Reuse**: Same data, multiple report types
- **💾 Storage Optimization**: Files stored once in `/backend/uploads/`

### File Management
- **📁 Persistent Storage**: Files remain available for future analyses
- **🔍 File Tracking**: List all uploaded files via `/upload/files`
- **ℹ️ File Info**: Get detailed file information via `/upload/<file_id>/info`
- **🔒 Secure Naming**: UUID-based file IDs prevent conflicts

## 📁 Output Structure

```
wil_analysis_output/
├── charts/                    # 300 DPI PNG charts
│   ├── year_comparison.png
│   ├── faculty_residency.png
│   ├── gender_distribution_pie.png
│   └── ... (10 charts total)
└── content/
    ├── pdf_template_data.json # Main data file
    └── analysis_summary.json  # Full statistics
```

## 📋 PDF Template Data

`pdf_template_data.json` structure:

```json
{
  "report_title": "WIL Data Analysis Report",
  "analysis_id": "unique-id-12345",
  "executive_summary": {
    "total_students": "10,167",
    "total_faculties": "9",
    "academic_year": "2025"
  },
  "key_metrics": {
    "largest_faculty": "UNSW Business School",
    "international_percentage": "39.8%",
    "female_percentage": "52.6%"
  },
  "charts": {
    "year_comparison": "year_comparison_20250629.png",
    "faculty_residency": "faculty_residency_20250629.png",
    "gender_pie": "gender_distribution_pie_20250629.png"
  },
  "chart_descriptions": {
    "year_comparison": {
      "title": "Faculty Enrollment Overview",
      "description": "Student distribution across faculties",
      "key_finding": "UNSW Business School has most students"
    }
  }
}
```

### Chart Descriptions
```json
{
  "chart_descriptions": {
    "year_comparison": {
      "title": "Faculty Enrollment Overview (2025)",
      "description": "This chart displays the distribution of WIL students across 9 faculties. A total of 10,167 students are enrolled in WIL programs.",
      "key_finding": "The largest faculty by enrollment is UNSW Business School."
    },
    "faculty_residency": {
      "title": "Student Distribution by Faculty and Residency Status",
      "description": "This grouped bar chart compares local and international student enrollment across different faculties, providing insights into the diversity and international appeal of each program.",
      "key_finding": "Overall, 60.2% are local students and 39.8% are international students."
    },
    "gender_distribution": {
      "title": "Gender Representation Analysis",
      "description": "These charts examine gender balance across the WIL program, showing both overall distribution and faculty-specific gender ratios to identify areas for diversity improvement.",
      "key_finding": "Gender distribution is 52.6% female and 47.3% male."
    }
  }
}
```

### Key Insights
```json
{
  "key_insights": {
    "program_overview": [
      "The WIL program serves 10,167 students across 9 faculties.",
      "A total of 178 different courses are offered.",
      "The program demonstrates strong diversity in both academic disciplines and student demographics."
    ],
    "diversity_analysis": [
      "International student participation is 39.8%.",
      "Gender balance shows 52.6% female participation.",
      "First-generation student representation is 13.8%."
    ]
  }
}
```

## 🎨 ReportLab Integration Example

Here's a basic example of how to use the analysis results in ReportLab:

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os

def create_wil_pdf_report(analysis_dir, pdf_data, output_path="wil_report.pdf"):
    """
    Create PDF report using WIL analysis results
    
    Args:
        analysis_dir: Analysis output directory
        pdf_data: PDF template data
        output_path: Output PDF path
    """
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Add title
    story.append(Paragraph(pdf_data['report_title'], styles['Title']))
    story.append(Spacer(1, 0.5*inch))
    
    # Add executive summary
    exec_summary = pdf_data['executive_summary']
    story.append(Paragraph("Executive Summary", styles['Heading1']))
    story.append(Paragraph(f"Total Students: {exec_summary['total_students']}", styles['Normal']))
    story.append(Paragraph(f"Academic Year: {exec_summary['academic_year']}", styles['Normal']))
    story.append(Paragraph(f"Report Date: {exec_summary['report_date']}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Add key metrics
    story.append(Paragraph("Key Metrics", styles['Heading2']))
    for metric, value in pdf_data['key_metrics'].items():
        formatted_metric = metric.replace('_', ' ').title()
        story.append(Paragraph(f"{formatted_metric}: {value}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Add charts
    charts_dir = os.path.join(analysis_dir, 'charts')
    
    # Year comparison chart
    year_chart_path = os.path.join(charts_dir, pdf_data['charts']['year_comparison'])
    if os.path.exists(year_chart_path):
        # Add chart description
        year_desc = pdf_data['chart_descriptions']['year_comparison']
        story.append(Paragraph(year_desc['title'], styles['Heading2']))
        story.append(Paragraph(year_desc['description'], styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Add chart image
        story.append(Image(year_chart_path, width=6*inch, height=4*inch))
        story.append(Paragraph(f"Key Finding: {year_desc['key_finding']}", styles['Italic']))
        story.append(Spacer(1, 0.3*inch))
    
    # Add faculty residency chart
    faculty_chart_path = os.path.join(charts_dir, pdf_data['charts']['faculty_residency'])
    if os.path.exists(faculty_chart_path):
        faculty_desc = pdf_data['chart_descriptions']['faculty_residency']
        story.append(Paragraph(faculty_desc['title'], styles['Heading2']))
        story.append(Paragraph(faculty_desc['description'], styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Image(faculty_chart_path, width=6*inch, height=4*inch))
        story.append(Paragraph(f"Key Finding: {faculty_desc['key_finding']}", styles['Italic']))
        story.append(Spacer(1, 0.3*inch))
    
    # Generate PDF
    doc.build(story)
    print(f"✅ PDF report generated: {output_path}")

# Usage example
# create_wil_pdf_report("wil_analysis_output", pdf_data, "monthly_wil_report.pdf")
```

## 📊 Chart Types Generated

The analysis generates 10 high-quality charts:

1. **Year Comparison** (`year_comparison_*.png`)
   - Faculty enrollment overview for 2025
   - Horizontal bar chart showing student distribution across faculties

2. **Faculty Residency** (`faculty_residency_*.png`)
   - Grouped bar chart comparing local vs international students by faculty
   - Shows diversity and international appeal of each program

3. **Gender Distribution Pie** (`gender_distribution_pie_*.png`)
   - Overall gender distribution across all WIL programs
   - Clear percentage breakdown with professional color scheme

4. **Gender Distribution by Faculty** (`gender_distribution_faculty_*.png`)
   - Horizontal stacked bar chart showing gender ratios within each faculty
   - Helps identify gender balance across different disciplines

5. **First Generation Participation** (`first_generation_participation_*.png`)
   - First-generation student participation rates by faculty
   - Horizontal bar chart with percentage values

6. **SES Distribution** (`ses_distribution_*.png`)
   - Socioeconomic status distribution by faculty
   - Stacked horizontal bar chart showing High/Medium/Low/Unknown categories

7. **Indigenous Participation** (`indigenous_participation_*.png`)
   - Indigenous student participation rates by faculty
   - Horizontal bar chart highlighting inclusion metrics

8. **Regional Distribution** (`regional_distribution_*.png`)
   - Geographic distribution of students (Major Cities, Regional, Remote areas)
   - Clean pie chart with legend only (no overlapping text)

9. **CDEV Residency** (`cdev_residency_*.png`)
   - Career Development course enrollment by residency status
   - Grouped bar chart for Local vs International students

10. **CDEV Gender** (`cdev_gender_*.png`)
    - Gender distribution in Career Development courses
    - Stacked bar chart showing participation patterns

## ❓ Frequently Asked Questions

### Q1: Service not connecting?
```bash
# Check service status
curl http://localhost:5050/api/visualization/health

# Start service
cd backend && python run.py
```

### Q2: Unsupported file format?
**Supported formats:**
- ✅ CSV files (.csv)
- ✅ Excel files (.xlsx, .xls)

### Q3: Analysis failing?
**Check if data file contains required columns:**
- `MASKED_ID` - Student ID
- `ACADEMIC_YEAR` - Academic year
- `FACULTY_DESCR` - Faculty description
- `COURSE_CODE` - Course code
- `GENDER` - Gender
- `RESIDENCY_GROUP_DESCR` - Residency status

### Q4: Chart quality issues?
- All charts are 300 DPI high resolution
- PNG format with white background
- Suitable for printing and PDF embedding

### Q5: Large file processing?
- Maximum file size: 100MB
- Processing time varies with data size
- Use preview endpoint to check data before full analysis

### Q6: Missing data handling?
- Unknown/missing values are handled automatically
- Empty cells are filled with "Unknown" where appropriate
- Statistical calculations exclude missing values appropriately

## 📢 Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | ✅ |
| 400 | Invalid file/params | Check file format and required columns |
| 413 | File too large | Use files <100MB or split data |
| 500 | Server error | Check logs, restart service |

## 📞 Support

**Health Check:**
```python
import requests
response = requests.get("http://localhost:5050/api/visualization/health")
print(response.json())
```

**Documentation:** `http://localhost:5050/docs/`

---

**🎉 Quick Reference:**
- **📤 Upload**: POST file to `/upload` → get `file_id`
- **🚀 Analyze**: POST to `/analyze/pdf-ready/<file_id>` → get `analysis_id`
- **⏳ Monitor**: Poll `/status/<analysis_id>`
- **📥 Download**: GET `/download/<analysis_id>`
- **🔄 Reuse**: Use same `file_id` for multiple analyses
- **📈 Performance**: Save both `file_id` and `analysis_id` for reuse
- **🎨 Integration**: Charts work directly with ReportLab