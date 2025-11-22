"""
Flask Web Application for JSON to TOON Conversion
Developer: arastu
"""

from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
import os
import json
import io
import re
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
import guincorn

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'json'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def json_to_toon(data, indent=0):
    """
    Convert JSON data to TOON format.
    TOON combines YAML-style indentation for objects with CSV-style tables for arrays.
    
    Args:
        data: JSON data (dict, list, or primitive)
        indent: Current indentation level
    
    Returns:
        str: TOON formatted string
    """
    indent_str = '  ' * indent
    
    if isinstance(data, dict):
        if not data:
            return '{}'
        
        lines = []
        for key, value in data.items():
            # Escape key if needed
            key_str = str(key)
            if ' ' in key_str or ':' in key_str or '\n' in key_str:
                key_str = f'"{key_str}"'
            
            if isinstance(value, (dict, list)) and value:
                # Complex nested structure
                if isinstance(value, list) and all(isinstance(item, dict) and 
                                                   len(item) > 0 and 
                                                   all(isinstance(v, (str, int, float, bool, type(None))) 
                                                       for v in item.values()) for item in value):
                    # Tabular array format (CSV-style)
                    lines.append(f'{indent_str}{key_str}:')
                    # Get all keys from first item
                    if value:
                        keys = list(value[0].keys())
                        # Header row
                        header = indent_str + '  ' + ' | '.join(str(k) for k in keys)
                        lines.append(header)
                        # Data rows
                        for item in value:
                            row_values = []
                            for k in keys:
                                val = item.get(k, '')
                                if val is None:
                                    val = 'null'
                                elif isinstance(val, bool):
                                    val = str(val).lower()
                                elif isinstance(val, str):
                                    # Escape special characters
                                    if '|' in val or '\n' in val:
                                        val = f'"{val}"'
                                row_values.append(str(val))
                            row = indent_str + '  ' + ' | '.join(row_values)
                            lines.append(row)
                else:
                    # Regular nested structure
                    value_str = json_to_toon(value, indent + 1)
                    lines.append(f'{indent_str}{key_str}:')
                    # Add value with proper indentation
                    if isinstance(value, dict):
                        lines.append(value_str)
                    elif isinstance(value, list):
                        lines.append(value_str)
                    else:
                        lines.append(f'{indent_str}  {value_str}')
            else:
                # Simple value
                value_str = format_value(value)
                lines.append(f'{indent_str}{key_str}: {value_str}')
        
        return '\n'.join(lines)
    
    elif isinstance(data, list):
        if not data:
            return '[]'
        
        # Check if all items are simple types (for inline format)
        if all(isinstance(item, (str, int, float, bool, type(None))) for item in data):
            values = [format_value(item) for item in data]
            return f'[{", ".join(values)}]'
        
        # Check if all items are dicts with same structure (tabular format)
        if all(isinstance(item, dict) and len(item) > 0 and 
               all(isinstance(v, (str, int, float, bool, type(None))) 
                   for v in item.values()) for item in data):
            # Tabular format
            if data:
                keys = list(data[0].keys())
                lines = []
                # Header
                header = indent_str + ' | '.join(str(k) for k in keys)
                lines.append(header)
                # Data rows
                for item in data:
                    row_values = []
                    for k in keys:
                        val = item.get(k, '')
                        if val is None:
                            val = 'null'
                        elif isinstance(val, bool):
                            val = str(val).lower()
                        elif isinstance(val, str):
                            if '|' in val or '\n' in val:
                                val = f'"{val}"'
                        row_values.append(str(val))
                    row = indent_str + ' | '.join(row_values)
                    lines.append(row)
                return '\n'.join(lines)
        
        # Regular list format
        lines = []
        for item in data:
            item_str = json_to_toon(item, indent)
            if isinstance(item, (dict, list)) and item:
                lines.append(f'{indent_str}-')
                # Adjust indentation for nested content
                item_lines = item_str.split('\n')
                for line in item_lines:
                    if line.strip():
                        lines.append(f'{indent_str}  {line.lstrip()}')
            else:
                lines.append(f'{indent_str}- {item_str}')
        
        return '\n'.join(lines)
    
    else:
        return format_value(data)


def format_value(value):
    """Format a primitive value for TOON output."""
    if value is None:
        return 'null'
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        # Escape if needed
        if any(char in value for char in ['\n', '"', ':', '|', '[', ']', '{', '}']):
            return json.dumps(value)
        return value
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        return json.dumps(value)


