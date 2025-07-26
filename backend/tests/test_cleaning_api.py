import pytest
import os
import tempfile
import io
from app import create_app
import pandas as pd


@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_excel_data():
    """Create sample Excel data for testing"""
    data = {
        'RESIDENCY_GROUP_DESCR': ['Local', 'International'],
        'ACADEMIC_YEAR': [2025, 2025],
        'TERM': [5256, 5256],
        'COURSE_CODE': ['PSYC7238', 'COMM5030'],
        'CATALOG_NUMBER': [7238, 5030],
        'MASKED_ID': [755415, 541573]
    }
    df = pd.DataFrame(data)
    # Create Excel file in memory
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    return excel_buffer.getvalue()


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    data = {
        'RESIDENCY_GROUP_DESCR': ['Local', 'International', 'Local'],
        'ACADEMIC_YEAR': [2025, 2025, 2025],
        'TERM': [5256, 5256, 5256],
        'TERM_DESCR': ['2025 Term 2', '2025 Term 2', '2025 Term 2'],
        'ACADEMIC_CAREER_DESCR': ['Postgraduate', 'Postgraduate', 'Postgraduate'],
        'ACAD_PROG': [8266, 8404, 8266],
        'COURSE_ID': [67107, 64962, 67106],
        'OFFER_NUMBER': [1, 1, 1],
        'FACULTY': ['SCI', 'COMM', 'SCI'],
        'FACULTY_DESCR': ['Faculty of Science', 'UNSW Business School', 'Faculty of Science'],
        'SCHOOL': ['PSYC', 'COMM', 'PSYC'],
        'SCHOOL_NAME': ['School of Psychology', 'UNSW Business School', 'School of Psychology'],
        'COURSE_NAME': ['Neuropsychology (NPEP2)', 'Social Entre Practicum', 'Neuropsychology (NPEP1)'],
        'GENDER': ['F', 'M', 'F'],
        'FIRST_GENERATION_IND': ['Non First Generation', 'Non First Generation', 'Non First Generation'],
        'ATSI_DESC': ['Not of Aboriginal/T S Islander', 'Not of Aboriginal/T S Islander', 'Not of Aboriginal/T S Islander'],
        'ATSI_GROUP': ['Non Indigenous', 'Non Indigenous', 'Non Indigenous'],
        'REGIONAL_REMOTE': ['Outer Regional Australia', 'Major Cities of Australia', 'Outer Regional Australia'],
        'SES': ['High', 'Medium', 'High'],
        'ADMISSION_PATHWAY': ['Others', 'Others', 'Others'],
        'COURSE_CODE': ['PSYC7238', 'COMM5030', 'PSYC7237'],
        'CATALOG_NUMBER': [7238, 5030, 7237],
        'CRSE_ATTR': ['WILC', 'WILC', 'WILC'],
        'MASKED_ID': [755415, 541573, 755415]
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_clean_data_no_file(client):
    """Test cleaning API without file"""
    response = client.post('/api/clean')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'No file provided' in data['error']


def test_clean_data_empty_filename(client):
    """Test cleaning API with empty filename"""
    data = {'file': (io.BytesIO(b''), '')}
    response = client.post('/api/clean', data=data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'No file selected' in data['error']


def test_clean_data_invalid_file_type(client):
    """Test cleaning API with invalid file type"""
    data = {'file': (io.BytesIO(b'test content'), 'test.txt')}
    response = client.post('/api/clean', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Invalid file type' in data['error']
    assert 'CSV, XLSX, and XLS' in data['details']


def test_validate_file_success(client, sample_csv_data):
    """Test file validation with valid CSV"""
    data = {
        'file': (io.BytesIO(sample_csv_data.encode()), 'test.csv')
    }
    response = client.post('/api/validate', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
    assert result['valid'] is True
    assert result['file_info']['rows'] == 3
    assert result['file_info']['columns'] == 24


def test_validate_file_no_file(client):
    """Test file validation without file"""
    response = client.post('/api/validate')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'No file provided' in data['error']


def test_clean_data_success(client, sample_csv_data):
    """Test successful data cleaning"""
    data = {
        'file': (io.BytesIO(sample_csv_data.encode()), 'test.csv'),
        'fill_missing': 'true',
        'batch_id': 'test_batch'
    }
    response = client.post('/api/clean', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
    assert 'file_id' in result['data']['file_info']
    assert result['data']['cleaned_records'] == 3
    assert result['data']['columns_count'] == 24


def test_get_cleaning_status_not_found(client):
    """Test getting status for non-existent file ID"""
    response = client.get('/api/status/nonexistent_id')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'File ID not found' in data['error']


def test_download_file_not_found(client):
    """Test downloading non-existent file"""
    response = client.get('/api/download/nonexistent_id/data')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


def test_download_invalid_file_type(client):
    """Test downloading with invalid file type"""
    response = client.get('/api/download/some_id/invalid_type')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'Invalid file type' in data['error']


def test_validate_excel_file_success(client, sample_excel_data):
    """Test file validation with valid Excel file"""
    data = {
        'file': (io.BytesIO(sample_excel_data), 'test.xlsx')
    }
    response = client.post('/api/validate', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
    assert result['valid'] is True
    assert result['file_info']['rows'] == 2
    assert result['file_info']['columns'] == 6


def test_clean_excel_data_success(client, sample_excel_data):
    """Test successful Excel data cleaning"""
    data = {
        'file': (io.BytesIO(sample_excel_data), 'test.xlsx'),
        'fill_missing': 'false',
        'batch_id': 'excel_test'
    }
    response = client.post('/api/clean', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
    assert 'file_id' in result['data']['file_info']
    assert result['data']['cleaned_records'] == 2
    assert result['data']['columns_count'] == 6