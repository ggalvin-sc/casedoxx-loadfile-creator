# Casedoxx Review Workflow System

## Overview

The **Review Workflow System** provides a comprehensive solution for reviewing and validating files before they are processed into Casedoxx loadfiles. This system ensures data quality, integrity, and compliance before processing begins.

## Key Features

### 🔍 **File Review & Validation**
- **Metadata Preview**: View file metadata, content, and properties
- **Integrity Checking**: Automatic detection of corrupted or problematic files
- **Content Preview**: Preview text content from documents and emails
- **File Type Validation**: Ensure files are in supported formats

### 📋 **Batch Management**
- **Review Batches**: Organize files into review batches
- **Progress Tracking**: Monitor review progress and statistics
- **Deadline Management**: Set review deadlines for batches
- **Status Tracking**: Track approved, rejected, and pending files

### ✅ **Approval Workflow**
- **Approve/Reject**: Simple approval or rejection with reasons
- **Review Notes**: Add detailed notes for each file
- **Priority Setting**: Set processing priority for approved files
- **Batch Actions**: Approve or reject entire batches

### 📊 **Reporting & Analytics**
- **Review Reports**: Generate detailed HTML, CSV, or JSON reports
- **Statistics Dashboard**: View review statistics and metrics
- **File Type Analysis**: Analyze file type distribution
- **Progress Tracking**: Monitor review completion rates

## How It Works

### 1. **Upload Files for Review**
```
📁 Upload Files → 🔍 Create Review Batch → 📋 Review Files → ✅ Approve/Reject → 🚀 Send to Processing
```

### 2. **Review Process**
1. **Upload**: Upload files through the Streamlit dashboard
2. **Create Batch**: Organize files into review batches
3. **Preview**: View metadata, content, and integrity information
4. **Review**: Approve or reject files with notes
5. **Export**: Generate reports and send approved files to processing

### 3. **Integration with Processing**
- Approved files are automatically prepared for Casedoxx processing
- Maintains file integrity and metadata throughout the workflow
- Seamless integration with the main LoadFile Creator system

## Installation

### Prerequisites
- Python 3.8+
- Java Runtime Environment (for Tika)
- Poppler (for PDF processing)

### Install Dependencies
```powershell
# Install Python dependencies
pip install -r requirements_review.txt

# Install system dependencies (Windows)
# Download and install Java from: https://adoptium.net/
# Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases
```

## Usage

### Starting the Review Dashboard

```powershell
# Start the review dashboard
streamlit run review_dashboard.py
```

### Workflow Steps

#### 1. **Upload Files**
- Open the review dashboard in your browser
- Use the sidebar to upload files for review
- Supported formats: PDF, DOCX, XLSX, TXT, JPG, PNG, EML, TIFF

#### 2. **Create Review Batch**
- Enter a batch name
- Set optional review deadline
- Click "Create Review Batch"

#### 3. **Review Files**
- Select the batch to review
- View file metadata and content previews
- Check for integrity issues
- Approve or reject files with notes

#### 4. **Generate Reports**
- Create detailed review reports in HTML, CSV, or JSON format
- View batch statistics and progress
- Export approved files for processing

#### 5. **Send to Processing**
- Approved files are ready for Casedoxx processing
- Maintains all metadata and file integrity
- Seamless integration with main processing pipeline

## File Review Features

### **Metadata Preview**
- File type and MIME type detection
- File size and hash calculation
- Estimated page count
- Document properties (title, author, subject)
- Creation and modification dates

### **Content Preview**
- Text extraction from documents
- Email content and headers
- Image file information
- Binary file identification

### **Integrity Checking**
- File corruption detection
- Format validation
- Size and type consistency
- Duplicate file detection

### **Review Actions**
- **Approve**: Mark files for processing with priority
- **Reject**: Reject files with specific reasons
- **Notes**: Add detailed review notes
- **Priority**: Set processing priority (1-5)

## Batch Management

### **Batch Operations**
- Create new review batches
- Set review deadlines
- Track batch progress
- Generate batch reports
- Export approved files

### **Batch Statistics**
- Total files in batch
- Approved/rejected/pending counts
- File type distribution
- Size and page count totals
- Review completion percentage

## Reporting

### **Report Types**
- **HTML Reports**: Detailed web-based reports with styling
- **CSV Reports**: Spreadsheet-compatible data export
- **JSON Reports**: Programmatic data access

### **Report Content**
- Batch information and statistics
- File metadata and review status
- Integrity issues and warnings
- Review notes and decisions
- Processing recommendations

## Integration with Main System

