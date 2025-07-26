from flask import Blueprint, request, jsonify, current_app, send_file
from flasgger import swag_from
import os
import logging
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import pytz
import traceback
import json
import zipfile
from io import BytesIO
from app.services.visualization import WILReportAnalyzer, generate_wil_report_charts
from app.services.validation import DataValidator, validate_filename, FileValidationError
from app.services.cleaning import DataCleaner, clean_wil_data

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    else:
        return obj

visualization_bp = Blueprint('visualization', __name__)

# Set up logging
logger = logging.getLogger(__name__)

def get_australian_time():
    """Get current time in Australian Eastern timezone"""
    aus_tz = pytz.timezone('Australia/Sydney')
    return datetime.now(aus_tz)

def sanitize_output_name(name):
    """Sanitize output name to prevent path traversal and ensure safe filename"""
    if not name:
        return "wil_report"
    
    import re
    sanitized = re.sub(r'[^\w\-_\.]', '_', name)
    sanitized = sanitized[:50].strip('._')
    
    return sanitized if sanitized else "wil_report"

@visualization_bp.route('/analyze/<file_id>', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Generate comprehensive WIL report charts and analysis using uploaded file',
    'description': '''
    Generates comprehensive WIL (Work Integrated Learning) report charts using a previously uploaded file:
    - Year-over-year comparison analysis
    - Faculty and residency status analysis
    - Gender distribution analysis
    - Equity cohort participation analysis
    - CDEV course analysis
    - Statistical summary
    
    This endpoint uses the file_id from the /upload endpoint to avoid duplicate file transmission.
    Workflow: Upload → Validation → Cleaning → Analysis
    ''',
    'consumes': ['application/json'],
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'File ID returned from the upload endpoint'
        },
        {
            'name': 'options',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'output_name': {
                        'type': 'string',
                        'description': 'Custom name for output files (optional)'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Analysis started successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'total_charts': {'type': 'integer'},
                    'download_available': {'type': 'boolean'}
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file_id or parameters',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'File not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        }
    }
})
def analyze_data(file_id):
    """Generate comprehensive WIL report charts and analysis using uploaded file"""
    try:
        # Validate file_id and check if file exists
        if not file_id:
            return jsonify({'error': 'No file_id provided'}), 400
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract original filename from file_id (format: uuid_originalname)
        parts = file_id.split('_', 1)
        if len(parts) < 2:
            return jsonify({'error': 'Invalid file_id format'}), 400
        
        original_filename = parts[1]
        
        # Validate filename using existing service
        is_valid_filename, filename_error = validate_filename(original_filename)
        if not is_valid_filename:
            return jsonify({'error': filename_error}), 400
        
        # Get optional output name from request body
        request_data = request.get_json() or {}
        output_name = sanitize_output_name(request_data.get('output_name', 'wil_report'))
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        timestamp = get_australian_time().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary directories
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', analysis_id)
        cleaned_dir = os.path.join(temp_dir, 'cleaned')
        output_dir = os.path.join(temp_dir, 'charts')
        os.makedirs(cleaned_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # File is already uploaded, no need to save again
        # Use the existing file path directly
        
        # Validate file content using existing service
        try:
            validator = DataValidator()
            file_info, error = validator.validate_file_structure(file_path, original_filename)
            if error:
                raise ValueError(error)
        except (ValueError, FileValidationError) as e:
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Invalid file content',
                'details': str(e)
            }), 400
        
        logger.info(f"Starting WIL analysis for file: {original_filename}, analysis_id: {analysis_id}")
        
        # Clean data using existing service
        try:
            cleaned_df, cleaned_file, report_file = clean_wil_data(
                input_file=file_path,
                output_dir=cleaned_dir,
                fill_missing=True,  # Fill missing values for analysis
                batch_id=analysis_id
            )
            logger.info(f"Data cleaning completed: {cleaned_file}")
        except Exception as e:
            logger.error(f"Data cleaning failed: {str(e)}")
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Data cleaning failed',
                'details': str(e)
            }), 500
        
        # Generate charts and analysis using cleaned data
        results = generate_wil_report_charts(cleaned_file, output_dir)
        
        if not results or not any(results.values()):
            return jsonify({
                'error': 'Failed to generate charts',
                'details': 'No charts were generated. Please check your data format.'
            }), 500
        
        # Create ZIP file with all generated files and save to persistent location
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        zip_filename = f'{output_name}_{timestamp}.zip'
        zip_filepath = os.path.join(analysis_output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all chart files
            for category, files in results.items():
                if isinstance(files, list):
                    for file_path in files:
                        if os.path.exists(file_path):
                            arcname = f"{category}/{os.path.basename(file_path)}"
                            zip_file.write(file_path, arcname)
                elif files and category == 'summary_file':
                    # Add summary JSON file
                    summary_path = os.path.join(output_dir, files)
                    if os.path.exists(summary_path):
                        zip_file.write(summary_path, f"summary/{files}")
            
            # Add a manifest file with analysis details
            manifest = {
                'analysis_id': analysis_id,
                'timestamp': timestamp,
                'original_filename': original_filename,
                'file_id': file_id,
                'output_name': output_name,
                'generated_charts': {
                    category: len(files) if isinstance(files, list) else (1 if files else 0)
                    for category, files in results.items()
                },
                'total_charts': sum(len(files) for files in results.values() if isinstance(files, list))
            }
            
            zip_file.writestr('manifest.json', json.dumps(manifest, indent=2))
        
        # Save analysis metadata for status tracking
        metadata = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'timestamp': timestamp,
            'original_filename': original_filename,
            'file_id': file_id,
            'output_name': output_name,
            'analysis_type': 'full_analysis',
            'zip_filename': zip_filename,
            'total_charts': sum(len(files) for files in results.values() if isinstance(files, list)),
            'completion_time': get_australian_time().isoformat()
        }
        
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        
        logger.info(f"WIL analysis completed successfully: {analysis_id}")
        
        # Return analysis ID and status instead of direct file download
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'completed',
            'message': 'Analysis completed successfully',
            'timestamp': timestamp,
            'total_charts': metadata['total_charts'],
            'download_available': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in WIL analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate analysis',
            'details': str(e)
        }), 500

