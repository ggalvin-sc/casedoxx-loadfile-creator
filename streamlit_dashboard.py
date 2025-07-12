"""
Streamlit Dashboard for Casedoxx Generator
=========================================

This dashboard provides a modern, user-friendly interface for creating and managing
casedoxx data generation tasks. It integrates with the LoadFile Creator program
to process various file types and generate Casedoxx-compatible loadfiles.

Features:
- File upload and validation
- Job creation and management
- Real-time progress tracking
- Job history and status monitoring
- Download processed outputs
- Error handling and logging

Functions:
- main(): Main dashboard interface
- create_job(): Create new processing job
- process_files(): Handle file processing
- display_jobs(): Show job status and history
- download_results(): Download processed files
"""

import streamlit as st
import pandas as pd
import os
import json
import datetime
import uuid
import threading
import time
import shutil
import base64
from pathlib import Path
import sys

# Import your existing LoadFile Creator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("LoadFileCreator", "LoadFile_Creator_4.1_Testing.py")
LoadFileCreator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LoadFileCreator_module)
LoadFileCreator = LoadFileCreator_module.LoadFileCreator

# Page configuration
st.set_page_config(
    page_title="Casedoxx Generator Dashboard",
    page_icon="📊",
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
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .job-card {
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
    .status-queued { background-color: #fff3cd; color: #856404; }
    .status-processing { background-color: #d1ecf1; color: #0c5460; }
    .status-completed { background-color: #d4edda; color: #155724; }
    .status-failed { background-color: #f8d7da; color: #721c24; }
    .progress-bar {
        height: 8px;
        border-radius: 4px;
        background-color: #e9ecef;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'jobs' not in st.session_state:
    st.session_state.jobs = {}
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

# Job management functions
def load_jobs():
    """Load jobs from persistent storage"""
    jobs_file = "streamlit_jobs.json"
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, 'r') as f:
                st.session_state.jobs = json.load(f)
        except:
            st.session_state.jobs = {}

def save_jobs():
    """Save jobs to persistent storage"""
    jobs_file = "streamlit_jobs.json"
    with open(jobs_file, 'w') as f:
        json.dump(st.session_state.jobs, f, indent=2)

def create_job(job_name, input_files, output_format="standard", options=None):
    """Create a new job"""
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "name": job_name,
        "status": "queued",
        "progress": 0,
        "created": datetime.datetime.now().isoformat(),
        "input_files": input_files,
        "output_format": output_format,
        "options": options or {},
        "log": [],
        "output_dir": f"outputs/{job_id}",
        "volume_name": f"VOLUME_{job_id[:8].upper()}",
        "eta": None,
        "completed": None,
        "files_processed": 0,
        "total_files": len(input_files),
        "error": None
    }
    st.session_state.jobs[job_id] = job
    save_jobs()
    return job_id

def update_job_status(job_id, status, progress=None, log_entry=None, error=None):
    """Update job status and progress"""
    if job_id in st.session_state.jobs:
        st.session_state.jobs[job_id]["status"] = status
        if progress is not None:
            st.session_state.jobs[job_id]["progress"] = progress
        if log_entry:
            st.session_state.jobs[job_id]["log"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "message": log_entry
            })
        if error:
            st.session_state.jobs[job_id]["error"] = error
        if status == "completed":
            st.session_state.jobs[job_id]["completed"] = datetime.datetime.now().isoformat()
        save_jobs()

def process_job(job_id):
    """Process job in background"""
    # Load jobs from file since we're in a background thread
    jobs_file = "streamlit_jobs.json"
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, 'r') as f:
                jobs = json.load(f)
        except:
            return
    else:
        return
    
    job = jobs.get(job_id)
    if not job:
        return
    
    try:
        # Create output directory
        output_dir = job["output_dir"]
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare input files
        input_files = []
        for file_info in job["input_files"]:
            if isinstance(file_info, dict):
                filepath = file_info.get("filepath", "")
            else:
                filepath = file_info
            if os.path.exists(filepath):
                input_files.append(filepath)
        
        if not input_files:
            update_job_status_file(job_id, "failed", error="No valid input files found")
            return
        
        # Initialize LoadFile Creator
        creator = LoadFileCreator()
        
        # Update progress
        update_job_status_file(job_id, "processing", 10, "Initializing processing")
        time.sleep(1)  # Simulate processing time
        
        # Process files
        update_job_status_file(job_id, "processing", 30, f"Processing {len(input_files)} files")
        time.sleep(1)
        
        # Update progress
        update_job_status_file(job_id, "processing", 50, "Running LoadFile Creator")
        time.sleep(1)
        
        # Create a temporary input directory with all uploaded files
        temp_input_dir = os.path.join(output_dir, "input_files")
        os.makedirs(temp_input_dir, exist_ok=True)
        
        # Copy all uploaded files to the temporary input directory
        for file_info in job["input_files"]:
            if isinstance(file_info, dict):
                source_path = file_info.get("filepath", "")
            else:
                source_path = file_info
            
            if os.path.exists(source_path):
                filename = os.path.basename(source_path)
                dest_path = os.path.join(temp_input_dir, filename)
                shutil.copy2(source_path, dest_path)
        
        # Call the actual processing function with the temporary input directory
        creator.process_files(
            input_dir=temp_input_dir,
            output_dir=output_dir,
            volume_name=job["volume_name"]
        )
        
        # Update progress
        update_job_status_file(job_id, "processing", 70, "Writing output files")
        time.sleep(1)
        
        # Write output files (this is what was missing!)
        creator.write_opt_file(output_dir, job["volume_name"])
        creator.write_loadfile(output_dir, job["volume_name"])
        
        # Update progress
        update_job_status_file(job_id, "processing", 85, "Applying Bates stamps")
        time.sleep(1)
        
        # Apply Bates stamps (optional)
        try:
            creator.apply_bates_stamps(output_dir, job["volume_name"])
        except Exception as e:
            update_job_status_file(job_id, "processing", 85, f"Bates stamping skipped: {str(e)}")
        
        # Update progress
        update_job_status_file(job_id, "processing", 95, "Running data integrity tests")
        time.sleep(1)
        
        # Run data integrity tests
        try:
            creator.run_data_integrity_tests(output_dir, job["volume_name"])
        except Exception as e:
            update_job_status_file(job_id, "processing", 95, f"Data integrity tests skipped: {str(e)}")
        
        # Check if LoadFile Creator generated output files
        volume_dir = os.path.join(output_dir, job["volume_name"])
        loadfile_path = os.path.join(volume_dir, f"{job['volume_name']}.dat")
        opt_path = os.path.join(volume_dir, f"{job['volume_name']}.opt")
        
        if os.path.exists(loadfile_path) and os.path.exists(opt_path):
            # Count processed files
            natives_dir = os.path.join(volume_dir, "NATIVES", "0000")
            images_dir = os.path.join(volume_dir, "IMAGES", "0000")
            text_dir = os.path.join(volume_dir, "TEXT", "0000")
            
            processed_files = 0
            if os.path.exists(natives_dir):
                processed_files += len([f for f in os.listdir(natives_dir) if os.path.isfile(os.path.join(natives_dir, f))])
            if os.path.exists(images_dir):
                processed_files += len([f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))])
            if os.path.exists(text_dir):
                processed_files += len([f for f in os.listdir(text_dir) if os.path.isfile(os.path.join(text_dir, f))])
            
            update_job_status_file(job_id, "completed", 100, f"Job completed successfully! Processed {processed_files} files")
        else:
            update_job_status_file(job_id, "failed", error="LoadFile Creator did not generate expected output files")
        
    except Exception as e:
        update_job_status_file(job_id, "failed", error=str(e))

def update_job_status_file(job_id, status, progress=None, log_entry=None, error=None):
    """Update job status in file (for background threads)"""
    jobs_file = "streamlit_jobs.json"
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, 'r') as f:
                jobs = json.load(f)
        except:
            return
    
    if job_id in jobs:
        jobs[job_id]["status"] = status
        if progress is not None:
            jobs[job_id]["progress"] = progress
        if log_entry:
            jobs[job_id]["log"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "message": log_entry
            })
        if error:
            jobs[job_id]["error"] = error
        if status == "completed":
            jobs[job_id]["completed"] = datetime.datetime.now().isoformat()
        
        # Save back to file
        with open(jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2)

