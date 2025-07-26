"""
Tests for file upload functionality
"""
import pytest
import os
import tempfile
import pandas as pd
from io import BytesIO
from app import create_app
from app.services.validation import DataValidator, validate_filename


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
def sample_csv_file():
    """Create a sample CSV file for testing"""
    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'London', 'Paris']
    }
    df = pd.DataFrame(data)
    
    # Create CSV in memory
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer


@pytest.fixture
def sample_excel_file():
    """Create a sample Excel file for testing"""
    data = {
        'Product': ['Laptop', 'Mouse', 'Keyboard'],
        'Price': [999.99, 29.99, 79.99],
        'Stock': [50, 100, 75]
    }
    df = pd.DataFrame(data)
    
    # Create Excel in memory
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    return excel_buffer


class TestFileUpload:
    """Test file upload endpoints"""
    
    def test_upload_csv_success(self, client, sample_csv_file):
        """Test successful CSV upload"""
        response = client.post('/api/upload', data={
            'file': (sample_csv_file, 'test.csv', 'text/csv')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'File uploaded successfully'
        assert data['original_filename'] == 'test.csv'
        assert 'file_id' in data
        assert 'file_info' in data
        assert data['file_info']['rows'] == 3
        assert data['file_info']['columns'] == 3
    
    def test_upload_excel_success(self, client, sample_excel_file):
        """Test successful Excel upload"""
        response = client.post('/api/upload', data={
            'file': (sample_excel_file, 'test.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'File uploaded successfully'
        assert data['original_filename'] == 'test.xlsx'
        assert 'quality_report' in data
    
    def test_upload_no_file(self, client):
        """Test upload with no file"""
        response = client.post('/api/upload', data={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename"""
        response = client.post('/api/upload', data={
            'file': (BytesIO(b''), '', 'text/csv')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No file selected' in data['error']
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        response = client.post('/api/upload', data={
            'file': (BytesIO(b'some text'), 'test.txt', 'text/plain')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'File type not allowed' in data['error']
    
    def test_upload_empty_file(self, client):
        """Test upload with empty CSV file"""
        empty_csv = BytesIO(b'')
        response = client.post('/api/upload', data={
            'file': (empty_csv, 'empty.csv', 'text/csv')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_file_info(self, client, sample_csv_file):
        """Test getting file information"""
        # First upload a file
        upload_response = client.post('/api/upload', data={
            'file': (sample_csv_file, 'test.csv', 'text/csv')
        }, content_type='multipart/form-data')
        
        assert upload_response.status_code == 200
        upload_data = upload_response.get_json()
        file_id = upload_data['file_id']
        
        # Get file info
        info_response = client.get(f'/api/upload/{file_id}/info')
        assert info_response.status_code == 200
        
        info_data = info_response.get_json()
        assert info_data['file_id'] == file_id
        assert info_data['original_filename'] == 'test.csv'
        assert 'file_info' in info_data
        assert 'quality_report' in info_data
    
    def test_get_file_info_not_found(self, client):
        """Test getting info for non-existent file"""
        response = client.get('/api/upload/nonexistent_file.csv/info')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'File not found' in data['error']
    
    def test_list_files(self, client, sample_csv_file):
        """Test listing uploaded files"""
        # Upload a file first
        client.post('/api/upload', data={
            'file': (sample_csv_file, 'test.csv', 'text/csv')
        }, content_type='multipart/form-data')
        
        # List files
        response = client.get('/api/upload/files')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'files' in data
        assert len(data['files']) >= 1
        assert data['files'][0]['original_filename'] == 'test.csv'
    
    def test_validate_file_with_rules(self, client, sample_csv_file):
        """Test file validation with custom rules"""
        # Upload a file first
        upload_response = client.post('/api/upload', data={
            'file': (sample_csv_file, 'test.csv', 'text/csv')
        }, content_type='multipart/form-data')
        
        file_id = upload_response.get_json()['file_id']
        
        # Test validation with rules
        rules = {
            'required_columns': ['Name', 'Age'],
            'min_rows': 2
        }
        
        response = client.post(f'/api/upload/{file_id}/validate', 
                              json=rules,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['passed'] == True
        assert 'Name' in str(data['rules_checked'])


class TestDataValidator:
    """Test DataValidator class"""
    
    def test_validate_filename_valid(self):
        """Test valid filename validation"""
        valid, error = validate_filename('test.csv')
        assert valid == True
        assert error is None
    
    def test_validate_filename_invalid_chars(self):
        """Test filename with invalid characters"""
        valid, error = validate_filename('test/file.csv')
        assert valid == False
        assert 'invalid character' in error
    
    def test_validate_filename_too_long(self):
        """Test filename that's too long"""
        long_name = 'a' * 300 + '.csv'
        valid, error = validate_filename(long_name)
        assert valid == False
        assert 'too long' in error
    
    def test_validate_filename_invalid_extension(self):
        """Test filename with invalid extension"""
        valid, error = validate_filename('test.txt')
        assert valid == False
        assert 'Invalid file extension' in error
    
    def test_data_validator_init(self):
        """Test DataValidator initialization"""
        validator = DataValidator()
        assert validator.required_columns == []
        assert validator.optional_columns == []
        assert validator.validation_rules == {}