@visualization_bp.route('/analyze/stats/<file_id>', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Generate statistical summary only (no charts) using uploaded file',
    'description': '''
    Generates only the statistical summary without charts using a previously uploaded file.
    Returns JSON with comprehensive statistics about the WIL data.
    Uses the file_id from the /upload endpoint to avoid duplicate file transmission.
    ''',
    'consumes': ['application/json'],
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'File ID returned from the upload endpoint'
        }
    ],
    'responses': {
        200: {
            'description': 'Statistical analysis completed successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'analysis_type': {'type': 'string'},
                    'results_available': {'type': 'boolean'}
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        }
    }
})
def analyze_stats_only(file_id):
    """Generate statistical summary only without charts using uploaded file"""
    try:
        # Validate file_id and check if file exists
        if not file_id:
            return jsonify({'error': 'No file_id provided'}), 400
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract original filename from file_id
        parts = file_id.split('_', 1)
        if len(parts) < 2:
            return jsonify({'error': 'Invalid file_id format'}), 400
        
        original_filename = parts[1]
        
        # Validate filename using existing service
        is_valid_filename, filename_error = validate_filename(original_filename)
        if not is_valid_filename:
            return jsonify({'error': filename_error}), 400
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        timestamp = get_australian_time().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary directories
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', analysis_id)
        cleaned_dir = os.path.join(temp_dir, 'cleaned')
        os.makedirs(cleaned_dir, exist_ok=True)
        
        # File is already uploaded, no need to save again
        
        # Validate file content using existing service
        try:
            validator = DataValidator()
            file_info, error = validator.validate_file_structure(file_path, original_filename)
            if error:
                raise ValueError(error)
        except (ValueError, FileValidationError) as e:
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Invalid file content',
                'details': str(e)
            }), 400
        
        logger.info(f"Starting statistical analysis for file: {original_filename}, analysis_id: {analysis_id}")
        
        # Clean data using existing service
        try:
            cleaned_df, cleaned_file, report_file = clean_wil_data(
                input_file=file_path,
                output_dir=cleaned_dir,
                fill_missing=True,
                batch_id=analysis_id
            )
        except Exception as e:
            logger.error(f"Data cleaning failed: {str(e)}")
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Data cleaning failed',
                'details': str(e)
            }), 500
        
        # Generate statistics using cleaned data
        analyzer = WILReportAnalyzer(cleaned_file, temp_dir)
        analyzer.load_data()
        summary = analyzer.generate_analysis_summary()
        
        # Save analysis results for later retrieval
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        # Save statistics summary
        stats_filename = f"statistics_{timestamp}.json"
        stats_filepath = os.path.join(analysis_output_dir, stats_filename)
        with open(stats_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Save analysis metadata for status tracking
        metadata = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'timestamp': timestamp,
            'original_filename': original_filename,
            'file_id': file_id,
            'analysis_type': 'statistics_only',
            'stats_filename': stats_filename,
            'completion_time': get_australian_time().isoformat()
        }
        
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        
        logger.info(f"Statistical analysis completed successfully: {analysis_id}")
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'completed',
            'message': 'Statistical analysis completed successfully',
            'timestamp': timestamp,
            'analysis_type': 'statistics_only',
            'results_available': True
        })
        
    except Exception as e:
        logger.error(f"Error in statistical analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate statistical analysis',
            'details': str(e)
        }), 500

@visualization_bp.route('/analyze/preview/<file_id>', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Preview data structure and basic statistics using uploaded file',
    'description': '''
    Returns a preview of the data structure using a previously uploaded file including:
    - Column names and types
    - Sample data rows
    - Basic statistics
    - Data quality assessment
    
    This endpoint helps validate data before running full analysis.
    Uses the file_id from the /upload endpoint to avoid duplicate file transmission.
    ''',
    'consumes': ['application/json'],
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'File ID returned from the upload endpoint'
        },
        {
            'name': 'options',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'rows': {
                        'type': 'integer',
                        'description': 'Number of sample rows to return (default: 5, max: 20)'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Data preview generated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string'},
                    'data_info': {
                        'type': 'object',
                        'properties': {
                            'total_rows': {'type': 'integer'},
                            'total_columns': {'type': 'integer'},
                            'column_names': {'type': 'array', 'items': {'type': 'string'}},
                            'column_types': {'type': 'object'},
                            'missing_values': {'type': 'object'}
                        }
                    },
                    'sample_data': {'type': 'array'},
                    'basic_statistics': {'type': 'object'},
                    'data_quality': {'type': 'object'}
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        }
    }
})
def preview_data(file_id):
    """Preview data structure and basic statistics using uploaded file"""
    try:
        # Validate file_id and check if file exists
        if not file_id:
            return jsonify({'error': 'No file_id provided'}), 400
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract original filename from file_id
        parts = file_id.split('_', 1)
        if len(parts) < 2:
            return jsonify({'error': 'Invalid file_id format'}), 400
        
        original_filename = parts[1]
        
        # Validate filename using existing service
        is_valid_filename, filename_error = validate_filename(original_filename)
        if not is_valid_filename:
            return jsonify({'error': filename_error}), 400
        
        # Get number of rows to preview from request body
        request_data = request.get_json() or {}
        try:
            preview_rows = int(request_data.get('rows', 5))
            preview_rows = max(1, min(preview_rows, 20))  # Limit between 1 and 20
        except (ValueError, TypeError):
            preview_rows = 5
        
        # Generate unique ID for this preview
        preview_id = str(uuid.uuid4())
        
        # Create temporary directory
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', preview_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # File is already uploaded, no need to save again
        
        logger.info(f"Starting data preview for file: {original_filename}")
        
        # Use existing validation service for file structure validation
        try:
            validator = DataValidator()
            file_info, error = validator.validate_file_structure(file_path, original_filename)
            if error:
                raise ValueError(error)
            
            quality_report = validator.validate_data_quality(file_path, original_filename)
        except Exception as e:
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Failed to analyze file',
                'details': str(e)
            }), 500
        
        # Read sample data for preview
        import pandas as pd
        try:
            if original_filename.lower().endswith('.csv'):
                data = pd.read_csv(file_path, nrows=preview_rows)
            elif original_filename.lower().endswith(('.xlsx', '.xls')):
                data = pd.read_excel(file_path, nrows=preview_rows)
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Failed to read file data',
                'details': str(e)
            }), 500
        
        # Generate preview information using existing validation results
        preview_data = {
            'filename': original_filename,
            'file_id': file_id,
            'data_info': file_info,
            'sample_data': data.fillna('').to_dict('records'),
            'quality_report': quality_report
        }
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        
        logger.info(f"Data preview completed successfully for: {original_filename}")
        
        return jsonify(preview_data)
        
    except Exception as e:
        logger.error(f"Error in data preview: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate data preview',
            'details': str(e)
        }), 500

