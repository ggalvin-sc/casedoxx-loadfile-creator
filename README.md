# Casedoxx LoadFile Creator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive Python application for creating Casedoxx-compatible loadfiles with advanced file processing, review workflows, and data integrity validation.

## 🚀 Features

### 📁 **File Processing**
- **Multi-format Support**: PDF, DOCX, XLSX, TXT, JPG, PNG, EML, TIFF
- **Metadata Extraction**: Automatic extraction using Apache Tika
- **Bates Numbering**: Sequential Bates numbering with customizable prefixes
- **Content Extraction**: Text extraction from documents and emails
- **Image Processing**: PDF to image conversion with Bates stamping

### 🔍 **Review Workflow**
- **File Validation**: Integrity checks and format validation
- **Metadata Preview**: View file properties and content previews
- **Batch Management**: Organize files into review batches
- **Approval Workflow**: Approve/reject files with detailed notes
- **Progress Tracking**: Real-time review progress and statistics

### 📊 **Dashboard Interface**
- **Streamlit Dashboard**: Modern web interface for file processing
- **Review Dashboard**: Comprehensive review workflow interface
- **Real-time Progress**: Live progress tracking and status updates
- **Statistics & Reports**: Detailed analytics and reporting

### 🛡️ **Data Integrity**
- **File Validation**: Corruption detection and format verification
- **Hash Verification**: MD5 hash calculation for file integrity
- **Quality Assurance**: Comprehensive testing and validation
- **Audit Trail**: Complete logging and documentation

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Java**: Runtime Environment (for Apache Tika)
- **Poppler**: PDF processing utilities
- **Windows**: 10/11 (primary platform)

### Python Dependencies
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
tika>=2.6.0
PyPDF2>=3.0.0
pdf2image>=1.16.0
Pillow>=10.0.0
python-magic>=0.4.27
```

## 🛠️ Installation

### 1. Clone the Repository
```powershell
git clone https://github.com/yourusername/casedoxx-loadfile-creator.git
cd casedoxx-loadfile-creator
```

### 2. Install Python Dependencies
```powershell
# Install core dependencies
pip install -r requirements_streamlit.txt

# Install review workflow dependencies
pip install -r requirements_review.txt
```

### 3. Install System Dependencies

#### Java Runtime Environment
```powershell
# Download from: https://adoptium.net/
# Install Java 8 or higher
java -version  # Verify installation
```

#### Poppler for PDF Processing
```powershell
# Download from: https://github.com/oschwartz10612/poppler-windows/releases
# Extract to C:\Program Files\poppler-24.08.0\
# Add to PATH: C:\Program Files\poppler-24.08.0\Library\bin
```

### 4. Download Apache Tika
```powershell
# Download tika-server-standard-3.0.0-BETA2.jar
# Place in project root directory
```

## 🚀 Quick Start

### Start the Main Dashboard
```powershell
streamlit run streamlit_dashboard.py
```

### Start the Review Dashboard
```powershell
streamlit run review_dashboard.py
```

### Run Tests
```powershell
python test_review_workflow.py
python run_tests.py
```

## 📖 Usage

### Main Processing Workflow

1. **Upload Files**: Use the Streamlit dashboard to upload files
2. **Create Job**: Configure processing settings and create a job
3. **Monitor Progress**: Track processing progress in real-time
4. **Download Results**: Download complete Casedoxx loadfiles

### Review Workflow

1. **Upload for Review**: Upload files through the review dashboard
2. **Create Review Batch**: Organize files into review batches
3. **Review Files**: Preview metadata, content, and integrity
4. **Approve/Reject**: Make decisions with detailed notes
5. **Send to Processing**: Approved files go to main processing

### Command Line Usage

```powershell
# Process files directly
python LoadFile_Creator_4.1_Testing.py --input input_dir --output output_dir --volume VOLUME_NAME

# Run tests
python run_tests.py

# Test review workflow
python test_review_workflow.py
```

## 📁 Project Structure

```
casedoxx-loadfile-creator/
├── 📄 LoadFile_Creator_4.1_Testing.py    # Main processing application
├── 📄 streamlit_dashboard.py              # Main Streamlit dashboard
├── 📄 review_dashboard.py                 # Review workflow dashboard
├── 📄 review_workflow.py                  # Review workflow system
├── 📄 config_manager.py                   # Configuration management
├── 📄 bates_config.json                   # Bates numbering configuration
├── 📄 requirements_streamlit.txt          # Main dependencies
├── 📄 requirements_review.txt             # Review workflow dependencies
├── 📄 tests/                             # Test suite
│   ├── 📄 run_tests.py                   # Test runner
│   ├── 📄 inputs/                        # Test input files
│   └── 📄 expected/                      # Expected test outputs
├── 📄 Supporting_Files/                  # Supporting resources
│   ├── 📄 FONTS/                         # Font files
│   ├── 📄 POPPLER/                       # Poppler utilities
│   └── 📄 TIKA/                          # Tika resources
└── 📄 docs/                              # Documentation
    ├── 📄 README_Streamlit.md            # Streamlit documentation
    ├── 📄 README_Review_Workflow.md      # Review workflow docs
    └── 📄 REVIEW_WORKFLOW_SUMMARY.md     # Best practices
