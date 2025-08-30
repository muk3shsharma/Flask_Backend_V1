# Training Report Generator Backend API

Flask-based REST API service for generating Word document training reports from templates.

## 🚀 Features

- **RESTful API** endpoints for report generation
- **Multiple training types** support (Type A, B, C, D)
- **Template management** with 5 templates per type
- **Image processing** for gallery and annexure images  
- **File upload handling** with secure temporary storage
- **CORS enabled** for frontend integration
- **Production ready** with proper error handling and logging

## 📋 API Endpoints

### Health Check
```
GET /api/health
```
Returns service health status

### Templates List
```
GET /api/templates  
```
Returns available Word document templates for all training types

### Generate Report
```
POST /api/generate
```
Generates training report from form data and uploaded files

**Required fields:**
- `training_type`: One of `type_a`, `type_b`, `type_c`, `type_d`
- `template_id`: Template number (1-5)
- Form data: Training details (dates, venue, people, etc.)
- Files: Gallery images and annexure documents

**Response:** Returns generated .docx file for download

## 🛠️ Installation & Setup

### Local Development

1. **Clone and navigate to backend:**
```bash
cd backend/
```

2. **Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create .env file:**
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=127.0.0.1
PORT=5000
```

5. **Run the application:**
```bash
python app_clean.py
```

The API will be available at `http://localhost:5000`

### Production Deployment (Render)

This backend is configured for deployment on Render using `render.yaml`:

1. **Push to GitHub repository**
2. **Connect to Render** and select your repository  
3. **Environment variables** will be loaded from `render.yaml`
4. **Automatic deployment** on every push to main branch

## 📁 Project Structure

```
backend/
├── app_clean.py          # Main Flask application
├── config.py             # Configuration settings  
├── requirements.txt      # Python dependencies
├── render.yaml          # Render deployment config
├── modules/             # Processing modules
│   ├── document_utils.py    # Word document manipulation
│   ├── form_processing.py   # Form data processing  
│   ├── image_processing.py  # Image handling
│   └── chart_processing.py  # Chart generation (placeholder)
├── word_templates/      # Word document templates
│   ├── type_a_template_1.docx
│   ├── type_a_template_2.docx  
│   └── ... (20 templates total)
└── output/             # Generated reports (temporary)
```

## ⚙️ Configuration

Key environment variables:

- `SECRET_KEY`: Flask secret key for sessions
- `DEBUG`: Enable/disable debug mode  
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 5000)
- `MAX_CONTENT_LENGTH`: File upload limit (default: 50MB)
- `CORS_ORIGINS`: Allowed frontend origins

## 🔧 Template System

The API supports 4 training types, each with 5 Word document templates:

- **Type A**: 1-Day ECSBC Training  
- **Type B**: 2-Day Technical Workshop
- **Type C**: Government Officials Training
- **Type D**: Professional Development Training

Templates use placeholder text (e.g., `{{CELL_NAME}}`, `{{EVENT_DATE}}`) that get replaced with form data.

## 📤 Image Processing

- **Gallery Images**: Up to 10 images arranged in 2×3 grids per page
- **Annexure Images**: Up to 5 annexure sections with multiple images each
- **File Handling**: Secure temporary storage with automatic cleanup
- **Formats Supported**: JPG, JPEG, PNG, GIF, BMP, TIFF

## 🚦 API Usage Examples

### Check Health
```bash
curl http://localhost:5000/api/health
```

### Get Templates
```bash
curl http://localhost:5000/api/templates
```

### Generate Report
```bash
curl -X POST http://localhost:5000/api/generate \
  -F "training_type=type_a" \
  -F "template_id=1" \
  -F "event_date=2025-08-28" \
  -F "cell_name=D2O Training Cell" \
  -F "venue=Conference Hall" \
  -F "gallery_image_1=@image1.jpg" \
  --output report.docx
```

## 📊 Error Handling

The API returns structured JSON error responses:

```json
{
  "status": "error",
  "message": "Detailed error description"
}
```

Common HTTP status codes:
- `200`: Success (with file download)
- `400`: Bad request (missing/invalid parameters)
- `404`: Template not found  
- `413`: File too large
- `500`: Internal server error

## 🧪 Testing

Test the API endpoints using tools like:
- **Postman** for interactive testing
- **curl** for command-line testing  
- **Frontend application** for end-to-end testing

## 📝 Logs

Production logs are written to `logs/api.log` with rotation when the file exceeds 10MB.

## 🔒 Security Features

- **CORS protection** with configurable origins
- **File upload validation** with size limits
- **Secure filename handling** to prevent directory traversal
- **Input sanitization** for form data
- **Production security headers** (X-Content-Type-Options, X-Frame-Options, etc.)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)  
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and support:
1. Check the logs in `logs/api.log`
2. Verify environment variables are set correctly
3. Ensure Word templates are present in `word_templates/`
4. Test API endpoints individually
5. Check CORS configuration for frontend integration