@visualization_bp.route('/health', methods=['GET'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Health check for visualization service',
    'description': 'Check if the visualization service is running and dependencies are available',
    'responses': {
        200: {
            'description': 'Service is healthy',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'service': {'type': 'string'},
                    'dependencies': {'type': 'object'}
                }
            }
        }
    }
})
def health_check():
    """Health check for visualization service"""
    try:
        # Check if required dependencies are available
        dependencies = {}
        
        try:
            import pandas as pd
            dependencies['pandas'] = pd.__version__
        except ImportError:
            dependencies['pandas'] = 'Missing'
        
        try:
            import matplotlib
            dependencies['matplotlib'] = matplotlib.__version__
        except ImportError:
            dependencies['matplotlib'] = 'Missing'
        
        try:
            import numpy as np
            dependencies['numpy'] = np.__version__
        except ImportError:
            dependencies['numpy'] = 'Missing'
        
        # Check if visualization module is importable
        try:
            from app.services.visualization import WILReportAnalyzer
            dependencies['visualization_service'] = 'Available'
        except ImportError as e:
            dependencies['visualization_service'] = f'Error: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'service': 'WIL Data Analysis & Visualization',
            'dependencies': dependencies
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'WIL Data Analysis & Visualization',
            'error': str(e)
        }), 500