### **Approved Files Processing**
```python
# Get approved files from review batch
approved_files = workflow.get_approved_files_for_processing(batch_id)

# Send to main processing pipeline
creator = LoadFileCreator()
creator.process_files(
    input_dir=approved_files_dir,
    output_dir=output_dir,
    volume_name=volume_name
)
```

### **Data Flow**
1. **Review**: Files are reviewed and approved
2. **Validation**: Integrity and format checks
3. **Preparation**: Files prepared for processing
4. **Processing**: Casedoxx loadfile generation
5. **Output**: Complete loadfile with all data

## Configuration

### **Review Settings**
```json
{
    "max_file_size": "100MB",
    "supported_formats": ["pdf", "docx", "xlsx", "txt", "jpg", "png", "eml"],
    "content_preview_length": 500,
    "integrity_checks": true,
    "auto_family_grouping": true
}
```

### **Processing Integration**
```json
{
    "bates_prefix": "REVIEW",
    "start_number": 1000,
    "include_metadata": true,
    "data_integrity_tests": true
}
```

## Best Practices

### **Review Workflow**
1. **Upload in Batches**: Organize related files together
2. **Set Deadlines**: Establish review timelines
3. **Check Integrity**: Review all integrity warnings
4. **Add Notes**: Document decisions and reasons
5. **Set Priorities**: Assign processing priorities
6. **Generate Reports**: Create detailed review documentation

### **Quality Assurance**
- Review all file metadata before approval
- Check for corrupted or problematic files
- Verify file types and formats
- Document rejection reasons
- Maintain review audit trail

### **Performance Optimization**
- Process files in manageable batches
- Use appropriate file size limits
- Monitor system resources
- Regular cleanup of temporary files

## Troubleshooting

### **Common Issues**

#### **File Upload Problems**
```powershell
# Check file permissions
icacls uploads /grant Everyone:F

# Verify file integrity
python -c "import magic; print(magic.from_file('file.pdf'))"
```

#### **Metadata Extraction Issues**
```powershell
# Restart Tika server
java -jar tika-server-standard-3.0.0-BETA2.jar

# Check Java installation
java -version
```

#### **Review Dashboard Issues**
```powershell
# Clear Streamlit cache
streamlit cache clear

# Restart dashboard
streamlit run review_dashboard.py
```

### **Error Messages**

| Error | Solution |
|-------|----------|
| "File corrupted" | Check file integrity, try re-uploading |
| "Unsupported format" | Verify file type, convert if needed |
| "Metadata extraction failed" | Restart Tika server, check Java |
| "Review batch not found" | Refresh dashboard, check batch ID |

## Advanced Features

### **Custom Review Workflows**
```python
# Custom review workflow
workflow = ReviewWorkflow()

# Create custom review criteria
def custom_review_criteria(file_review):
    if file_review.file_size > 50 * 1024 * 1024:  # 50MB
        return "File too large"
    if file_review.integrity_issues:
        return "Integrity issues found"
    return "Approve"

# Apply custom criteria
for file_review in batch_files:
    decision = custom_review_criteria(file_review)
    if decision == "Approve":
        workflow.approve_file(file_review.file_id, "custom_reviewer")
    else:
        workflow.reject_file(file_review.file_id, "custom_reviewer", decision)
```

### **Automated Review Rules**
```python
# Automated approval rules
def auto_approve_rules(file_review):
    # Auto-approve small text files
    if (file_review.file_type in ['txt', 'csv'] and 
        file_review.file_size < 1024 * 1024):  # 1MB
        return True
    
    # Auto-reject corrupted files
    if file_review.integrity_issues:
        return False
    
    return None  # Manual review required
```

## Security Considerations

### **File Security**
- Files are stored in secure directories
- Access controls on review data
- Audit trail for all review actions
- Secure file deletion after processing

### **Data Privacy**
- Review notes are encrypted
- User authentication for review actions
- Secure transmission of file data
- Compliance with data protection regulations

## Support and Maintenance

### **Regular Maintenance**
- Clean up temporary files
- Archive completed review batches
- Update review criteria and rules
- Monitor system performance

### **Backup and Recovery**
- Regular backup of review data
- Export review reports for archiving
- Recovery procedures for data loss
- Version control for review configurations

## Conclusion

The **Casedoxx Review Workflow System** provides a robust, user-friendly solution for reviewing files before processing. It ensures data quality, maintains audit trails, and integrates seamlessly with the main Casedoxx processing pipeline.

By implementing this review workflow, you can:
- ✅ Ensure data quality before processing
- ✅ Maintain compliance and audit trails
- ✅ Improve processing efficiency
- ✅ Reduce errors and rework
- ✅ Generate detailed review documentation

For questions or support, refer to the troubleshooting section or contact the development team. 