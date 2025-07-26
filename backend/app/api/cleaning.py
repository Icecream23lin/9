from flask import Blueprint, request, jsonify, current_app, send_file
from flasgger import swag_from
import os
import logging
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import pytz
import traceback
from app.services.cleaning import DataCleaner, clean_wil_data, clean_multiple_wil_data

cleaning_bp = Blueprint('cleaning', __name__)

# Set up logging
logger = logging.getLogger(__name__)

def get_australian_time():
    """Get current time in Australian Eastern timezone"""
    aus_tz = pytz.timezone('Australia/Sydney')
    return datetime.now(aus_tz)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['csv', 'xlsx', 'xls']

@cleaning_bp.route('/clean', methods=['POST'])
@swag_from({
    'tags': ['Data Cleaning'],
    'summary': 'Clean uploaded data file',
    'description': 'Upload a CSV or Excel file and perform comprehensive data cleaning operations',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'CSV or Excel file to be cleaned'
        },
        {
            'name': 'fill_missing',
            'in': 'formData',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Whether to fill missing values (numeric: 0, categorical: Unknown)'
        },
        {
            'name': 'batch_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Custom batch identifier for output files'
        }
    ],
    'responses': {
        200: {
            'description': 'Data cleaning completed successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'original_records': {'type': 'integer'},
                            'cleaned_records': {'type': 'integer'},
                            'removed_records': {'type': 'integer'},
                            'columns_count': {'type': 'integer'},
                            'cleaning_summary': {'type': 'object'},
                            'file_info': {
                                'type': 'object',
                                'properties': {
                                    'cleaned_file': {'type': 'string'},
                                    'report_file': {'type': 'string'},
                                    'file_id': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file or parameters',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error during cleaning process',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        }
    }
})
def clean_data():
    """Clean uploaded CSV data"""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            logger.warning("No file provided in cleaning request")
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'details': 'Please upload a CSV file'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning("Empty filename in cleaning request")
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'details': 'Please select a file to upload'
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'details': 'Only CSV, XLSX, and XLS files are allowed'
            }), 400
        
        # Get optional parameters
        fill_missing = request.form.get('fill_missing', 'false').lower() == 'true'
        batch_id = request.form.get('batch_id', None)
        
        # Generate unique file ID and secure filename
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        temp_filename = f"{file_id}_{original_filename}"
        
        # Save uploaded file temporarily
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(upload_path)
        
        logger.info(f"File uploaded successfully: {temp_filename}, fill_missing: {fill_missing}")
        
        # Create output directory for this cleaning session
        output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"cleaned_{file_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Perform data cleaning
        try:
            cleaned_df, cleaned_file, report_file = clean_wil_data(
                input_file=upload_path,
                output_dir=output_dir,
                fill_missing=fill_missing,
                batch_id=batch_id
            )
            
            # Extract cleaning statistics
            original_records = None
            cleaned_records = len(cleaned_df)
            columns_count = len(cleaned_df.columns)
            
            # Read the cleaning log for summary
            cleaning_summary = {
                'missing_values_filled': fill_missing,
                'batch_id': batch_id,
                'processing_time': get_australian_time().isoformat()
            }
            
            # Try to extract original record count from report
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                    for line in report_content.split('\n'):
                        if 'Original records:' in line:
                            original_records = int(line.split(':')[1].strip().replace(',', ''))
                            break
            except:
                logger.warning("Could not extract original record count from report")
            
            removed_records = (original_records - cleaned_records) if original_records else 0
            
            # Prepare response data
            response_data = {
                'success': True,
                'message': 'Data cleaning completed successfully',
                'data': {
                    'original_records': original_records,
                    'cleaned_records': cleaned_records,
                    'removed_records': removed_records,
                    'columns_count': columns_count,
                    'cleaning_summary': cleaning_summary,
                    'file_info': {
                        'cleaned_file': os.path.basename(cleaned_file),
                        'report_file': os.path.basename(report_file),
                        'file_id': file_id
                    }
                }
            }
            
            logger.info(f"Data cleaning completed successfully for file_id: {file_id}")
            
            # Clean up temporary upload file
            try:
                os.remove(upload_path)
            except:
                logger.warning(f"Could not remove temporary file: {upload_path}")
            
            return jsonify(response_data), 200
            
        except Exception as cleaning_error:
            logger.error(f"Data cleaning failed: {str(cleaning_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Clean up files on error
            try:
                os.remove(upload_path)
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': 'Data cleaning failed',
                'details': str(cleaning_error)
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in clean_data: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'details': 'An unexpected error occurred during data cleaning'
        }), 500