```

## ⚙️ Configuration

### Bates Numbering Configuration
```json
{
    "bates_stamping": {
        "font_size": 30,
        "margin": 20,
        "text_color_light": [255, 255, 255],
        "text_color_dark": [0, 0, 0],
        "contrast_threshold": 128,
        "add_border": false,
        "border_color": [255, 255, 255],
        "border_width": 2
    },
    "processing_settings": {
        "timeout": 500,
        "max_file_timeout": 300,
        "max_total_timeout": 3600,
        "max_workers": 4,
        "pdf_dpi": 150,
        "pdf_chunk_size": 5
    }
}
```

### Review Workflow Settings
```json
{
    "max_file_size": "100MB",
    "supported_formats": ["pdf", "docx", "xlsx", "txt", "jpg", "png", "eml"],
    "content_preview_length": 500,
    "integrity_checks": true,
    "auto_family_grouping": true
}
```

## 🧪 Testing

### Run All Tests
```powershell
python run_tests.py
```

### Test Review Workflow
```powershell
python test_review_workflow.py
```

### Test Streamlit Integration
```powershell
python test_streamlit_integration.py
```

### Validate Bates and Pages
```powershell
python validate_bates_and_pages.py
```

## 📊 Features in Detail

### File Processing Capabilities
- **PDF Processing**: Multi-page PDF support with image conversion
- **Office Documents**: DOCX, XLSX with metadata extraction
- **Email Processing**: EML files with thread grouping
- **Image Files**: JPG, PNG, TIFF with Bates stamping
- **Text Files**: TXT, CSV with content extraction

### Review Workflow Features
- **File Validation**: Integrity checks and format verification
- **Metadata Preview**: Document properties and content previews
- **Batch Management**: Organized review batches with deadlines
- **Approval System**: Approve/reject with detailed documentation
- **Progress Tracking**: Real-time statistics and completion rates

### Dashboard Features
- **Modern UI**: Clean, responsive Streamlit interface
- **Real-time Updates**: Live progress tracking and status updates
- **File Management**: Upload, organize, and process files
- **Job Management**: Create, monitor, and manage processing jobs
- **Download Results**: Easy download of processed loadfiles

## 🔧 Troubleshooting

### Common Issues

#### File Upload Problems
```powershell
# Check file permissions
icacls uploads /grant Everyone:F

# Verify file integrity
python -c "import magic; print(magic.from_file('file.pdf'))"
```

#### Tika Server Issues
```powershell
# Start Tika server manually
java -jar tika-server-standard-3.0.0-BETA2.jar

# Check Java installation
java -version
```

#### Streamlit Dashboard Issues
```powershell
# Clear Streamlit cache
streamlit cache clear

# Restart dashboard
streamlit run streamlit_dashboard.py
```

### Error Messages

| Error | Solution |
|-------|----------|
| "Tika server not found" | Start Tika server or check Java installation |
| "Poppler not found" | Install Poppler and add to PATH |
| "File upload failed" | Check file permissions and size limits |
| "Processing timeout" | Increase timeout settings in configuration |

## 🤝 Contributing

### Development Setup
```powershell
# Clone repository
git clone https://github.com/yourusername/casedoxx-loadfile-creator.git
cd casedoxx-loadfile-creator

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements_streamlit.txt
pip install -r requirements_review.txt

# Run tests
python run_tests.py
```

### Code Style
- Follow PEP 8 Python style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write comprehensive tests for new features

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Apache Tika**: For document parsing and metadata extraction
- **Streamlit**: For the web application framework
- **Poppler**: For PDF processing utilities
- **Pillow**: For image processing capabilities

## 📞 Support

For questions, issues, or feature requests:

- **Issues**: [GitHub Issues](https://github.com/yourusername/casedoxx-loadfile-creator/issues)
- **Documentation**: See the `docs/` directory for detailed guides
- **Email**: Contact the development team

## 🔄 Version History

### v4.1.0 (Current)
- ✅ Complete review workflow system
- ✅ Streamlit dashboard integration
- ✅ Advanced file processing capabilities
- ✅ Comprehensive testing suite
- ✅ Documentation and guides

### v4.0.0
- ✅ Initial Casedoxx loadfile generation
- ✅ Basic file processing
- ✅ Bates numbering system

### v3.x.x
- ✅ Legacy Concordance support
- ✅ Basic file processing

---

**Casedoxx LoadFile Creator** - Professional-grade file processing and loadfile generation for legal document management. 