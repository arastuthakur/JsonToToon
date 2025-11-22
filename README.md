# JSON to TOON Converter

A modern Flask-based web application that allows users to upload JSON files and convert them to TOON (Token-Oriented Object Notation) format instantly.

## Features

- 🚀 **Fast Conversion**: Instant JSON to TOON conversion
- 🎨 **Modern UI**: Beautiful, responsive user interface
- 📤 **Drag & Drop**: Easy file upload with drag and drop support
- 🔒 **Secure**: File validation and secure filename handling
- 📱 **Responsive**: Works seamlessly on desktop and mobile devices
- 🎯 **API Support**: RESTful API endpoint for programmatic access

## About TOON Format

TOON (Token-Oriented Object Notation) is a compact, human-readable encoding of the JSON data model, optimized for Large Language Model (LLM) prompts. It combines:

- **YAML-style indentation** for nested objects
- **CSV-style tabular layout** for uniform arrays
- **30-60% fewer tokens** compared to standard JSON

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd JSONTOTOON
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your SECRET_KEY
# Generate a secure key using:
python -c "import secrets; print(secrets.token_hex(32))"
```

## Usage

1. Run the Flask application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload a JSON file using the web interface:
   - Click the upload area or drag and drop your JSON file
   - Click "Convert to TOON"
   - The converted file will be downloaded automatically

## Testing

Run the test suite to verify functionality:

```bash
# Test JSON to TOON conversion
python tests/test_conversion.py

# Test TOON validation
python tests/test_validation.py
```

## API Usage

You can also use the API endpoint for programmatic access:

```bash
curl -X POST -F "file=@example.json" http://localhost:5000/api/convert
```

Response:
```json
{
  "success": true,
  "toon": "...",
  "filename": "example.toon"
}
```

## Project Structure

```
JSONTOTOON/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── SEO_GEO_OPTIMIZATION.md     # SEO & GEO optimization documentation
├── .env.example                # Example environment variables file
├── .gitignore                  # Git ignore rules
├── templates/
│   └── index.html              # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css          # Stylesheet
│   └── robots.txt             # Robots.txt for SEO
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_conversion.py      # Conversion tests
│   ├── test_validation.py     # Validation tests
│   └── test_data.json         # Test data
└── uploads/                    # Temporary upload directory (auto-created)
    └── .gitkeep                # Keep directory in git
```

## Example JSON to TOON Conversion

**Input JSON:**
```json
{
  "name": "John Doe",
  "age": 30,
  "city": "New York",
  "hobbies": ["reading", "coding", "traveling"]
}
```

**Output TOON:**
```
name: John Doe
age: 30
city: New York
hobbies: [reading, coding, traveling]
```

## Features in Detail

- **File Validation**: Only accepts `.json` files
- **TOON Validation**: Validates generated TOON format to ensure correctness
- **Error Handling**: Comprehensive error messages for invalid files
- **File Size Limit**: Maximum 16MB file size
- **Auto-cleanup**: Temporary files are automatically removed after processing
- **Security**: Uses Werkzeug's `secure_filename` for safe file handling
- **Environment Variables**: Secure configuration via `.env` file
- **Instant Download**: Converted TOON files are automatically downloaded

## Developer

**Arastu Thakur**

## License

This project is open source and available for use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

