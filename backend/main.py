"""
Training Report Generator - Backend API Service
==============================================

Flask API service that generates Word document reports from templates.
Provides RESTful endpoints for report generation, template management, and file downloads.

API Endpoints:
- POST /api/generate - Generate report from form data and files (returns JSON with download info)
- GET /api/download/{file_id} - Download generated report by file ID
- GET /api/files - List all generated files with download links
- GET /api/templates - List available Word templates
- GET /api/health - Health check endpoint
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from datetime import datetime
from docx import Document
from docx.shared import Cm
from werkzeug.utils import secure_filename
import uuid
import logging
import json
from functools import wraps
from pathlib import Path

# Import processing modules
from modules.document_utils import find_and_replace_text
from modules.image_processing import insert_gallery_table, get_annexure_images_and_captions, insert_annexure_images
from modules.form_processing import process_form_data_api, process_gallery_images_api
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize configuration
Config.init_app(app)

# Enable CORS for frontend communication
CORS(app, origins=Config.CORS_ORIGINS)

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# API Key Authentication
def load_api_keys():
    """Load API keys from JSON file or environment variables."""
    # Try to load from JSON file first
    try:
        with open(Config.API_KEYS_FILE, 'r') as f:
            data = json.load(f)
            json_keys = data.get('valid_keys', [])
            if json_keys:
                logger.info(f"Loaded {len(json_keys)} API keys from JSON file")
                return json_keys
    except FileNotFoundError:
        logger.info("API keys JSON file not found, trying environment variables")
    except Exception as e:
        logger.warning(f"Error loading API keys from JSON: {str(e)}")
    
    # Fallback to environment variables
    env_keys = Config.API_KEYS_ENV
    if env_keys:
        logger.info(f"Loaded {len(env_keys)} API keys from environment variables")
        return env_keys
    
    # No keys found
    logger.warning("No API keys found in JSON file or environment variables")
    return []

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip API key check if disabled in config
        if not Config.REQUIRE_API_KEY:
            return f(*args, **kwargs)
            
        # Check for API key in header
        api_key = request.headers.get('x-api-key')
        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'Please provide x-api-key in request headers'
            }), 401
            
        # Load and validate API key
        valid_keys = load_api_keys()
        if api_key not in valid_keys:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
            
        # Log successful authentication
        logger.info(f"API request authenticated with key ending in: ...{api_key[-4:]}")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Root endpoint - provides API information"""
    return jsonify({
        'name': 'Training Report Generator API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'templates': '/api/templates/<training_type>',
            'generate': '/api/generate (POST)'
        },
        'frontend_url': 'Serve frontend separately on different port'
    })