@visualization_bp.route('/analyze/multi-file', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Generate analysis using multiple uploaded files for year-on-year comparison',
    'description': '''
    Generates comprehensive WIL report analysis using multiple previously uploaded files.
    This endpoint is designed for year-on-year comparison when data is split across multiple files.
    
    The endpoint:
    - Accepts multiple file_ids from previous uploads
    - Merges the data from all files
    - Performs year-on-year comparison analysis
    - Generates charts optimized for multi-year comparison
    
    This is ideal when users have separate files for different years (e.g., 2024.csv and 2025.csv).
    ''',
    'consumes': ['application/json'],
    'parameters': [
        {
            'name': 'files_data',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'file_ids': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Array of file IDs from previous uploads'
                    },
                    'output_name': {
                        'type': 'string',
                        'description': 'Custom name for output files (optional)'
                    }
                },
                'required': ['file_ids']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Multi-file analysis started successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'files_processed': {'type': 'integer'},
                    'total_charts': {'type': 'integer'},
                    'download_available': {'type': 'boolean'}
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file_ids or parameters'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def analyze_multi_file():
    """Generate comprehensive WIL report analysis using multiple uploaded files"""
    try:
        request_data = request.get_json()
        if not request_data or 'file_ids' not in request_data:
            return jsonify({'error': 'No file_ids provided'}), 400
        
        file_ids = request_data.get('file_ids', [])
        if not isinstance(file_ids, list) or len(file_ids) < 2:
            return jsonify({'error': 'At least 2 file_ids are required for multi-file analysis'}), 400
        
        output_name = sanitize_output_name(request_data.get('output_name', 'multi_year_wil_report'))
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        timestamp = get_australian_time().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary directories
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', analysis_id)
        cleaned_dir = os.path.join(temp_dir, 'cleaned')
        merged_dir = os.path.join(temp_dir, 'merged')
        output_dir = os.path.join(temp_dir, 'charts')
        os.makedirs(cleaned_dir, exist_ok=True)
        os.makedirs(merged_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Validate and process each file
        processed_files = []
        all_dataframes = []
        
        for file_id in file_ids:
            # Validate file_id and check if file exists
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
            if not os.path.exists(file_path):
                # Clean up and return error
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({'error': f'File not found: {file_id}'}), 404
            
            # Extract original filename from file_id
            parts = file_id.split('_', 1)
            if len(parts) < 2:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({'error': f'Invalid file_id format: {file_id}'}), 400
            
            original_filename = parts[1]
            
            # Validate filename using existing service
            is_valid_filename, filename_error = validate_filename(original_filename)
            if not is_valid_filename:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({'error': f'Invalid filename {original_filename}: {filename_error}'}), 400
            
            # Validate file content using existing service
            try:
                validator = DataValidator()
                file_info, error = validator.validate_file_structure(file_path, original_filename)
                if error:
                    raise ValueError(error)
            except (ValueError, FileValidationError) as e:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({
                    'error': f'Invalid file content in {original_filename}',
                    'details': str(e)
                }), 400
            
            # Clean data using existing service
            try:
                cleaned_df, cleaned_file, report_file = clean_wil_data(
                    input_file=file_path,
                    output_dir=cleaned_dir,
                    fill_missing=True,
                    batch_id=f"{analysis_id}_{len(processed_files)}"
                )
                processed_files.append({
                    'file_id': file_id,
                    'original_filename': original_filename,
                    'cleaned_file': cleaned_file,
                    'records': len(cleaned_df)
                })
                all_dataframes.append(cleaned_df)
                logger.info(f"Processed file {original_filename}: {len(cleaned_df)} records")
            except Exception as e:
                logger.error(f"Data cleaning failed for {original_filename}: {str(e)}")
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({
                    'error': f'Data cleaning failed for {original_filename}',
                    'details': str(e)
                }), 500
        
        # Merge all dataframes
        try:
            import pandas as pd
            merged_df = pd.concat(all_dataframes, ignore_index=True)
            
            # Remove any potential duplicates based on MASKED_ID and ACADEMIC_YEAR
            if 'MASKED_ID' in merged_df.columns and 'ACADEMIC_YEAR' in merged_df.columns:
                initial_count = len(merged_df)
                merged_df = merged_df.drop_duplicates(subset=['MASKED_ID', 'ACADEMIC_YEAR'])
                final_count = len(merged_df)
                if initial_count != final_count:
                    logger.info(f"Removed {initial_count - final_count} duplicate records during merge")
            
            # Save merged data
            merged_filename = f"merged_data_{timestamp}.csv"
            merged_filepath = os.path.join(temp_dir, merged_filename)
            merged_df.to_csv(merged_filepath, index=False)
            
            logger.info(f"Merged data saved: {len(merged_df)} total records from {len(file_ids)} files")
            
        except Exception as e:
            logger.error(f"Data merging failed: {str(e)}")
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Data merging failed',
                'details': str(e)
            }), 500
        
        # Generate charts and analysis using merged data
        try:
            results = generate_wil_report_charts(merged_filepath, output_dir)
            
            if not results or not any(results.values()):
                return jsonify({
                    'error': 'Failed to generate charts',
                    'details': 'No charts were generated. Please check your data format.'
                }), 500
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Chart generation failed',
                'details': str(e)
            }), 500
        
        # Create ZIP file with all generated files
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        zip_filename = f'{output_name}_{timestamp}.zip'
        zip_filepath = os.path.join(analysis_output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all chart files
            for category, files in results.items():
                if isinstance(files, list):
                    for file_path in files:
                        if os.path.exists(file_path):
                            arcname = f"{category}/{os.path.basename(file_path)}"
                            zip_file.write(file_path, arcname)
                elif files and category == 'summary_file':
                    summary_path = os.path.join(output_dir, files)
                    if os.path.exists(summary_path):
                        zip_file.write(summary_path, f"summary/{files}")
            
            # Add merged data file
            zip_file.write(merged_filepath, f"data/{merged_filename}")
            
            # Add a detailed manifest file
            manifest = {
                'analysis_id': analysis_id,
                'analysis_type': 'multi_file_comparison',
                'timestamp': timestamp,
                'files_processed': processed_files,
                'total_records': len(merged_df),
                'output_name': output_name,
                'generated_charts': {
                    category: len(files) if isinstance(files, list) else (1 if files else 0)
                    for category, files in results.items()
                },
                'total_charts': sum(len(files) for files in results.values() if isinstance(files, list))
            }
            
            zip_file.writestr('manifest.json', json.dumps(manifest, indent=2))
        
        # Save analysis metadata
        metadata = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'timestamp': timestamp,
            'analysis_type': 'multi_file_comparison',
            'files_processed': processed_files,
            'total_records': len(merged_df),
            'output_name': output_name,
            'zip_filename': zip_filename,
            'total_charts': sum(len(files) for files in results.values() if isinstance(files, list)),
            'completion_time': get_australian_time().isoformat()
        }
        
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        
        logger.info(f"Multi-file WIL analysis completed successfully: {analysis_id}")
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'completed',
            'message': 'Multi-file analysis completed successfully',
            'timestamp': timestamp,
            'files_processed': len(file_ids),
            'total_records': len(merged_df),
            'total_charts': metadata['total_charts'],
            'download_available': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in multi-file WIL analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate multi-file analysis',
            'details': str(e)
        }), 500

