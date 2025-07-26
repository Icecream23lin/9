from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import pytz
from app.services.validation import DataValidator, validate_filename, FileValidationError

upload_bp = Blueprint('upload', __name__)

def get_australian_time():
    """Get current time in Australian Eastern timezone"""
    aus_tz = pytz.timezone('Australia/Sydney')
    return datetime.now(aus_tz)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload CSV or Excel file for processing
    ---
    tags:
      - File Upload
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: CSV or Excel file to upload (.csv, .xlsx, .xls)
    responses:
      200:
        description: File uploaded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "File uploaded successfully"
            file_id:
              type: string
              example: "uuid_filename.csv"
            original_filename:
              type: string  
              example: "data.csv"
            upload_time:
              type: string
              format: date-time
              example: "2024-01-01T12:00:00"
            file_info:
              type: object
              properties:
                rows:
                  type: integer
                  example: 1000
                columns:
                  type: integer
                  example: 5
                column_names:
                  type: array
                  items:
                    type: string
                  example: ["Name", "Age", "City"]
                file_size:
                  type: integer
                  example: 1024
                has_headers:
                  type: boolean
                  example: true
            quality_report:
              type: object
              properties:
                total_rows:
                  type: integer
                  example: 1000
                total_columns:
                  type: integer
                  example: 5
                missing_data:
                  type: object
                duplicate_rows:
                  type: integer
                  example: 5
                warnings:
                  type: array
                  items:
                    type: string
      400:
        description: Bad request (invalid file, validation error)
        schema:
          type: object
          properties:
            error:
              type: string
              example: "File type not allowed. Please upload .csv, .xlsx, or .xls files only"
      413:
        description: File too large (>15MB)
        schema:
          type: object
          properties:
            error:
              type: string
              example: "File too large. Maximum size is 15MB."
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Upload failed: Internal error"
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate filename for security
        is_valid_filename, filename_error = validate_filename(file.filename)
        if not is_valid_filename:
            return jsonify({'error': filename_error}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed. Please upload .csv, .xlsx, or .xls files only'
            }), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Initialize validator
        validator = DataValidator()
        
        # Validate file structure and content
        file_info, error = validator.validate_file_structure(file_path, filename)
        if error:
            # Clean up file if validation fails
            os.remove(file_path)
            return jsonify({'error': error}), 400
        
        # Perform data quality validation
        quality_report = validator.validate_data_quality(file_path, filename)
        
        # Return success response with file info and quality report
        response = {
            'message': 'File uploaded successfully',
            'file_id': unique_filename,
            'original_filename': filename,
            'upload_time': get_australian_time().isoformat(),
            'file_info': file_info,
            'quality_report': quality_report
        }
        
        return jsonify(response), 200
        
    except FileValidationError as e:
        # Clean up file if it exists
        try:
            if 'file_path' in locals():
                os.remove(file_path)
        except:
            pass
        return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        # Clean up file if it exists
        try:
            if 'file_path' in locals():
                os.remove(file_path)
        except:
            pass
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@upload_bp.route('/upload/<file_id>/info', methods=['GET'])
def get_file_info(file_id):
    """
    Get detailed information about an uploaded file
    ---
    tags:
      - File Upload
    parameters:
      - name: file_id
        in: path
        type: string
        required: true
        description: Unique identifier of the uploaded file
        example: "uuid_filename.csv"
    responses:
      200:
        description: File information retrieved successfully
        schema:
          type: object
          properties:
            file_id:
              type: string
              example: "uuid_filename.csv"
            original_filename:
              type: string
              example: "data.csv"
            upload_time:
              type: string
              format: date-time
            last_modified:
              type: string
              format: date-time
            file_info:
              type: object
              properties:
                rows:
                  type: integer
                columns:
                  type: integer
                column_names:
                  type: array
                  items:
                    type: string
                file_size:
                  type: integer
            quality_report:
              type: object
      404:
        description: File not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "File not found"
      500:
        description: Internal server error
    """
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract original filename from file_id (format: uuid_originalname)
        parts = file_id.split('_', 1)
        if len(parts) < 2:
            return jsonify({'error': 'Invalid file ID'}), 400
        
        original_filename = parts[1]
        
        # Initialize validator
        validator = DataValidator()
        
        # Get file structure info
        file_info, error = validator.validate_file_structure(file_path, original_filename)
        if error:
            return jsonify({'error': error}), 400
        
        # Get quality report
        quality_report = validator.validate_data_quality(file_path, original_filename)
        
        # Get file stats
        file_stats = os.stat(file_path)
        
        # Convert file timestamps to Australian timezone
        aus_tz = pytz.timezone('Australia/Sydney')
        upload_time = datetime.fromtimestamp(file_stats.st_ctime, aus_tz)
        last_modified = datetime.fromtimestamp(file_stats.st_mtime, aus_tz)
        
        response = {
            'file_id': file_id,
            'original_filename': original_filename,
            'upload_time': upload_time.isoformat(),
            'last_modified': last_modified.isoformat(),
            'file_info': file_info,
            'quality_report': quality_report
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get file info: {str(e)}'}), 500

@upload_bp.route('/upload/<file_id>/validate', methods=['POST'])
def validate_file_with_rules(file_id):
    """
    Validate uploaded file against custom business rules
    ---
    tags:
      - File Upload
    parameters:
      - name: file_id
        in: path
        type: string
        required: true
        description: Unique identifier of the uploaded file
      - name: validation_rules
        in: body
        required: false
        schema:
          type: object
          properties:
            required_columns:
              type: array
              items:
                type: string
              example: ["Name", "Age", "Email"]
            min_rows:
              type: integer
              example: 10
            column_types:
              type: object
              example: {"Age": "numeric", "Name": "text"}
    responses:
      200:
        description: Validation completed
        schema:
          type: object
          properties:
            passed:
              type: boolean
              example: true
            errors:
              type: array
              items:
                type: string
            warnings:
              type: array
              items:
                type: string
            rules_checked:
              type: array
              items:
                type: string
      404:
        description: File not found
      500:
        description: Validation failed
    """
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract original filename
        parts = file_id.split('_', 1)
        if len(parts) < 2:
            return jsonify({'error': 'Invalid file ID'}), 400
        
        original_filename = parts[1]
        
        # Get validation rules from request
        rules = request.get_json() or {}
        
        # Initialize validator
        validator = DataValidator()
        
        # Validate against business rules
        validation_results = validator.validate_business_rules(file_path, original_filename, rules)
        
        return jsonify(validation_results), 200
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@upload_bp.route('/upload/files', methods=['GET'])
def list_uploaded_files():
    """
    List all uploaded files
    ---
    tags:
      - File Upload
    responses:
      200:
        description: List of uploaded files
        schema:
          type: object
          properties:
            files:
              type: array
              items:
                type: object
                properties:
                  file_id:
                    type: string
                    example: "uuid_filename.csv"
                  original_filename:
                    type: string
                    example: "data.csv"
                  size:
                    type: integer
                    example: 1024
                  upload_time:
                    type: string
                    format: date-time
                  last_modified:
                    type: string
                    format: date-time
      500:
        description: Failed to list files
    """
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        files = []
        
        if not os.path.exists(upload_folder):
            return jsonify({'files': []}), 200
        
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                # Extract original filename
                parts = filename.split('_', 1)
                original_filename = parts[1] if len(parts) >= 2 else filename
                
                file_stats = os.stat(file_path)
                
                # Convert timestamps to Australian timezone
                aus_tz = pytz.timezone('Australia/Sydney')
                upload_time = datetime.fromtimestamp(file_stats.st_ctime, aus_tz)
                last_modified = datetime.fromtimestamp(file_stats.st_mtime, aus_tz)
                
                files.append({
                    'file_id': filename,
                    'original_filename': original_filename,
                    'size': file_stats.st_size,
                    'upload_time': upload_time.isoformat(),
                    'last_modified': last_modified.isoformat()
                })
        
        # Sort by upload time (newest first)
        files.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return jsonify({'files': files}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list files: {str(e)}'}), 500

@upload_bp.route('/upload/batch', methods=['POST'])
def upload_batch():
    """
    Upload multiple CSV or Excel files for batch processing
    ---
    tags:
      - File Upload
    consumes:
      - multipart/form-data
    parameters:
      - name: files
        in: formData
        type: array
        items:
          type: file
        required: true
        description: Multiple CSV or Excel files to upload (.csv, .xlsx, .xls)
      - name: batch_id
        in: formData
        type: string
        required: false
        description: Custom batch identifier for grouping files
    responses:
      200:
        description: Files uploaded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Batch upload completed"
            batch_id:
              type: string
              example: "batch_20240101_120000"
            total_files:
              type: integer
              example: 3
            successful_uploads:
              type: integer
              example: 2
            failed_uploads:
              type: integer
              example: 1
            upload_time:
              type: string
              format: date-time
            results:
              type: array
              items:
                type: object
                properties:
                  original_filename:
                    type: string
                  file_id:
                    type: string
                  status:
                    type: string
                    enum: ["success", "failed"]
                  error:
                    type: string
                  file_info:
                    type: object
                  quality_report:
                    type: object
      400:
        description: Bad request (no files provided)
        schema:
          type: object
          properties:
            error:
              type: string
              example: "No files provided for batch upload"
      500:
        description: Internal server error
    """
    try:
        # Check if files are present in request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided for batch upload'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files provided for batch upload'}), 400
        
        # Get batch_id from form data or generate one
        batch_id = request.form.get('batch_id')
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        upload_time = get_australian_time()
        results = []
        successful_uploads = 0
        failed_uploads = 0
        
        # Initialize validator once for all files
        validator = DataValidator()
        
        for file in files:
            file_result = {
                'original_filename': file.filename,
                'file_id': None,
                'status': 'failed',
                'error': None,
                'file_info': None,
                'quality_report': None
            }
            
            try:
                # Check if file was selected
                if file.filename == '':
                    file_result['error'] = 'Empty filename'
                    failed_uploads += 1
                    results.append(file_result)
                    continue
                
                # Validate filename for security
                is_valid_filename, filename_error = validate_filename(file.filename)
                if not is_valid_filename:
                    file_result['error'] = filename_error
                    failed_uploads += 1
                    results.append(file_result)
                    continue
                
                # Check if file type is allowed
                if not allowed_file(file.filename):
                    file_result['error'] = 'File type not allowed. Please upload .csv, .xlsx, or .xls files only'
                    failed_uploads += 1
                    results.append(file_result)
                    continue
                
                # Generate unique filename with batch_id
                filename = secure_filename(file.filename)
                unique_filename = f"{batch_id}_{uuid.uuid4()}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save file
                file.save(file_path)
                file_result['file_id'] = unique_filename
                
                # Validate file structure and content
                file_info, error = validator.validate_file_structure(file_path, filename)
                if error:
                    # Clean up file if validation fails
                    os.remove(file_path)
                    file_result['error'] = error
                    failed_uploads += 1
                    results.append(file_result)
                    continue
                
                # Perform data quality validation
                quality_report = validator.validate_data_quality(file_path, filename)
                
                # Mark as successful
                file_result['status'] = 'success'
                file_result['file_info'] = file_info
                file_result['quality_report'] = quality_report
                successful_uploads += 1
                
            except FileValidationError as e:
                # Clean up file if it exists
                try:
                    if file_result['file_id']:
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_result['file_id'])
                        if os.path.exists(file_path):
                            os.remove(file_path)
                except:
                    pass
                file_result['error'] = str(e)
                failed_uploads += 1
            except Exception as e:
                # Clean up file if it exists
                try:
                    if file_result['file_id']:
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_result['file_id'])
                        if os.path.exists(file_path):
                            os.remove(file_path)
                except:
                    pass
                file_result['error'] = f'Upload failed: {str(e)}'
                failed_uploads += 1
            
            results.append(file_result)
        
        response = {
            'message': 'Batch upload completed',
            'batch_id': batch_id,
            'total_files': len(files),
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'upload_time': upload_time.isoformat(),
            'results': results
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Batch upload failed: {str(e)}'}), 500

@upload_bp.route('/upload/test', methods=['GET'])
def test_upload():
    """
    Test upload service availability
    ---
    tags:
      - File Upload
    responses:
      200:
        description: Upload service is working
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Upload blueprint is working!"
    """
    return {'message': 'Upload blueprint is working!'}