@cleaning_bp.route('/download/<file_id>/<file_type>', methods=['GET'])
@swag_from({
    'tags': ['Data Cleaning'],
    'summary': 'Download cleaned data or report file',
    'description': 'Download the cleaned CSV file or cleaning report',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'File ID returned from cleaning operation'
        },
        {
            'name': 'file_type',
            'in': 'path',
            'type': 'string',
            'required': True,
            'enum': ['data', 'report'],
            'description': 'Type of file to download (data or report)'
        }
    ],
    'responses': {
        200: {
            'description': 'File download successful',
            'content': {
                'application/octet-stream': {
                    'schema': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        404: {
            'description': 'File not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def download_file(file_id, file_type):
    """Download cleaned data or report file"""
    try:
        # Validate file type first
        if file_type not in ['data', 'report']:
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Use "data" or "report"'
            }), 400
        
        # Determine file path based on type
        base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"cleaned_{file_id}")
        
        # Check if directory exists
        if not os.path.exists(base_dir):
            return jsonify({
                'success': False,
                'error': 'File ID not found'
            }), 404
        
        if file_type == 'data':
            # Find the cleaned CSV file
            for filename in os.listdir(base_dir):
                if filename.endswith('_cleaned.csv'):
                    file_path = os.path.join(base_dir, filename)
                    break
            else:
                return jsonify({
                    'success': False,
                    'error': 'Cleaned data file not found'
                }), 404
                
        elif file_type == 'report':
            # Find the report file
            for filename in os.listdir(base_dir):
                if filename.startswith('data_cleaning_report_') and filename.endswith('.txt'):
                    file_path = os.path.join(base_dir, filename)
                    break
            else:
                return jsonify({
                    'success': False,
                    'error': 'Cleaning report file not found'
                }), 404
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        logger.info(f"Downloading file: {file_path}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Download failed',
            'details': str(e)
        }), 500


@cleaning_bp.route('/status/<file_id>', methods=['GET'])
@swag_from({
    'tags': ['Data Cleaning'],
    'summary': 'Get cleaning operation status',
    'description': 'Check the status of a data cleaning operation',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'File ID from cleaning operation'
        }
    ],
    'responses': {
        200: {
            'description': 'Status retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'file_id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'files_available': {
                        'type': 'object',
                        'properties': {
                            'cleaned_data': {'type': 'boolean'},
                            'cleaning_report': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        404: {
            'description': 'File ID not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def get_cleaning_status(file_id):
    """Get status of cleaning operation"""
    try:
        base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"cleaned_{file_id}")
        
        if not os.path.exists(base_dir):
            return jsonify({
                'success': False,
                'error': 'File ID not found'
            }), 404
        
        # Check which files are available
        files = os.listdir(base_dir)
        cleaned_data_available = any(f.endswith('_cleaned.csv') for f in files)
        report_available = any(f.startswith('data_cleaning_report_') for f in files)
        
        status = 'completed' if (cleaned_data_available and report_available) else 'partial'
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'status': status,
            'files_available': {
                'cleaned_data': cleaned_data_available,
                'cleaning_report': report_available
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cleaning status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Status check failed',
            'details': str(e)
        }), 500


@cleaning_bp.route('/validate', methods=['POST'])
@swag_from({
    'tags': ['Data Cleaning'],
    'summary': 'Validate data file for cleaning',
    'description': 'Upload and validate a CSV or Excel file to check if it can be cleaned',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'CSV or Excel file to validate'
        }
    ],
    'responses': {
        200: {
            'description': 'File validation completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'valid': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'file_info': {
                        'type': 'object',
                        'properties': {
                            'filename': {'type': 'string'},
                            'size': {'type': 'integer'},
                            'rows': {'type': 'integer'},
                            'columns': {'type': 'integer'},
                            'column_names': {'type': 'array', 'items': {'type': 'string'}}
                        }
                    },
                    'validation_issues': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        400: {
            'description': 'Validation failed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        }
    }
})
def validate_file():
    """Validate CSV file for data cleaning"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'details': 'Only CSV, XLSX, and XLS files are allowed'
            }), 400
        
        # Save file temporarily for validation
        file_id = str(uuid.uuid4())
        temp_filename = f"validate_{file_id}_{secure_filename(file.filename)}"
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(temp_path)
        
        try:
            # Create cleaner instance and try to read the file
            cleaner = DataCleaner()
            df = cleaner.read_data(temp_path)
            
            validation_issues = []
            is_valid = True
            
            # Basic validation checks
            if df.empty:
                validation_issues.append("File is empty")
                is_valid = False
            
            if len(df.columns) == 0:
                validation_issues.append("No columns found")
                is_valid = False
            
            # Check for required columns (basic WIL data structure)
            expected_columns = ['ACADEMIC_YEAR', 'TERM', 'COURSE_CODE', 'MASKED_ID']
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                validation_issues.append(f"Missing expected columns: {', '.join(missing_columns)}")
                is_valid = False
            
            file_info = {
                'filename': file.filename,
                'size': os.path.getsize(temp_path),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist()
            }
            
            message = "File is valid for cleaning" if is_valid else "File has validation issues"
            
            return jsonify({
                'success': True,
                'valid': is_valid,
                'message': message,
                'file_info': file_info,
                'validation_issues': validation_issues
            }), 200
            
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': str(e)
        }), 500


@cleaning_bp.route('/clean/batch', methods=['POST'])
@swag_from({
    'tags': ['Data Cleaning'],
    'summary': 'Clean multiple uploaded data files in batch',
    'description': 'Upload multiple CSV or Excel files and perform comprehensive data cleaning operations on all files',
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'files',
            'in': 'formData',
            'type': 'array',
            'items': {'type': 'file'},
            'required': True,
            'description': 'Multiple CSV or Excel files to be cleaned'
        },
        {
            'name': 'fill_missing',
            'in': 'formData',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Whether to fill missing values (numeric: 0, categorical: Unknown)'
        },
        {
            'name': 'batch_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Custom batch identifier for output files'
        }
    ],
    'responses': {
        200: {
            'description': 'Batch data cleaning completed',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'batch_id': {'type': 'string'},
                    'total_files': {'type': 'integer'},
                    'successful_cleanings': {'type': 'integer'},
                    'failed_cleanings': {'type': 'integer'},
                    'processing_time': {'type': 'string'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'original_filename': {'type': 'string'},
                                'file_id': {'type': 'string'},
                                'status': {'type': 'string', 'enum': ['success', 'failed']},
                                'error': {'type': 'string'},
                                'data': {
                                    'type': 'object',
                                    'properties': {
                                        'original_records': {'type': 'integer'},
                                        'cleaned_records': {'type': 'integer'},
                                        'removed_records': {'type': 'integer'},
                                        'columns_count': {'type': 'integer'},
                                        'file_info': {
                                            'type': 'object',
                                            'properties': {
                                                'cleaned_file': {'type': 'string'},
                                                'report_file': {'type': 'string'}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request - no files provided',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error during batch cleaning',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        }
    }
})
def clean_batch():
    """Clean multiple uploaded files in batch"""
    try:
        # Check if files are present in request
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided for batch cleaning'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files provided for batch cleaning'
            }), 400
        
        # Get optional parameters
        fill_missing = request.form.get('fill_missing', 'false').lower() == 'true'
        batch_id = request.form.get('batch_id', None)
        
        if batch_id is None:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        start_time = get_australian_time()
        logger.info(f"Starting batch cleaning for {len(files)} files with batch_id: {batch_id}")
        
        # Process each file and save temporarily
        temp_files = []
        file_ids = []
        
        for file in files:
            # Validate each file
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                continue
            
            # Generate unique file ID and save temporarily
            file_id = str(uuid.uuid4())
            original_filename = secure_filename(file.filename)
            temp_filename = f"{batch_id}_{file_id}_{original_filename}"
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
            
            file.save(temp_path)
            temp_files.append(temp_path)
            file_ids.append(file_id)
        
        if not temp_files:
            return jsonify({
                'success': False,
                'error': 'No valid files found for cleaning'
            }), 400
        
        # Create batch output directory
        batch_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f"batch_cleaned_{batch_id}")
        os.makedirs(batch_output_dir, exist_ok=True)
        
        # Perform batch cleaning
        try:
            cleaning_results = clean_multiple_wil_data(
                input_files=temp_files,
                output_dir=batch_output_dir,
                fill_missing=fill_missing,
                batch_id=batch_id
            )
            
            # Process results and create response
            results = []
            successful_cleanings = 0
            failed_cleanings = 0
            
            for i, result in enumerate(cleaning_results):
                file_id = file_ids[i]
                original_filename = os.path.basename(temp_files[i]).split('_', 2)[-1]  # Extract original filename
                
                file_result = {
                    'original_filename': original_filename,
                    'file_id': file_id,
                    'status': result['status'],
                    'error': result.get('error'),
                    'data': None
                }
                
                if result['status'] == 'success':
                    successful_cleanings += 1
                    
                    # Extract statistics from cleaned dataframe
                    cleaned_df = result['cleaned_df']
                    original_records = None
                    cleaned_records = len(cleaned_df)
                    
                    # Try to extract original record count from report
                    try:
                        with open(result['report_file'], 'r', encoding='utf-8') as f:
                            report_content = f.read()
                            for line in report_content.split('\n'):
                                if 'Original records:' in line:
                                    original_records = int(line.split(':')[1].strip().replace(',', ''))
                                    break
                    except:
                        pass
                    
                    removed_records = (original_records - cleaned_records) if original_records else 0
                    
                    file_result['data'] = {
                        'original_records': original_records,
                        'cleaned_records': cleaned_records,
                        'removed_records': removed_records,
                        'columns_count': len(cleaned_df.columns),
                        'file_info': {
                            'cleaned_file': os.path.basename(result['cleaned_file']),
                            'report_file': os.path.basename(result['report_file'])
                        }
                    }
                else:
                    failed_cleanings += 1
                
                results.append(file_result)
            
            # Calculate processing time
            end_time = get_australian_time()
            processing_time = (end_time - start_time).total_seconds()
            
            response_data = {
                'success': True,
                'message': 'Batch data cleaning completed',
                'batch_id': batch_id,
                'total_files': len(files),
                'successful_cleanings': successful_cleanings,
                'failed_cleanings': failed_cleanings,
                'processing_time': f"{processing_time:.2f} seconds",
                'results': results
            }
            
            logger.info(f"Batch cleaning completed: {successful_cleanings} successful, {failed_cleanings} failed")
            
            return jsonify(response_data), 200
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    logger.warning(f"Could not remove temporary file: {temp_file}")
                    pass
            
    except Exception as e:
        logger.error(f"Unexpected error in batch cleaning: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Clean up temporary files in case of error
        if 'temp_files' in locals():
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        return jsonify({
            'success': False,
            'error': 'Batch cleaning failed',
            'details': str(e)
        }), 500