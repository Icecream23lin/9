
import os
import json
import logging
import base64
import tempfile
import requests
from io import BytesIO
from flask import Blueprint, jsonify, current_app, send_file, request
from flasgger import swag_from
from app.services.pdf_generator import process_single_file, process_multiple_files


report_bp = Blueprint('report', __name__)

@report_bp.route('/api/analyze/pdf-ready/<file_id>', methods=['GET'])
def mock_analysis(file_id):
    return jsonify({"analysis_id": f"mock-analysis-id-{file_id}"})


@report_bp.route('/report/test', methods=['GET'])
@swag_from({
    'tags': ['Report'],
    'summary': 'Test report API endpoint',
    'description': 'Simple test endpoint to verify report API is working',
    'responses': {
        '200': {
            'description': 'Report API is working',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {
                        'type': 'string',
                        'example': 'Report blueprint is working!'
                    }
                }
            }
        }
    }
})
def test_report():
    return {'message': 'Report blueprint is working!'}

# --- Single file route ---
@report_bp.route('/report/generate/<file_id>', methods=['POST'])
@swag_from({
    'tags': ['Report'],
    'summary': 'Generate PDF report from uploaded file',
    'description': 'Generate a PDF report with data analysis and visualizations from uploaded CSV file using file ID',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Unique ID of the uploaded file',
            'example': '4a329ae9-9553-4b54-90b7-a915cd26afc8'
        }
    ],
    'responses': {
        '200': {
            'description': 'PDF report file generated successfully',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'file_id': {'type': 'string'},
                            'analysis_id': {'type': 'string'},
                            'download_url': {'type': 'string'},
                            'pdf_base64': {'type': 'string'},
                            'success': {'type': 'boolean'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': 'Failed to generate report',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'error': {'type': 'string'},
                            'details': {'type': 'string'},
                            'success': {'type': 'boolean'}
                        }
                    }
                }
            }
        }
    }
})
def generate_report_by_id(file_id):
    """Generate single PDF report via path parameter"""
    result = process_single_file(file_id)
    if result.get("success"):
        return jsonify(result), 200
    else:
        return jsonify(result), 500


