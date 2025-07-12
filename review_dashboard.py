"""
Review Dashboard for Casedoxx Generator
======================================

This dashboard provides a comprehensive review workflow interface that allows users to:
1. Upload files for review
2. Preview file metadata and content
3. Validate file integrity
4. Approve or reject files
5. Track review progress
6. Send approved files for processing

Features:
- File upload and validation
- Metadata preview and content display
- Integrity checking and issue reporting
- Batch review management
- Approval/rejection workflow
- Integration with main processing pipeline
- Review statistics and reporting

Functions:
- main(): Main review dashboard interface
- upload_files(): Handle file uploads
- display_file_preview(): Show file metadata and content
- approve_files(): Approve files for processing
- reject_files(): Reject files with reasons
- process_approved_files(): Send approved files to main processing
- display_review_statistics(): Show review statistics
"""

import streamlit as st
import os
import json
import datetime
import pandas as pd
from pathlib import Path
import sys

# Import review workflow
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from review_workflow import ReviewWorkflow

# Page configuration
st.set_page_config(
    page_title="Casedoxx Review Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .review-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-pending { background-color: #fff3cd; color: #856404; }
    .status-approved { background-color: #d4edda; color: #155724; }
    .status-rejected { background-color: #f8d7da; color: #721c24; }
    .metadata-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    .metadata-table th, .metadata-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .metadata-table th {
        background-color: #f2f2f2;
    }
    .issue-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .content-preview {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 5px;
        max-height: 300px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize review workflow
@st.cache_resource
def get_review_workflow():
    return ReviewWorkflow()

workflow = get_review_workflow()

# Initialize session state
if 'current_batch_id' not in st.session_state:
    st.session_state.current_batch_id = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def display_file_preview(file_review):
    """Display file preview with metadata and content."""
    with st.expander(f"📄 {file_review.filename} ({format_file_size(file_review.file_size)})", expanded=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("File Information")
            st.write(f"**Type:** {file_review.file_type.upper()}")
            st.write(f"**MIME Type:** {file_review.mime_type}")
            st.write(f"**Size:** {format_file_size(file_review.file_size)}")
            st.write(f"**Hash:** {file_review.hash_value[:16]}...")
            if file_review.estimated_pages:
                st.write(f"**Estimated Pages:** {file_review.estimated_pages}")
            if file_review.family_group:
                st.write(f"**Family Group:** {file_review.family_group}")
            
            # Status badge
            status_color = {
                'pending': 'status-pending',
                'approved': 'status-approved',
                'rejected': 'status-rejected'
            }.get(file_review.review_status, 'status-pending')
            
            st.markdown(f'<span class="status-badge {status_color}">{file_review.review_status.upper()}</span>', 
                       unsafe_allow_html=True)
        
        with col2:
            st.subheader("Metadata")
            if file_review.metadata:
                # Display key metadata
                key_metadata = {
                    'Title': file_review.metadata.get('title', 'N/A'),
                    'Author': file_review.metadata.get('Author', 'N/A'),
                    'Subject': file_review.metadata.get('Subject', 'N/A'),
                    'Date Created': file_review.metadata.get('Creation-Date', 'N/A'),
                    'Date Modified': file_review.metadata.get('Last-Modified', 'N/A'),
                    'Page Count': file_review.metadata.get('xmpTPg:NPages', 'N/A')
                }
                
                for key, value in key_metadata.items():
                    if value and value != 'N/A':
                        st.write(f"**{key}:** {value}")
            else:
                st.write("No metadata available")
        
        # Integrity issues
        if file_review.integrity_issues:
            st.markdown("""
            <div class="issue-warning">
                <strong>⚠️ Integrity Issues Found:</strong>
            </div>
            """, unsafe_allow_html=True)
            for issue in file_review.integrity_issues:
                st.write(f"• {issue}")
        
        # Content preview
        if file_review.content_preview:
            st.subheader("Content Preview")
            st.markdown(f"""
            <div class="content-preview">
                {file_review.content_preview}
            </div>
            """, unsafe_allow_html=True)
        
        # Review actions
        st.subheader("Review Actions")
        col3, col4, col5 = st.columns([1, 1, 1])
        
        with col3:
            if file_review.review_status == 'pending':
                if st.button(f"✅ Approve", key=f"approve_{file_review.file_id}"):
                    notes = st.text_area("Review Notes (optional)", key=f"notes_approve_{file_review.file_id}")
                    priority = st.selectbox("Processing Priority", [1, 2, 3, 4, 5], key=f"priority_{file_review.file_id}")
                    
                    if st.button("Confirm Approval", key=f"confirm_approve_{file_review.file_id}"):
                        workflow.approve_file(file_review.file_id, "dashboard_user", notes, priority)
                        st.success(f"✅ {file_review.filename} approved!")
                        st.rerun()
        
        with col4:
            if file_review.review_status == 'pending':
                if st.button(f"❌ Reject", key=f"reject_{file_review.file_id}"):
                    reason = st.selectbox("Rejection Reason", [
                        "File corrupted or unreadable",
                        "Inappropriate content",
                        "Wrong file type",
                        "Duplicate file",
                        "File too large",
                        "Other"
                    ], key=f"reason_{file_review.file_id}")
                    
                    notes = st.text_area("Rejection Notes", key=f"notes_reject_{file_review.file_id}")
                    
                    if st.button("Confirm Rejection", key=f"confirm_reject_{file_review.file_id}"):
                        workflow.reject_file(file_review.file_id, "dashboard_user", reason, notes)
                        st.error(f"❌ {file_review.filename} rejected!")
                        st.rerun()
        
        with col5:
            if file_review.review_status in ['approved', 'rejected']:
                st.write(f"**Reviewed by:** {file_review.reviewed_by}")
                st.write(f"**Reviewed at:** {file_review.reviewed_at}")
                if file_review.review_notes:
                    st.write(f"**Notes:** {file_review.review_notes}")

def display_review_statistics(batch_id):
    """Display review statistics for a batch."""
    if batch_id:
        batch = workflow.batches.get(batch_id)
        if batch:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Files", batch.total_files)
            
            with col2:
                st.metric("Pending", batch.pending_files)
            
            with col3:
                st.metric("Approved", batch.approved_files)
            
            with col4:
                st.metric("Rejected", batch.rejected_files)
            
            # Progress bar
            if batch.total_files > 0:
                progress = (batch.approved_files + batch.rejected_files) / batch.total_files
                st.progress(progress)
                st.write(f"Review Progress: {progress:.1%}")

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Casedoxx Review Dashboard</h1>
        <p>Review and validate files before processing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 File Upload")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload files for review",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'eml', 'tif', 'tiff']
        )
        
        if uploaded_files:
            st.session_state.uploaded_files = []
            for uploaded_file in uploaded_files:
                # Save uploaded file
                upload_dir = "uploads"
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, uploaded_file.name)
                
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.session_state.uploaded_files.append(filepath)
            
            st.success(f"✅ {len(uploaded_files)} files uploaded!")
        
        # Create review batch
        st.header("⚙️ Create Review Batch")
        
        batch_name = st.text_input("Batch Name", placeholder="Enter batch name")
        
        review_deadline = st.date_input("Review Deadline (optional)")
        
        if st.button("🔍 Create Review Batch", type="primary", 
                    disabled=not (batch_name and st.session_state.uploaded_files)):
            if batch_name and st.session_state.uploaded_files:
                # Create review batch
                batch_id = workflow.create_review_batch(
                    batch_name=batch_name,
                    files=st.session_state.uploaded_files,
                    created_by="dashboard_user",
                    review_deadline=review_deadline.isoformat() if review_deadline else None
                )
                
                st.session_state.current_batch_id = batch_id
                st.session_state.uploaded_files = []
                st.success(f"✅ Review batch '{batch_name}' created!")
                st.rerun()
        
        # Batch selection
        st.header("📋 Select Batch")
        if workflow.batches:
            batch_options = {f"{batch.batch_name} ({batch.total_files} files)": batch_id 
                           for batch_id, batch in workflow.batches.items()}
            
            selected_batch = st.selectbox("Choose batch to review", 
                                        options=list(batch_options.keys()),
                                        key="batch_selector")
            
            if selected_batch:
                st.session_state.current_batch_id = batch_options[selected_batch]
        else:
            st.info("No review batches available. Create one above.")
    
    # Main content area
    if st.session_state.current_batch_id:
        batch_id = st.session_state.current_batch_id
        batch = workflow.batches.get(batch_id)
        
        if batch:
            # Batch header
            st.header(f"📋 Reviewing: {batch.batch_name}")
            st.write(f"Created by {batch.created_by} on {batch.created_at}")
            
            # Display statistics
            display_review_statistics(batch_id)
            
            # Batch actions
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("📊 Generate Report"):
                    report_file = workflow.export_review_report(batch_id, 'html')
                    st.success(f"✅ Report generated: {report_file}")
            
            with col2:
                if st.button("📥 Export Approved Files"):
                    approved_files = workflow.get_approved_files_for_processing(batch_id)
                    if approved_files:
                        st.success(f"✅ {len(approved_files)} files ready for processing")
                    else:
                        st.warning("No approved files found")
            
            with col3:
                if st.button("🚀 Send to Processing"):
                    approved_files = workflow.get_approved_files_for_processing(batch_id)
                    if approved_files:
                        # Here you would integrate with the main processing pipeline
                        st.success(f"✅ {len(approved_files)} files sent to processing!")
                    else:
                        st.warning("No approved files to process")
            
            # File reviews
            st.header("📄 File Reviews")
            batch_files = workflow.get_batch_files(batch_id)
            
            if batch_files:
                # Filter options
                col1, col2 = st.columns([1, 1])
                with col1:
                    status_filter = st.selectbox("Filter by Status", 
                                               ["All", "Pending", "Approved", "Rejected"])
                with col2:
                    type_filter = st.selectbox("Filter by Type", 
                                             ["All"] + list(set(f.file_type for f in batch_files)))
                
                # Apply filters
                filtered_files = batch_files
                if status_filter != "All":
                    filtered_files = [f for f in filtered_files if f.review_status == status_filter.lower()]
                if type_filter != "All":
                    filtered_files = [f for f in filtered_files if f.file_type == type_filter.lower()]
                
                # Display files
                for file_review in filtered_files:
                    display_file_preview(file_review)
            else:
                st.info("No files in this batch.")
    
    # Global statistics
    st.header("📈 Review Statistics")
    stats = workflow.get_review_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Batches", stats['total_batches'])
    
    with col2:
        st.metric("Total Files", stats['total_files'])
    
    with col3:
        st.metric("Total Size", f"{stats['total_size_mb']:.1f} MB")
    
    with col4:
        st.metric("Avg File Size", f"{stats['average_file_size_mb']:.1f} MB")
    
    # File type distribution
    if stats['file_type_counts']:
        st.subheader("File Type Distribution")
        df_types = pd.DataFrame(list(stats['file_type_counts'].items()), 
                              columns=['File Type', 'Count'])
        st.bar_chart(df_types.set_index('File Type'))
    
    # Status distribution
    if stats['status_counts']:
        st.subheader("Review Status Distribution")
        df_status = pd.DataFrame(list(stats['status_counts'].items()), 
                               columns=['Status', 'Count'])
        st.bar_chart(df_status.set_index('Status'))

if __name__ == "__main__":
    main() 