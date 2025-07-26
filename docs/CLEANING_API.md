# Data Cleaning API Documentation

This document describes the data cleaning API endpoints for the WIL data processing system. The API supports both CSV and Excel file formats (.csv, .xlsx, .xls).

## API Endpoints

### 1. Data Cleaning
**POST** `/api/clean`

Upload and clean a CSV or Excel file with comprehensive data processing.

**Parameters:**
- `file` (file, required): CSV or Excel file to be cleaned
- `fill_missing` (boolean, optional): Whether to fill missing values (default: false)
- `batch_id` (string, optional): Custom batch identifier for output files

**Response:**
```json
{
    "success": true,
    "message": "Data cleaning completed successfully",
    "data": {
        "original_records": 1000,
        "cleaned_records": 995,
        "removed_records": 5,
        "columns_count": 24,
        "cleaning_summary": {
            "missing_values_filled": true,
            "batch_id": "batch_001",
            "processing_time": "2024-12-25T14:30:22+11:00"
        },
        "file_info": {
            "cleaned_file": "WIL_2025_cleaned.csv",
            "report_file": "data_cleaning_report_2025_20241225_143022.txt",
            "file_id": "uuid-string"
        }
    }
}
```

### 2. File Validation
**POST** `/api/validate`

Validate a CSV file before cleaning to check compatibility.

**Parameters:**
- `file` (file, required): CSV file to validate

**Response:**
```json
{
    "success": true,
    "valid": true,
    "message": "File is valid for cleaning",
    "file_info": {
        "filename": "data.csv",
        "size": 1024000,
        "rows": 1000,
        "columns": 24,
        "column_names": ["ACADEMIC_YEAR", "TERM", ...]
    },
    "validation_issues": []
}
```

### 3. Download Files
**GET** `/api/download/<file_id>/<file_type>`

Download cleaned data or cleaning report.

**Parameters:**
- `file_id` (path, required): File ID from cleaning operation
- `file_type` (path, required): "data" for cleaned CSV or "report" for cleaning report

**Response:**
- Success: File download
- Error: JSON error message

### 4. Check Status
**GET** `/api/status/<file_id>`

Check the status of a cleaning operation.

**Response:**
```json
{
    "success": true,
    "file_id": "uuid-string",
    "status": "completed",
    "files_available": {
        "cleaned_data": true,
        "cleaning_report": true
    }
}
```

## Data Cleaning Features

### 1. Missing Value Handling
- Converts empty strings to NaN
- Preserves "Unknown" as valid category
- Optional filling: numeric fields with 0, categorical with "Unknown"

### 2. Data Type Conversion
- Integer fields: `ACADEMIC_YEAR`, `TERM`, `ACAD_PROG`, `COURSE_ID`, `OFFER_NUMBER`, `CATALOG_NUMBER`, `MASKED_ID`
- Other fields: string type

### 3. Text Cleaning
- Removes leading/trailing whitespace
- Standardizes text fields
- Preserves original case

### 4. Gender Standardization
- Ensures only M/F/U values
- U represents "Unknown"

### 5. Categorical Validation
- Validates expected values for key fields
- Reports unexpected values

### 6. Duplicate Detection
- Removes completely duplicate rows
- Handles business duplicates (same student/term/course)

### 7. Data Consistency Checks
- Faculty-description mapping
- Course code format validation
- Catalog number consistency

## Usage Examples

### Python Requests
```python
import requests

# Clean data with missing value filling
files = {'file': open('data.csv', 'rb')}
data = {'fill_missing': 'true', 'batch_id': 'morning_batch'}
response = requests.post('http://localhost:5050/api/clean', files=files, data=data)

# Download cleaned data
file_id = response.json()['data']['file_info']['file_id']
cleaned_data = requests.get(f'http://localhost:5050/api/download/{file_id}/data')
```

### cURL Examples
```bash
# Validate file
curl -X POST -F "file=@data.csv" http://localhost:5050/api/validate

# Clean data
curl -X POST -F "file=@data.csv" -F "fill_missing=true" -F "batch_id=test" http://localhost:5050/api/clean

# Download report
curl -O http://localhost:5050/api/download/{file_id}/report
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid file, missing parameters)
- `404`: File not found
- `500`: Server error

Error responses include:
```json
{
    "success": false,
    "error": "Error description",
    "details": "Detailed error message"
}
```

## Swagger Documentation

Visit `/docs/` when the server is running to access interactive API documentation.

## Testing

Run the test suite:
```bash
cd backend
python -m pytest tests/test_cleaning_api.py -v
```