# --- Multi-file route ---
@report_bp.route('/report/generate/', methods=['POST'])
@swag_from({
    'tags': ['Report'],
    'summary': 'Generate multi-file PDF report with year-over-year analysis',
    'description': 'This endpoint generates PDF reports from multiple uploaded files for year-over-year comparison analysis. Requires at least 2 file_ids from previous uploads via /api/upload/batch.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'description': 'Multi-file report generation request',
            'schema': {
                'type': 'object',
                'properties': {
                    'file_ids': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'minItems': 2,
                        'description': 'Array of file IDs from uploaded files (minimum 2 required)',
                        'example': ['abc123', 'def908']
                    },
                    'report_title': {
                        'type': 'string',
                        'description': 'Optional custom title for the multi-year report',
                        'example': 'Multi-Year WIL Analysis Report'
                    }
                },
                'required': ['file_ids'],
                'example': {
                    'file_ids': ['abc123', 'def908'],
                    'report_title': 'Multi-Year WIL Analysis Report'
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Multi-file PDF report generated successfully',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'file_ids': {'type': 'array', 'items': {'type': 'string'}},
                            'analysis_id': {'type': 'string'},
                            'success': {'type': 'boolean'},
                            'download_url': {'type': 'string'},
                            'files_processed': {'type': 'integer'},
                            'years_analyzed': {'type': 'array', 'items': {'type': 'integer'}},
                            'total_records': {'type': 'integer'},
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '400': {
            'description': 'Bad request - invalid file_ids or missing required fields',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'success': {'type': 'boolean'},
                            'error': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': 'Internal server error during report generation',
            'content': {
                'application/json': {
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
        }
    }
})
def generation_report_by_multiple_id():
    """Generate multi-file PDF report for year-over-year analysis"""
    data = request.get_json()
    
    if not data or 'file_ids' not in data:
        return jsonify({
            "success": False,
            "error": 'Missing "file_ids" in request body'
        }), 400
    
    file_ids = data['file_ids']
    
    # Validate minimum file count
    if not isinstance(file_ids, list) or len(file_ids) < 2:
        return jsonify({
            "success": False,
            "error": 'At least 2 file_ids are required for multi-file analysis'
        }), 400
    
    report_title = data.get('report_title')
    
    # Process multiple files for year-over-year analysis
    result = process_multiple_files(file_ids, report_title)
    if result.get("success"):
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@report_bp.route('/report/sample', methods=['GET'])
@swag_from({
    'tags': ['Report'],
    'summary': 'View sample PDF report',
    'description': 'View the sample PDF report inline from frontend/public/Sample.pdf',
    'responses': {
        '200': {
            'description': 'Sample PDF file',
            'content': {
                'application/pdf': {
                    'schema': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        '404': {
            'description': 'Sample file not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'error': {
                        'type': 'string',
                        'example': 'Sample PDF not found'
                    }
                }
            }
        }
    }
})

def get_sample_pdf():
    """Return the sample PDF file"""
    logger = logging.getLogger(__name__)
    
    try:
        # Get the backend directory path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # Navigate to frontend/public/Sample.pdf
        sample_pdf_path = os.path.join(backend_dir, '..', 'frontend', 'public', 'Sample.pdf')
        sample_pdf_path = os.path.abspath(sample_pdf_path)
        
        if not os.path.exists(sample_pdf_path):
            logger.warning(f"Sample PDF not found at: {sample_pdf_path}")
            return jsonify({
                'success': False,
                'error': 'Sample PDF not found'
            }), 404
        
        logger.info(f"Serving sample PDF from: {sample_pdf_path}")
        
        return send_file(
            sample_pdf_path,
            as_attachment=False,
            download_name='WIL_Sample_Report.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error serving sample PDF: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to serve sample PDF',
            'details': str(e)
        }), 500


@report_bp.route('/report/pdf/<analysis_id>', methods=['GET'])
@swag_from({
    'tags': ['Report'],
    'summary': 'View generated PDF report',
    'description': 'View the generated PDF report inline in browser using analysis_id',
    'parameters': [
        {
            'name': 'analysis_id',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Analysis ID returned from report generation',
            'example': '550e8400-e29b-41d4-a716-446655440000'
        }
    ],
    'responses': {
        '200': {
            'description': 'PDF file displayed inline',
            'content': {
                'application/pdf': {
                    'schema': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
        '404': {
            'description': 'PDF report not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'error': {'type': 'string', 'example': 'PDF report not found'}
                }
            }
        }
    }
})
def download_pdf_report(analysis_id):
    """Download generated PDF report by analysis_id"""
    logger = logging.getLogger(__name__)
    
    try:
        # Construct path to PDF file
        # Check for both single-file and multi-file report formats
        pdf_filename_single = f"report_{analysis_id}.pdf"
        pdf_filename_multi = f"multi_year_report_{analysis_id}.pdf"
        analysis_results_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        
        # Try both single-file and multi-file report formats
        pdf_path_single = os.path.join(analysis_results_dir, pdf_filename_single)
        pdf_path_multi = os.path.join(analysis_results_dir, pdf_filename_multi)
        
        if os.path.exists(pdf_path_single):
            pdf_path = pdf_path_single
            pdf_filename = pdf_filename_single
        elif os.path.exists(pdf_path_multi):
            pdf_path = pdf_path_multi
            pdf_filename = pdf_filename_multi
        else:
            logger.warning(f"PDF report not found at: {pdf_path_single} or {pdf_path_multi}")
            return jsonify({
                'success': False,
                'error': 'PDF report not found'
            }), 404
        
        logger.info(f"Serving PDF report from: {pdf_path}")
        
        return send_file(
            pdf_path,
            as_attachment=False,
            download_name='WIL_Analysis_Report.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error serving PDF report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to serve PDF report',
            'details': str(e)
        }), 500