@visualization_bp.route('/analyze/pdf-ready/<file_id>', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Generate PDF-optimized analysis package using uploaded file',
    'description': '''
    Generates a comprehensive analysis package specifically optimized for PDF report generation using a previously uploaded file.
    Returns organized charts, metadata, and structured content ready for PDF template integration.
    
    The output includes:
    - High-resolution charts with consistent sizing
    - Structured metadata and content descriptions
    - Ready-to-use text content for PDF templates
    - Chart file mappings and positioning data
    
    Uses the file_id from the /upload endpoint to avoid duplicate file transmission.
    ''',
    'consumes': ['application/json'],
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'File ID returned from the upload endpoint'
        },
        {
            'name': 'options',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'report_title': {
                        'type': 'string',
                        'description': 'Custom title for the PDF report'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'PDF-ready analysis package generated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'analysis_type': {'type': 'string'},
                    'report_title': {'type': 'string'},
                    'download_available': {'type': 'boolean'}
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file or parameters'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def analyze_pdf_ready(file_id):
    """Generate PDF-optimized analysis package for report generation using uploaded file"""
    
    def format_number(value):
        """Safely format a number with comma separators, return as-is if not a number"""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{value:,}"
        return str(value)
    
    try:
        # Validate file_id and check if file exists
        if not file_id:
            return jsonify({'error': 'No file_id provided'}), 400
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract original filename from file_id
        parts = file_id.split('_', 1)
        if len(parts) < 2:
            return jsonify({'error': 'Invalid file_id format'}), 400
        
        original_filename = parts[1]
        
        # Validate filename using existing service
        is_valid_filename, filename_error = validate_filename(original_filename)
        if not is_valid_filename:
            return jsonify({'error': filename_error}), 400
        
        # Get optional report title from request body
        request_data = request.get_json() or {}
        report_title = request_data.get('report_title', 'Work Integrated Learning Data Analysis Report')
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        timestamp = get_australian_time().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary directories with PDF-specific structure
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', analysis_id)
        cleaned_dir = os.path.join(temp_dir, 'cleaned')
        charts_dir = os.path.join(temp_dir, 'charts')
        content_dir = os.path.join(temp_dir, 'content')
        
        os.makedirs(cleaned_dir, exist_ok=True)
        os.makedirs(charts_dir, exist_ok=True)
        os.makedirs(content_dir, exist_ok=True)
        
        # File is already uploaded, no need to save again
        
        # Validate file content using existing service
        try:
            validator = DataValidator()
            file_info, error = validator.validate_file_structure(file_path, original_filename)
            if error:
                raise ValueError(error)
        except (ValueError, FileValidationError) as e:
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Invalid file content',
                'details': str(e)
            }), 400
        
        logger.info(f"Starting PDF-ready WIL analysis for file: {original_filename}, analysis_id: {analysis_id}")
        
        # Clean data using existing service
        try:
            cleaned_df, cleaned_file, report_file = clean_wil_data(
                input_file=file_path,
                output_dir=cleaned_dir,
                fill_missing=True,
                batch_id=analysis_id
            )
        except Exception as e:
            logger.error(f"Data cleaning failed: {str(e)}")
            # Clean up and return error
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Data cleaning failed',
                'details': str(e)
            }), 500
        
        # Generate charts and analysis optimized for PDF using cleaned data
        results = generate_wil_report_charts(cleaned_file, charts_dir)
        
        if not results or not any(results.values()):
            return jsonify({
                'error': 'Failed to generate charts',
                'details': 'No charts were generated. Please check your data format.'
            }), 500
        
        # Load the analyzer to get enhanced summary using cleaned data
        from app.services.visualization import WILReportAnalyzer
        analyzer = WILReportAnalyzer(cleaned_file, charts_dir)
        analyzer.load_data()
        enhanced_summary = analyzer.generate_analysis_summary()
        
        # Create PDF template file
        pdf_template_data = {
            'report_title': report_title,
            'analysis_id': analysis_id,
            'timestamp': timestamp,
            'charts': enhanced_summary.get('pdf_ready_content', {}).get('chart_files', {}),
            'executive_summary': enhanced_summary.get('pdf_ready_content', {}).get('executive_summary', {}),
            'key_metrics': enhanced_summary.get('pdf_ready_content', {}).get('key_metrics', {}),
            'chart_descriptions': enhanced_summary.get('chart_descriptions', {}),
            'key_insights': enhanced_summary.get('key_insights', {}),
            'analysis_tables': enhanced_summary.get('analysis_tables', {}),  # Add analysis_tables to top level
            'full_statistics': enhanced_summary
        }
        
        # Save PDF template data
        template_path = os.path.join(content_dir, 'pdf_template_data.json')
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(convert_numpy_types(pdf_template_data), f, indent=2, ensure_ascii=False)
        
        # Create README for PDF generation team
        readme_content = f"""# WIL Report PDF Generation Package
        
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis ID: {analysis_id}

## Contents:
- `/charts/` - All chart images (PNG, 300 DPI)
- `/content/pdf_template_data.json` - Structured data for PDF templates
- `/content/analysis_summary_{analyzer.date_str}.json` - Complete statistical analysis

## Chart Files:
{chr(10).join([f'- {name}: {file}' for name, file in enhanced_summary.get('pdf_ready_content', {}).get('chart_files', {}).items()])}

## Key Statistics:
- Total Students: {format_number(enhanced_summary.get('key_statistics', {}).get('total_students', 'N/A'))}
- Total Faculties: {enhanced_summary.get('key_statistics', {}).get('total_faculties', 'N/A')}
- Academic Year: {enhanced_summary.get('report_metadata', {}).get('academic_year', 'N/A')}

## Usage:
1. Extract this package
2. Use `pdf_template_data.json` for template population
3. Reference chart files from `/charts/` directory
4. Include key insights and descriptions as needed

For technical details, see the complete analysis in `analysis_summary_{analyzer.date_str}.json`.
"""
        
        readme_path = os.path.join(content_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Create ZIP package optimized for PDF generation
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all chart files to charts directory
            for category, files in results.items():
                if isinstance(files, list):
                    for file_path in files:
                        if os.path.exists(file_path):
                            arcname = f"charts/{os.path.basename(file_path)}"
                            zip_file.write(file_path, arcname)
            
            # Add content files
            zip_file.write(template_path, 'content/pdf_template_data.json')
            zip_file.write(readme_path, 'content/README.md')
            
            # Add complete analysis summary
            if results.get('summary_file'):
                summary_path = os.path.join(charts_dir, results['summary_file'])
                if os.path.exists(summary_path):
                    zip_file.write(summary_path, f'content/{results["summary_file"]}')
        
        # Save ZIP file to persistent location
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        zip_filename = f'wil_pdf_package_{timestamp}.zip'
        zip_filepath = os.path.join(analysis_output_dir, zip_filename)
        
        zip_buffer.seek(0)
        with open(zip_filepath, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        # Save analysis metadata for status tracking
        metadata = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'timestamp': timestamp,
            'original_filename': original_filename,
            'file_id': file_id,
            'analysis_type': 'pdf_ready',
            'report_title': report_title,
            'zip_filename': zip_filename,
            'completion_time': get_australian_time().isoformat()
        }
        
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        
        logger.info(f"PDF-ready WIL analysis completed successfully: {analysis_id}")
        
        # Return analysis ID and status instead of direct file download
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'completed',
            'message': 'PDF-ready analysis completed successfully',
            'timestamp': timestamp,
            'analysis_type': 'pdf_ready',
            'report_title': report_title,
            'download_available': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in PDF-ready analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate PDF-ready analysis',
            'details': str(e)
        }), 500