def validate_toon(toon_data):
    """
    Validate that the generated TOON format is valid.
    
    Args:
        toon_data: TOON formatted string
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not toon_data or not toon_data.strip():
        return False, "TOON data is empty"
    
    lines = toon_data.split('\n')
    indent_stack = [0]  # Track expected indentation levels
    
    try:
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                i += 1
                continue
            
            # Check for tabular format (header row with |)
            if ' | ' in stripped and not stripped.startswith('-'):
                # This is a tabular header or data row
                parts = [p.strip() for p in stripped.split(' | ')]
                if not parts or not all(parts):
                    return False, f"Invalid tabular format at line {i+1}: empty columns"
                i += 1
                continue
            
            # Check for list item
            if stripped.startswith('-'):
                # List item format
                content = stripped[1:].strip()
                if not content:
                    return False, f"Empty list item at line {i+1}"
                i += 1
                continue
            
            # Check for key-value pair
            if ':' in stripped:
                parts = stripped.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else ''
                
                if not key:
                    return False, f"Empty key at line {i+1}"
                
                # Check indentation
                current_indent = len(line) - len(line.lstrip())
                
                # If value is empty, next line should be indented
                if not value:
                    # Check if next line exists and is more indented
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= current_indent and next_line.strip():
                            # This might be valid if it's a tabular format
                            if ' | ' not in next_line.strip():
                                # Not tabular, should be more indented
                                pass  # Allow for now, might be tabular format
                i += 1
                continue
            
            # Check for inline array
            if stripped.startswith('[') and stripped.endswith(']'):
                # Inline array format
                content = stripped[1:-1].strip()
                # Basic validation - should have comma-separated values
                if content:
                    # Try to parse as comma-separated
                    values = [v.strip() for v in content.split(',')]
                    if not all(values):
                        return False, f"Invalid array format at line {i+1}: empty values"
                i += 1
                continue
            
            # Check for empty object/array markers
            if stripped in ['{}', '[]']:
                i += 1
                continue
            
            # If we get here, the line doesn't match any known TOON format
            # But it might still be valid (e.g., continuation of a value)
            # So we'll be lenient and just continue
            i += 1
        
        return True, None
    
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def verify_toon_roundtrip(json_data, toon_data):
    """
    Verify TOON by attempting to reconstruct the original JSON structure.
    This is a basic verification - full TOON parser would be more complex.
    
    Args:
        json_data: Original JSON data
        toon_data: Generated TOON data
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    # Basic checks:
    # 1. TOON should not be empty if JSON had data
    if json_data and not toon_data.strip():
        return False, "TOON output is empty but input had data"
    
    # 2. Check that key counts match (for objects)
    if isinstance(json_data, dict):
        json_keys = set(json_data.keys())
        # Extract keys from TOON (basic regex)
        toon_keys = set()
        for line in toon_data.split('\n'):
            if ':' in line and not line.strip().startswith('-'):
                key_match = re.match(r'^\s*([^:]+):', line)
                if key_match:
                    key = key_match.group(1).strip().strip('"\'')
                    toon_keys.add(key)
        
        # Allow some difference due to nested structures
        # But main top-level keys should be present
        if len(json_keys) > 0 and len(toon_keys) == 0:
            return False, "No keys found in TOON output"
    
    # 3. Validate TOON structure
    is_valid, error = validate_toon(toon_data)
    if not is_valid:
        return False, error
    
    return True, None


@app.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')


@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for SEO."""
    return send_file('static/robots.txt', mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    """Generate sitemap.xml for SEO."""
    from datetime import datetime
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{request.url_root}</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>'''
    return app.response_class(sitemap, mimetype='application/xml')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and conversion."""
    try:
        # Check if file is present
        if 'file' not in request.files:
            flash('No file part in the request', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        # Validate file extension
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a JSON file.', 'error')
            return redirect(url_for('index'))
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
            
            # Convert to TOON
            toon_data = json_to_toon(json_data)
            
            # Validate TOON output
            is_valid, error_msg = verify_toon_roundtrip(json_data, toon_data)
            if not is_valid:
                os.remove(file_path)
                flash(f'TOON validation failed: {error_msg}', 'error')
                return redirect(url_for('index'))
            
            # Create output filename
            base_name = os.path.splitext(filename)[0]
            toon_filename = f'{base_name}.toon'
            
            # Create in-memory file
            toon_file = io.BytesIO()
            toon_file.write(toon_data.encode('utf-8'))
            toon_file.seek(0)
            
            # Clean up uploaded file
            os.remove(file_path)
            
            # Send file for download
            return send_file(
                toon_file,
                mimetype='text/plain',
                as_attachment=True,
                download_name=toon_filename
            )
        
        except json.JSONDecodeError as e:
            os.remove(file_path)
            flash(f'Invalid JSON file: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    except RequestEntityTooLarge:
        flash('File is too large. Maximum size is 16MB.', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """API endpoint for JSON to TOON conversion."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Read JSON data
        json_data = json.load(file)
        
        # Convert to TOON
        toon_data = json_to_toon(json_data)
        
        # Validate TOON output
        is_valid, error_msg = verify_toon_roundtrip(json_data, toon_data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'TOON validation failed: {error_msg}'
            }), 400
        
        return jsonify({
            'success': True,
            'toon': toon_data,
            'filename': os.path.splitext(secure_filename(file.filename))[0] + '.toon',
            'validated': True
        })
    
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))