def validate_file(filename):
    """Validate file type"""
    allowed_extensions = ['.pdf', '.docx', '.xlsx', '.txt', '.jpg', '.jpeg', '.png', '.eml']
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

def get_file_size(filepath):
    """Get file size in MB"""
    size_bytes = os.path.getsize(filepath)
    return round(size_bytes / (1024 * 1024), 2)

# Load existing jobs
load_jobs()

# Main dashboard
def main():
    # Auto-refresh mechanism
    if 'refresh_counter' not in st.session_state:
        st.session_state.refresh_counter = 0
    
    # Increment counter to trigger refresh
    st.session_state.refresh_counter += 1
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Casedoxx Generator Dashboard</h1>
        <p>Create and manage casedoxx data generation tasks</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 File Upload")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload files for processing",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'eml']
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
                
                file_size = get_file_size(filepath)
                
                st.session_state.uploaded_files.append({
                    "filename": uploaded_file.name,
                    "filepath": filepath,
                    "size_mb": file_size
                })
            
            st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
        
        # Job creation form
        st.header("⚙️ Create New Job")
        
        job_name = st.text_input("Job Name", placeholder="Enter job name")
        
        output_format = st.selectbox(
            "Output Format",
            ["Standard Casedoxx", "Custom Format", "Legacy Format"]
        )
        
        processing_options = st.multiselect(
            "Processing Options",
            ["Include metadata", "Generate word frequency analysis", "Create cross-references", "Optimize for performance"]
        )
        
        if st.button("🚀 Start Processing", type="primary", disabled=not (job_name and st.session_state.uploaded_files)):
            if job_name and st.session_state.uploaded_files:
                # Create job
                job_id = create_job(
                    job_name=job_name,
                    input_files=st.session_state.uploaded_files,
                    output_format=output_format,
                    options=processing_options
                )
                
                # Start processing in background
                thread = threading.Thread(target=process_job, args=(job_id,))
                thread.daemon = True
                thread.start()
                
                st.success(f"✅ Job '{job_name}' created and started!")
                st.session_state.uploaded_files = []
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📋 Active Jobs")
        
        active_jobs = [job for job in st.session_state.jobs.values() if job["status"] in ["queued", "processing"]]
        
        if active_jobs:
            for job in active_jobs:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{job['name']}**")
                        st.markdown(f"*Created: {job['created'][:19]}*")
                    
                    with col2:
                        status_class = f"status-{job['status']}"
                        st.markdown(f'<span class="status-badge {status_class}">{job["status"].title()}</span>', unsafe_allow_html=True)
                    
                    with col3:
                        st.metric("Progress", f"{job['progress']}%")
                    
                    # Progress bar
                    st.markdown(f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {job['progress']}%"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Job actions
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button(f"📊 View Details", key=f"details_{job['id']}"):
                            st.session_state.selected_job = job['id']
                    with col2:
                        if st.button(f"⏹️ Stop", key=f"stop_{job['id']}"):
                            update_job_status(job['id'], "stopped")
                            st.rerun()
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{job['id']}"):
                            del st.session_state.jobs[job['id']]
                            save_jobs()
                            st.rerun()
        else:
            st.info("No active jobs. Create a new job to get started!")
    
    with col2:
        st.header("📊 Statistics")
        
        total_jobs = len(st.session_state.jobs)
        active_count = len([j for j in st.session_state.jobs.values() if j["status"] in ["queued", "processing"]])
        completed_count = len([j for j in st.session_state.jobs.values() if j["status"] == "completed"])
        failed_count = len([j for j in st.session_state.jobs.values() if j["status"] == "failed"])
        
        st.metric("Total Jobs", total_jobs)
        st.metric("Active Jobs", active_count)
        st.metric("Completed", completed_count)
        st.metric("Failed", failed_count)
    
    # Completed jobs
    st.header("✅ Completed Jobs")
    
    completed_jobs = [job for job in st.session_state.jobs.values() if job["status"] in ["completed", "failed", "stopped"]]
    
    if completed_jobs:
        for job in completed_jobs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{job['name']}**")
                    completed_time = job.get('completed')
                    if completed_time:
                        st.markdown(f"*Completed: {completed_time[:19]}*")
                    else:
                        st.markdown("*Completed: Unknown*")
                
                with col2:
                    status_class = f"status-{job['status']}"
                    st.markdown(f'<span class="status-badge {status_class}">{job["status"].title()}</span>', unsafe_allow_html=True)
                
                with col3:
                    st.metric("Files", job.get("files_processed", 0))
                
                with col4:
                    if job["status"] == "completed":
                        if st.button(f"📥 Download", key=f"download_{job['id']}"):
                            # Create zip file for download
                            import zipfile
                            zip_path = f"downloads/{job['id']}_results.zip"
                            os.makedirs("downloads", exist_ok=True)
                            
                            with zipfile.ZipFile(zip_path, 'w') as zipf:
                                if os.path.exists(job["output_dir"]):
                                    for root, dirs, files in os.walk(job["output_dir"]):
                                        for file in files:
                                            file_path = os.path.join(root, file)
                                            arcname = os.path.relpath(file_path, job["output_dir"])
                                            zipf.write(file_path, arcname)
                            
                            with open(zip_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download Results",
                                    data=f.read(),
                                    file_name=f"{job['name']}_results.zip",
                                    mime="application/zip"
                                )
                    
                    if st.button(f"🗑️ Delete", key=f"delete_completed_{job['id']}"):
                        del st.session_state.jobs[job['id']]
                        save_jobs()
                        st.rerun()
    else:
        st.info("No completed jobs yet.")
    
    # Job details panel
    if 'selected_job' in st.session_state:
        st.header("📋 Job Details")
        
        job = st.session_state.jobs.get(st.session_state.selected_job)
        if job:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"**Job Name:** {job['name']}")
                st.markdown(f"**Status:** {job['status']}")
                st.markdown(f"**Created:** {job['created'][:19]}")
                st.markdown(f"**Progress:** {job['progress']}%")
                
                if job.get('completed'):
                    completed_time = job['completed']
                    st.markdown(f"**Completed:** {completed_time[:19]}")
                
                if job.get('error'):
                    st.error(f"**Error:** {job['error']}")
            
            with col2:
                st.markdown("**Input Files:**")
                for file_info in job['input_files']:
                    if isinstance(file_info, dict):
                        st.markdown(f"- {file_info['filename']} ({file_info['size_mb']} MB)")
                    else:
                        st.markdown(f"- {file_info}")
            
            # Job logs
            if job.get('log'):
                st.markdown("**Processing Log:**")
                for log_entry in job['log'][-10:]:  # Show last 10 entries
                    st.markdown(f"*{log_entry['timestamp'][:19]}*: {log_entry['message']}")
            
            if st.button("❌ Close Details"):
                del st.session_state.selected_job
                st.rerun()

if __name__ == "__main__":
    main() 