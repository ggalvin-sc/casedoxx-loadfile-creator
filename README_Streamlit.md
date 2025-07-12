# Streamlit Casedoxx Generator Dashboard

A modern, user-friendly web interface for creating and managing casedoxx data generation tasks. This dashboard integrates with your existing LoadFile Creator program to process various file types and generate Casedoxx-compatible loadfiles.

## Features

- **📁 File Upload**: Drag and drop multiple files for processing
- **⚙️ Job Management**: Create, monitor, and manage processing jobs
- **📊 Real-time Progress**: Live progress tracking with status updates
- **📋 Job History**: View completed jobs and download results
- **🎨 Modern UI**: Clean, responsive interface with custom styling
- **🔧 Error Handling**: Comprehensive error reporting and logging
- **💾 Persistent Storage**: Jobs are saved and persist between sessions

## Quick Start

### 1. Install Dependencies

```powershell
pip install -r requirements_streamlit.txt
```

### 2. Run the Dashboard

```powershell
streamlit run streamlit_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

## Usage

### Creating a New Job

1. **Upload Files**: Use the sidebar to upload PDF, DOCX, XLSX, TXT, JPG, PNG, or EML files
2. **Configure Job**: 
   - Enter a job name
   - Select output format (Standard Casedoxx, Custom Format, Legacy Format)
   - Choose processing options (metadata, word frequency, cross-references, etc.)
3. **Start Processing**: Click "Start Processing" to begin

### Monitoring Jobs

- **Active Jobs**: View currently running jobs with real-time progress
- **Statistics**: See job counts and status overview
- **Job Details**: Click "View Details" for detailed information and logs
- **Job Actions**: Stop, delete, or download completed jobs

### Downloading Results

- Completed jobs show a "Download" button
- Results are packaged as ZIP files containing all processed outputs
- Files are organized by the LoadFile Creator's standard structure

## File Structure

```
Loadfile_Creator/
├── streamlit_dashboard.py          # Main dashboard application
├── requirements_streamlit.txt      # Python dependencies
├── streamlit_jobs.json           # Job database (auto-created)
├── uploads/                      # Uploaded files directory
├── outputs/                      # Processing outputs directory
└── downloads/                    # Download files directory
```

## Configuration

### Customizing the Dashboard

The dashboard can be customized by modifying:

- **Styling**: Edit the CSS in the `st.markdown()` section
- **File Types**: Modify the `allowed_extensions` list in `validate_file()`
- **Processing Options**: Update the options in the sidebar
- **Job Storage**: Change the JSON file location in `load_jobs()`

### Integration with LoadFile Creator

The dashboard automatically imports and uses your existing `LoadFile_Creator_4.1_Testing.py` file. Make sure this file is in the same directory as the dashboard.

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure `LoadFile_Creator_4.1_Testing.py` is in the same directory
2. **File Upload Issues**: Check file permissions and available disk space
3. **Processing Errors**: Review job logs in the "Job Details" section
4. **Port Conflicts**: Streamlit will automatically find an available port

### Performance Tips

- Use smaller files for testing
- Monitor disk space for uploads and outputs
- Close unused browser tabs to reduce memory usage
- Restart the dashboard if it becomes unresponsive

## Advantages Over Dash

- **Simpler Code**: No complex callback management
- **Better UX**: Built-in file upload, progress bars, and error handling
- **Faster Development**: Less boilerplate code
- **Better Error Messages**: More informative error reporting
- **Auto-reload**: Changes to code automatically refresh the page
- **Mobile Friendly**: Responsive design works on all devices

## Next Steps

Consider these enhancements:

1. **User Authentication**: Add login system for multiple users
2. **Advanced Analytics**: Add charts and statistics for job performance
3. **Email Notifications**: Send completion alerts
4. **Batch Processing**: Process multiple job types simultaneously
5. **API Integration**: Connect to external services for enhanced processing

## Support

For issues or questions:
1. Check the job logs in the dashboard
2. Review the console output for error messages
3. Ensure all dependencies are installed correctly
4. Verify file permissions and disk space 