# Backward compatibility route for old analyze endpoint
@visualization_bp.route('/analyze', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': '[DEPRECATED] Use /analyze/<file_id> instead',
    'description': '''
    DEPRECATED: This endpoint is maintained for backward compatibility only.
    Please use the new /analyze/<file_id> endpoint instead.
    
    This endpoint still accepts file uploads but is less efficient due to duplicate file transmission.
    ''',
    'deprecated': True
})
def analyze_data_deprecated():
    """Deprecated analyze endpoint - redirects to upload then analyze workflow"""
    return jsonify({
        'error': 'This endpoint is deprecated',
        'message': 'Please use the new workflow: 1) Upload file to /upload to get file_id, 2) Use /analyze/<file_id> for analysis',
        'new_endpoints': {
            'upload': '/api/upload',
            'analyze': '/api/analyze/<file_id>',
            'stats': '/api/analyze/stats/<file_id>',
            'preview': '/api/analyze/preview/<file_id>',
            'pdf_ready': '/api/analyze/pdf-ready/<file_id>'
        }
    }), 410  # HTTP 410 Gone


@visualization_bp.route('/status/<analysis_id>', methods=['GET'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Get analysis status and progress',
    'description': 'Check the status of a data analysis operation using analysis_id',
    'parameters': [
        {
            'name': 'analysis_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Analysis ID returned from analysis request'
        }
    ],
    'responses': {
        200: {
            'description': 'Status retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['processing', 'completed', 'failed']},
                    'message': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'analysis_type': {'type': 'string'},
                    'progress': {'type': 'object'},
                    'results_available': {'type': 'boolean'},
                    'download_available': {'type': 'boolean'}
                }
            }
        },
        404: {
            'description': 'Analysis ID not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def get_analysis_status(analysis_id):
    """Get status of analysis operation"""
    try:
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return jsonify({
                'error': 'Analysis ID not found'
            }), 404
        
        # Read metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        logger.info(f"Status check for analysis: {analysis_id}")
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': metadata.get('status', 'unknown'),
            'message': f"Analysis {metadata.get('status', 'unknown')}",
            'timestamp': metadata.get('timestamp'),
            'analysis_type': metadata.get('analysis_type'),
            'original_filename': metadata.get('original_filename'),
            'completion_time': metadata.get('completion_time'),
            'results_available': metadata.get('status') == 'completed',
            'download_available': metadata.get('status') == 'completed' and (
                'zip_filename' in metadata or 'stats_filename' in metadata
            )
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        return jsonify({
            'error': 'Failed to get analysis status',
            'details': str(e)
        }), 500


@visualization_bp.route('/download/<analysis_id>', methods=['GET'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Download analysis results',
    'description': 'Download the analysis results (ZIP file) using analysis_id',
    'parameters': [
        {
            'name': 'analysis_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Analysis ID returned from analysis request'
        }
    ],
    'responses': {
        200: {
            'description': 'File download successful',
            'content': {
                'application/zip': {
                    'schema': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        404: {
            'description': 'Analysis ID or file not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def download_analysis_results(analysis_id):
    """Download analysis results file"""
    try:
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return jsonify({
                'error': 'Analysis ID not found'
            }), 404
        
        # Read metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if metadata.get('status') != 'completed':
            return jsonify({
                'error': 'Analysis not completed yet'
            }), 400
        
        # Determine file to download based on analysis type
        zip_filename = metadata.get('zip_filename')
        if zip_filename:
            file_path = os.path.join(analysis_output_dir, zip_filename)
            if os.path.exists(file_path):
                logger.info(f"Downloading analysis results: {analysis_id}")
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=zip_filename
                )
        
        return jsonify({
            'error': 'Download file not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Error downloading analysis results: {str(e)}")
        return jsonify({
            'error': 'Failed to download analysis results',
            'details': str(e)
        }), 500


@visualization_bp.route('/results/<analysis_id>', methods=['GET'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Get analysis results as JSON',
    'description': 'Get the analysis results in JSON format using analysis_id (for statistics-only analyses)',
    'parameters': [
        {
            'name': 'analysis_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Analysis ID returned from analysis request'
        }
    ],
    'responses': {
        200: {
            'description': 'Results retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'analysis_type': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'results': {'type': 'object'},
                    'metadata': {'type': 'object'}
                }
            }
        },
        404: {
            'description': 'Analysis ID or results not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def get_analysis_results(analysis_id):
    """Get analysis results in JSON format"""
    try:
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return jsonify({
                'error': 'Analysis ID not found'
            }), 404
        
        # Read metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if metadata.get('status') != 'completed':
            return jsonify({
                'error': 'Analysis not completed yet'
            }), 400
        
        response_data = {
            'analysis_id': analysis_id,
            'analysis_type': metadata.get('analysis_type'),
            'timestamp': metadata.get('timestamp'),
            'completion_time': metadata.get('completion_time'),
            'original_filename': metadata.get('original_filename'),
            'metadata': metadata
        }
        
        # For statistics-only analyses, include the actual results
        if metadata.get('analysis_type') == 'statistics_only':
            stats_filename = metadata.get('stats_filename')
            if stats_filename:
                stats_path = os.path.join(analysis_output_dir, stats_filename)
                if os.path.exists(stats_path):
                    with open(stats_path, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                    response_data['results'] = results
        
        # For chart analyses, provide summary information
        elif metadata.get('analysis_type') in ['full_analysis', 'pdf_ready']:
            response_data['charts_info'] = {
                'total_charts': metadata.get('total_charts', 0),
                'download_available': True,
                'zip_filename': metadata.get('zip_filename')
            }
        
        logger.info(f"Retrieved analysis results: {analysis_id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting analysis results: {str(e)}")
        return jsonify({
            'error': 'Failed to get analysis results',
            'details': str(e)
        }), 500


@visualization_bp.route('/analyze/multi-file/pdf-ready', methods=['POST'])
@swag_from({
    'tags': ['Data Analysis & Visualization'],
    'summary': 'Generate PDF-optimized analysis package using multiple uploaded files',
    'description': '''
    Generates a comprehensive PDF-optimized analysis package using multiple previously uploaded files.
    This endpoint is designed for year-on-year comparison when data is split across multiple files,
    specifically optimized for PDF report generation.
    
    The endpoint:
    - Accepts multiple file_ids from previous uploads
    - Merges the data from all files for multi-year analysis
    - Generates charts optimized for year-on-year comparison
    - Returns organized charts, metadata, and structured content ready for PDF template integration
    
    The output includes:
    - High-resolution charts with consistent sizing optimized for multi-year comparison
    - Structured metadata and content descriptions
    - Ready-to-use text content for PDF templates
    - Chart file mappings and positioning data
    
    This is ideal when users have separate files for different years (e.g., 2024.csv and 2025.csv)
    and need PDF-ready output.
    ''',
    'consumes': ['application/json'],
    'parameters': [
        {
            'name': 'files_data',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'file_ids': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Array of file IDs from previous uploads'
                    },
                    'report_title': {
                        'type': 'string',
                        'description': 'Custom title for the PDF report (optional)'
                    },
                    'output_name': {
                        'type': 'string',
                        'description': 'Custom name for output files (optional)'
                    }
                },
                'required': ['file_ids']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Multi-file PDF-ready analysis started successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'analysis_id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'timestamp': {'type': 'string'},
                    'files_processed': {'type': 'integer'},
                    'total_records': {'type': 'integer'},
                    'analysis_type': {'type': 'string'},
                    'report_title': {'type': 'string'},
                    'download_available': {'type': 'boolean'}
                }
            }
        },
        400: {
            'description': 'Bad request - invalid file_ids or parameters'
        },
        500: {
            'description': 'Internal server error'
        }
    }
})
def analyze_multi_file_pdf_ready():
    """Generate PDF-optimized analysis package using multiple uploaded files"""
    
    def format_number(value):
        """Safely format a number with comma separators, return as-is if not a number"""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{value:,}"
        return str(value)
    
    try:
        request_data = request.get_json()
        if not request_data or 'file_ids' not in request_data:
            return jsonify({'error': 'No file_ids provided'}), 400
        
        file_ids = request_data.get('file_ids', [])
        if not isinstance(file_ids, list) or len(file_ids) < 2:
            return jsonify({'error': 'At least 2 file_ids are required for multi-file analysis'}), 400
        
        report_title = request_data.get('report_title', 'Multi-Year Work Integrated Learning Data Analysis Report')
        output_name = sanitize_output_name(request_data.get('output_name', 'multi_year_wil_pdf_report'))
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        timestamp = get_australian_time().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary directories with PDF-specific structure
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', analysis_id)
        cleaned_dir = os.path.join(temp_dir, 'cleaned')
        charts_dir = os.path.join(temp_dir, 'charts')
        content_dir = os.path.join(temp_dir, 'content')
        
        os.makedirs(cleaned_dir, exist_ok=True)
        os.makedirs(charts_dir, exist_ok=True)
        os.makedirs(content_dir, exist_ok=True)
        
        # Validate and process each file
        processed_files = []
        all_dataframes = []
        
        for file_id in file_ids:
            # Validate file_id and check if file exists
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
            if not os.path.exists(file_path):
                # Clean up and return error
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({'error': f'File not found: {file_id}'}), 404
            
            # Extract original filename from file_id
            parts = file_id.split('_', 1)
            if len(parts) < 2:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({'error': f'Invalid file_id format: {file_id}'}), 400
            
            original_filename = parts[1]
            
            # Validate filename using existing service
            is_valid_filename, filename_error = validate_filename(original_filename)
            if not is_valid_filename:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({'error': f'Invalid filename {original_filename}: {filename_error}'}), 400
            
            # Validate file content using existing service
            try:
                validator = DataValidator()
                file_info, error = validator.validate_file_structure(file_path, original_filename)
                if error:
                    raise ValueError(error)
            except (ValueError, FileValidationError) as e:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({
                    'error': f'Invalid file content in {original_filename}',
                    'details': str(e)
                }), 400
            
            # Clean data using existing service
            try:
                cleaned_df, cleaned_file, report_file = clean_wil_data(
                    input_file=file_path,
                    output_dir=cleaned_dir,
                    fill_missing=True,
                    batch_id=f"{analysis_id}_{len(processed_files)}"
                )
                processed_files.append({
                    'file_id': file_id,
                    'original_filename': original_filename,
                    'cleaned_file': cleaned_file,
                    'records': len(cleaned_df)
                })
                all_dataframes.append(cleaned_df)
                logger.info(f"Processed file {original_filename}: {len(cleaned_df)} records")
            except Exception as e:
                logger.error(f"Data cleaning failed for {original_filename}: {str(e)}")
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                return jsonify({
                    'error': f'Data cleaning failed for {original_filename}',
                    'details': str(e)
                }), 500
        
        # Merge all dataframes
        try:
            import pandas as pd
            merged_df = pd.concat(all_dataframes, ignore_index=True)
            
            # Remove any potential duplicates based on MASKED_ID and ACADEMIC_YEAR
            if 'MASKED_ID' in merged_df.columns and 'ACADEMIC_YEAR' in merged_df.columns:
                initial_count = len(merged_df)
                merged_df = merged_df.drop_duplicates(subset=['MASKED_ID', 'ACADEMIC_YEAR'])
                final_count = len(merged_df)
                if initial_count != final_count:
                    logger.info(f"Removed {initial_count - final_count} duplicate records during merge")
            
            # Save merged data
            merged_filename = f"merged_data_{timestamp}.csv"
            merged_filepath = os.path.join(temp_dir, merged_filename)
            merged_df.to_csv(merged_filepath, index=False)
            
            logger.info(f"Merged data saved: {len(merged_df)} total records from {len(file_ids)} files")
            
        except Exception as e:
            logger.error(f"Data merging failed: {str(e)}")
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Data merging failed',
                'details': str(e)
            }), 500
        
        # Generate charts and analysis using merged data
        try:
            results = generate_wil_report_charts(merged_filepath, charts_dir)
            
            if not results or not any(results.values()):
                return jsonify({
                    'error': 'Failed to generate charts',
                    'details': 'No charts were generated. Please check your data format.'
                }), 500
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            return jsonify({
                'error': 'Chart generation failed',
                'details': str(e)
            }), 500
        
        # Load the analyzer to get enhanced summary using merged data
        from app.services.visualization import WILReportAnalyzer
        analyzer = WILReportAnalyzer(merged_filepath, charts_dir)
        analyzer.load_data()
        enhanced_summary = analyzer.generate_analysis_summary()
        
        # Create PDF template file optimized for multi-year comparison
        pdf_template_data = {
            'report_title': report_title,
            'analysis_id': analysis_id,
            'analysis_type': 'multi_file_pdf_ready',
            'timestamp': timestamp,
            'files_processed': processed_files,
            'total_records': len(merged_df),
            'charts': enhanced_summary.get('pdf_ready_content', {}).get('chart_files', {}),
            'executive_summary': enhanced_summary.get('pdf_ready_content', {}).get('executive_summary', {}),
            'key_metrics': enhanced_summary.get('pdf_ready_content', {}).get('key_metrics', {}),
            'chart_descriptions': enhanced_summary.get('chart_descriptions', {}),
            'key_insights': enhanced_summary.get('key_insights', {}),
            'analysis_tables': enhanced_summary.get('analysis_tables', {}),  # Add analysis_tables to top level for multi-year
            'multi_year_insights': {
                'years_analyzed': sorted(merged_df['ACADEMIC_YEAR'].unique().tolist()) if 'ACADEMIC_YEAR' in merged_df.columns else [],
                'total_files_processed': len(file_ids),
                'comparison_type': 'year_on_year'
            },
            'full_statistics': enhanced_summary
        }
        
        # Save PDF template data
        template_path = os.path.join(content_dir, 'pdf_template_data.json')
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(convert_numpy_types(pdf_template_data), f, indent=2, ensure_ascii=False)
        
        # Create README for PDF generation team with multi-file specific information
        years_analyzed = pdf_template_data['multi_year_insights']['years_analyzed']
        readme_content = f"""# Multi-Year WIL Report PDF Generation Package

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis ID: {analysis_id}
Analysis Type: Multi-File Year-on-Year Comparison

## Multi-Year Analysis Details:
- Files Processed: {len(file_ids)}
- Years Analyzed: {', '.join(map(str, years_analyzed))}
- Total Records: {len(merged_df):,}
- Comparison Type: Year-on-Year Analysis

## File Sources:
{chr(10).join([f'- {f["original_filename"]}: {f["records"]:,} records' for f in processed_files])}

## Contents:
- `/charts/` - All chart images (PNG, 300 DPI) optimized for multi-year comparison
- `/content/pdf_template_data.json` - Structured data for PDF templates with multi-year insights
- `/content/analysis_summary_{analyzer.date_str}.json` - Complete statistical analysis

## Chart Files:
{chr(10).join([f'- {name}: {file}' for name, file in enhanced_summary.get('pdf_ready_content', {}).get('chart_files', {}).items()])}

## Key Multi-Year Statistics:
- Total Students: {format_number(enhanced_summary.get('key_statistics', {}).get('total_students', 'N/A'))}
- Total Faculties: {enhanced_summary.get('key_statistics', {}).get('total_faculties', 'N/A')}
- Years Covered: {years_analyzed[0] if years_analyzed else 'N/A'} - {years_analyzed[-1] if len(years_analyzed) > 1 else 'N/A'}

## Usage:
1. Extract this package
2. Use `pdf_template_data.json` for template population
3. Reference chart files from `/charts/` directory
4. Utilize multi_year_insights for year-on-year analysis context
5. Include key insights and descriptions as needed

## Multi-Year Features:
- Year-on-year comparison charts
- Trend analysis across multiple years
- Consolidated statistics from all files
- Duplicate removal based on MASKED_ID and ACADEMIC_YEAR

For technical details, see the complete analysis in `analysis_summary_{analyzer.date_str}.json`.
"""
        
        readme_path = os.path.join(content_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Create ZIP package optimized for PDF generation
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all chart files to charts directory
            for category, files in results.items():
                if isinstance(files, list):
                    for file_path in files:
                        if os.path.exists(file_path):
                            arcname = f"charts/{os.path.basename(file_path)}"
                            zip_file.write(file_path, arcname)
            
            # Add content files
            zip_file.write(template_path, 'content/pdf_template_data.json')
            zip_file.write(readme_path, 'content/README.md')
            
            # Add complete analysis summary
            if results.get('summary_file'):
                summary_path = os.path.join(charts_dir, results['summary_file'])
                if os.path.exists(summary_path):
                    zip_file.write(summary_path, f'content/{results["summary_file"]}')
        
        # Save ZIP file to persistent location
        analysis_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        zip_filename = f'{output_name}_pdf_package_{timestamp}.zip'
        zip_filepath = os.path.join(analysis_output_dir, zip_filename)
        
        zip_buffer.seek(0)
        with open(zip_filepath, 'wb') as f:
            f.write(zip_buffer.getvalue())
        
        # Save analysis metadata for status tracking
        metadata = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'timestamp': timestamp,
            'analysis_type': 'multi_file_pdf_ready',
            'files_processed': processed_files,
            'total_records': len(merged_df),
            'report_title': report_title,
            'output_name': output_name,
            'zip_filename': zip_filename,
            'years_analyzed': years_analyzed,
            'completion_time': get_australian_time().isoformat()
        }
        
        metadata_path = os.path.join(analysis_output_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")
        
        logger.info(f"Multi-file PDF-ready WIL analysis completed successfully: {analysis_id}")
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'completed',
            'message': 'Multi-file PDF-ready analysis completed successfully',
            'timestamp': timestamp,
            'files_processed': len(file_ids),
            'total_records': len(merged_df),
            'analysis_type': 'multi_file_pdf_ready',
            'report_title': report_title,
            'years_analyzed': years_analyzed,
            'download_available': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in multi-file PDF-ready analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate multi-file PDF-ready analysis',
            'details': str(e)
        }), 500