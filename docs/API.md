# Reporting System API Documentation

This document provides comprehensive documentation for the Reporting System API endpoints. The API supports automated report generation and file upload functionality.

## Base URL
```
http://localhost:5050/api
```

## Interactive Documentation
- **Swagger UI**: `http://localhost:5050/docs/`
- **OpenAPI Spec**: `http://localhost:5050/apispec_1.json`

## File Upload Endpoints

### Upload File
Upload CSV or Excel files for processing and analysis.

**Endpoint:** `POST /upload`

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | Yes | CSV or Excel file (.csv, .xlsx, .xls) |

**File Requirements:**
- Maximum file size: 15MB
- Supported formats: CSV (.csv), Excel (.xlsx, .xls)
- File must contain data (not empty)

**Success Response (200):**
```json
{
  "message": "File uploaded successfully",
  "file_id": "uuid_filename.csv",
  "original_filename": "data.csv",
  "upload_time": "2024-12-27T14:30:00+11:00",
  "file_info": {
    "rows": 1000,
    "columns": 5,
    "column_names": ["Name", "Age", "City", "Email", "Phone"],
    "column_types": {
      "Name": "text",
      "Age": "integer", 
      "City": "text",
      "Email": "text",
      "Phone": "text"
    },
    "file_size": 1024,
    "non_empty_rows": 995,
    "has_headers": true
  },
  "quality_report": {
    "total_rows": 1000,
    "total_columns": 5,
    "missing_data": {
      "Name": {"count": 0, "percentage": 0.0},
      "Age": {"count": 5, "percentage": 0.5}
    },
    "duplicate_rows": 3,
    "data_types": {
      "Name": "object",
      "Age": "int64"
    },
    "warnings": [
      "Found 3 duplicate rows"
    ],
    "errors": []
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file type, missing file, validation errors
- `413 Payload Too Large`: File exceeds 15MB limit
- `500 Internal Server Error`: Server processing error

### Get File Information
Retrieve detailed information about an uploaded file.

**Endpoint:** `GET /upload/{file_id}/info`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | Unique identifier of uploaded file |

**Success Response (200):**
```json
{
  "file_id": "uuid_filename.csv",
  "original_filename": "data.csv",
  "upload_time": "2024-12-27T14:30:00+11:00",
  "last_modified": "2024-12-27T14:30:00+11:00",
  "file_info": {
    "rows": 1000,
    "columns": 5,
    "column_names": ["Name", "Age", "City"],
    "file_size": 1024
  },
  "quality_report": {
    "total_rows": 1000,
    "missing_data": {},
    "warnings": []
  }
}
```

### Validate File with Custom Rules
Validate an uploaded file against custom business rules.

**Endpoint:** `POST /upload/{file_id}/validate`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "required_columns": ["Name", "Age", "Email"],
  "min_rows": 10,
  "column_types": {
    "Age": "numeric",
    "Name": "text"
  }
}
```

**Success Response (200):**
```json
{
  "passed": true,
  "errors": [],
  "warnings": [
    "Column 'Phone' expected to be numeric but appears to be object"
  ],
  "rules_checked": [
    "required_columns",
    "min_rows", 
    "column_types"
  ]
}
```

### List Uploaded Files
Get a list of all uploaded files.

**Endpoint:** `GET /upload/files`

**Success Response (200):**
```json
{
  "files": [
    {
      "file_id": "uuid_filename.csv",
      "original_filename": "data.csv", 
      "size": 1024,
      "upload_time": "2024-12-27T14:30:00+11:00",
      "last_modified": "2024-12-27T14:30:00+11:00"
    }
  ]
}
```

### Test Upload Service
Test if the upload service is available.

**Endpoint:** `GET /upload/test`

**Success Response (200):**
```json
{
  "message": "Upload blueprint is working!"
}
```

## Example Usage

### JavaScript/Fetch API
```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:5050/api/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();

if (response.ok) {
  console.log('Upload successful:', result.file_id);
  console.log('File info:', result.file_info);
} else {
  console.error('Upload failed:', result.error);
}
```

### Python/Requests
```python
import requests

# Upload file
with open('data.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5050/api/upload', files=files)

if response.status_code == 200:
    result = response.json()
    file_id = result['file_id']
    print(f"Upload successful: {file_id}")
else:
    print(f"Upload failed: {response.json()['error']}")
```

### cURL Examples
```bash
# Upload file
curl -X POST \
  http://localhost:5050/api/upload \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@data.csv'

# Get file info
curl -X GET \
  http://localhost:5050/api/upload/{file_id}/info

# List files
curl -X GET \
  http://localhost:5050/api/upload/files
```

## Time Zone Information
All timestamps in API responses use Australian Eastern Standard Time (AEST/AEDT):
- Format: ISO 8601 with timezone offset (+11:00 for AEDT, +10:00 for AEST)
- Example: `2024-12-27T14:30:00+11:00`