# Template mapping for different training types
TEMPLATE_MAPPING = {
    'type_a': {
        '1': 'word_templates/type_a_template_1.docx',  # RRECL
        '2': 'word_templates/type_a_template_2.docx',  # GEDA
        '3': 'word_templates/type_a_template_3.docx',  # HAREDA
        '4': 'word_templates/type_a_template_4.docx',  # UREDA
        '5': 'word_templates/type_a_template_5.docx'   # SDA Odisha
    },
    'type_b': {
        '1': 'word_templates/type_b_template_1.docx',
        '2': 'word_templates/type_b_template_2.docx',
        '3': 'word_templates/type_b_template_3.docx',
        '4': 'word_templates/type_b_template_4.docx',
        '5': 'word_templates/type_b_template_5.docx'
    },
    'type_c': {
        '1': 'word_templates/type_c_template_1.docx',
        '2': 'word_templates/type_c_template_2.docx',
        '3': 'word_templates/type_c_template_3.docx',
        '4': 'word_templates/type_c_template_4.docx',
        '5': 'word_templates/type_c_template_5.docx'
    },
    'type_d': {
        '1': 'word_templates/type_d_template_1.docx',
        '2': 'word_templates/type_d_template_2.docx',
        '3': 'word_templates/type_d_template_3.docx',
        '4': 'word_templates/type_d_template_4.docx',
        '5': 'word_templates/type_d_template_5.docx'
    }
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Training Report Generator API"
    })

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get list of available templates."""
    try:
        available_templates = {}
        
        for training_type, templates in TEMPLATE_MAPPING.items():
            available_templates[training_type] = {}
            for template_id, template_path in templates.items():
                full_path = os.path.join(os.path.dirname(__file__), template_path)
                available_templates[training_type][template_id] = {
                    "id": template_id,
                    "path": template_path,
                    "exists": os.path.exists(full_path)
                }
        
        return jsonify({
            "status": "success",
            "templates": available_templates
        })
    
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch templates: {str(e)}"
        }), 500

@app.route('/api/generate', methods=['POST'])
@require_api_key
def generate_report():
    """Generate training report from form data and uploaded files."""
    try:
        logger.info("Report generation request received")
        
        # Validate required fields
        if 'training_type' not in request.form:
            return jsonify({
                "status": "error",
                "message": "Training type is required"
            }), 400
            
        if 'template_id' not in request.form:
            return jsonify({
                "status": "error", 
                "message": "Template ID is required"
            }), 400
        
        training_type = request.form.get('training_type')
        template_id = request.form.get('template_id', '1')
        
        # Validate training type and template
        if training_type not in TEMPLATE_MAPPING:
            return jsonify({
                "status": "error",
                "message": f"Invalid training type: {training_type}"
            }), 400
            
        if template_id not in TEMPLATE_MAPPING[training_type]:
            return jsonify({
                "status": "error",
                "message": f"Invalid template ID: {template_id} for training type: {training_type}"
            }), 400
        
        # Get template path
        template_path = TEMPLATE_MAPPING[training_type][template_id]
        full_template_path = os.path.join(os.path.dirname(__file__), template_path)
        
        if not os.path.exists(full_template_path):
            return jsonify({
                "status": "error",
                "message": f"Template file not found: {template_path}"
            }), 404
        
        # Load Word template
        doc = Document(full_template_path)
        logger.info(f"Loaded template: {template_path}")
        
        # Process form data for text replacements
        text_replacements = process_form_data_api(request)
        logger.info(f"Processing {len(text_replacements)} text replacements")
        
        # Apply text replacements with debugging
        replacement_count = 0
        for placeholder, value in text_replacements.items():
            if value:
                count = find_and_replace_text(doc, placeholder, value)
                replacement_count += count
                if count > 0:
                    logger.info(f"Replaced '{placeholder}' -> '{value[:50]}...' ({count} times)")
                else:
                    logger.warning(f"Placeholder '{placeholder}' not found in document")
        
        logger.info(f"Total replacements made: {replacement_count}")
        
        # Process gallery images
        gallery_images, gallery_captions = process_gallery_images_api(request)
        logger.info(f"Processing {len(gallery_images)} gallery images")
        
        # Insert gallery table if images exist
        if gallery_images:
            insert_gallery_table(doc, gallery_images, gallery_captions, 
                                images_per_row=2, image_width=Cm(8.13))
        
        # Process annexure images
        annexure_placeholders = [
            ('annexure1', '{{ANNEXURE1_TABLE}}'),
            ('annexure2', '{{ANNEXURE2_TABLE}}'),
            ('annexure3', '{{ANNEXURE3_TABLE}}'),
            ('annexure4', '{{ANNEXURE4_TABLE}}'),
            ('annexure5', '{{ANNEXURE5_TABLE}}'),
        ]
        
        for i, (prefix, placeholder) in enumerate(annexure_placeholders):
            images, captions = get_annexure_images_and_captions(prefix, request)
            if images:
                is_last_annexure = (i == len(annexure_placeholders) - 1)
                insert_annexure_images(doc, images, captions, placeholder,
                                     image_width=Cm(15), image_height=Cm(20),
                                     add_final_page_break=not is_last_annexure)
        
        # Generate filename
        event_date = request.form.get('event_date', datetime.now().strftime('%Y%m%d')).replace('-', '')
        cell_name = request.form.get('cell_name', 'Training').replace(' ', '_')
        filename = f"{training_type.upper()}_{event_date}_{cell_name}_report.docx"
        
        # Generate unique file ID for download
        file_id = str(uuid.uuid4())
        
        # Save to output directory with unique ID
        output_path = os.path.join(Config.OUTPUT_FOLDER, f"{file_id}_{filename}")
        doc.save(output_path)
        
        logger.info(f"Report generated successfully: {filename}")
        
        # Return JSON with download information
        return jsonify({
            "status": "success",
            "message": "Report generated successfully",
            "filename": filename,
            "file_id": file_id,
            "download_url": f"/api/download/{file_id}",
            "generated_at": datetime.now().isoformat(),
            "file_size_mb": round(os.path.getsize(output_path) / (1024 * 1024), 2)
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Failed to generate report: {str(e)}"
        }), 500


@app.route('/api/download/<file_id>', methods=['GET'])
@require_api_key
def download_report(file_id):
    """Download generated report by file ID."""
    try:
        logger.info(f"Download request received for file_id: {file_id}")
        
        # Validate file_id format (basic UUID check)
        if not file_id or len(file_id) < 36:
            return jsonify({
                "status": "error",
                "message": "Invalid file ID format"
            }), 400
        
        # Check if output folder exists
        if not os.path.exists(Config.OUTPUT_FOLDER):
            logger.error(f"Output folder does not exist: {Config.OUTPUT_FOLDER}")
            return jsonify({
                "status": "error",
                "message": "Output directory not found"
            }), 500
        
        # Find file with the given ID
        try:
            output_files = [f for f in os.listdir(Config.OUTPUT_FOLDER) if f.startswith(f"{file_id}_")]
            logger.info(f"Found {len(output_files)} files matching file_id: {file_id}")
        except Exception as e:
            logger.error(f"Error listing output directory: {e}")
            return jsonify({
                "status": "error",
                "message": "Error accessing output directory"
            }), 500
        
        if not output_files:
            logger.warning(f"No files found for file_id: {file_id}")
            # List all files for debugging
            all_files = os.listdir(Config.OUTPUT_FOLDER)
            logger.info(f"Available files in output directory: {all_files}")
            return jsonify({
                "status": "error",
                "message": f"File not found or expired. File ID: {file_id}"
            }), 404
        
        file_path = os.path.join(Config.OUTPUT_FOLDER, output_files[0])
        
        # Check if file actually exists and is readable
        if not os.path.exists(file_path):
            logger.error(f"File path does not exist: {file_path}")
            return jsonify({
                "status": "error",
                "message": "File path not found"
            }), 404
        
        # Extract original filename (remove ID prefix)
        original_filename = output_files[0].replace(f"{file_id}_", "")
        
        logger.info(f"Serving file for download:")
        logger.info(f"  File path: {file_path}")
        logger.info(f"  Original filename: {original_filename}")
        logger.info(f"  File size: {os.path.getsize(file_path)} bytes")
        
        # Return file for download with proper headers
        return send_file(
            file_path,
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except FileNotFoundError:
        logger.error(f"File not found during download: {file_id}")
        return jsonify({
            "status": "error",
            "message": "File not found"
        }), 404
    except PermissionError:
        logger.error(f"Permission denied accessing file: {file_id}")
        return jsonify({
            "status": "error",
            "message": "Permission denied accessing file"
        }), 403
    except Exception as e:
        logger.error(f"Unexpected error downloading file {file_id}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to download file: {str(e)}"
        }), 500


@app.route('/api/files', methods=['GET'])
@require_api_key
def list_generated_files():
    """List all generated files in output directory."""
    try:
        files = []
        for filename in os.listdir(Config.OUTPUT_FOLDER):
            if filename.endswith('.docx'):
                file_path = os.path.join(Config.OUTPUT_FOLDER, filename)
                file_stat = os.stat(file_path)
                
                # Extract file_id if present
                if '_' in filename:
                    file_id = filename.split('_')[0]
                    display_name = filename.replace(f"{file_id}_", "")
                else:
                    file_id = None
                    display_name = filename
                
                files.append({
                    "filename": display_name,
                    "file_id": file_id,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "download_url": f"/api/download/{file_id}" if file_id else None
                })
        
        return jsonify({
            "status": "success",
            "files": sorted(files, key=lambda x: x['created_at'], reverse=True),
            "total_files": len(files)
        })
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to list files: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors."""
    return jsonify({
        "status": "error",
        "message": "File too large"
    }), 413

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    
    # Get configuration from environment variables
    host = Config.API_HOST
    port = Config.API_PORT
    debug = Config.DEBUG_MODE
    
    logger.info(f"Starting Training Report Generator API on {host}:{port}")
    logger.info(f"API Base URL: {Config.API_BASE_URL}")
    logger.info(f"Debug Mode: {debug}")
    logger.info(f"Available Endpoints:")
    logger.info(f"  - Health Check: {Config.HEALTH_ENDPOINT}")
    logger.info(f"  - Templates: {Config.TEMPLATES_ENDPOINT}")
    logger.info(f"  - Generate: {Config.GENERATE_ENDPOINT}")
    logger.info(f"  - Download: {Config.DOWNLOAD_ENDPOINT}/<file_id>")
    logger.info(f"  - Files List: {Config.FILES_LIST_ENDPOINT}")
    
    app.run(debug=debug, host=host, port=port)
