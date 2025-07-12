"""
Review Workflow for Casedoxx Generator
=====================================

This module provides a comprehensive review workflow system that allows users to:
1. Create files for review before processing
2. Preview file metadata and content
3. Validate file integrity and format
4. Approve or reject files for processing
5. Track review status and history
6. Generate review reports

Features:
- File preview and metadata display
- Content validation and integrity checks
- Review approval workflow
- Batch review operations
- Review history tracking
- Export review reports
- Integration with main processing pipeline

Functions:
- create_review_batch(): Create a new review batch
- preview_file_metadata(): Display file metadata for review
- validate_file_integrity(): Check file integrity and format
- approve_files_for_processing(): Approve files for processing
- reject_files(): Reject files with reasons
- generate_review_report(): Create detailed review report
- get_review_statistics(): Get review statistics and metrics
"""

import os
import json
import datetime
import uuid
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from dataclasses import dataclass, asdict
import mimetypes
import logging

# Try to import magic, but make it optional for Windows compatibility
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available. Using fallback file type detection.")

# Import LoadFile Creator for metadata extraction
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("LoadFileCreator", "LoadFile_Creator_4.1_Testing.py")
LoadFileCreator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LoadFileCreator_module)
LoadFileCreator = LoadFileCreator_module.LoadFileCreator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileReview:
    """Data class for file review information."""
    file_id: str
    filename: str
    filepath: str
    file_size: int
    file_type: str
    mime_type: str
    hash_value: str
    metadata: Dict[str, Any]
    review_status: str  # 'pending', 'approved', 'rejected'
    review_notes: str
    reviewed_by: str
    reviewed_at: Optional[str]
    review_reason: str
    processing_priority: int
    estimated_pages: Optional[int]
    content_preview: str
    integrity_issues: List[str]
    family_group: Optional[str]

@dataclass
class ReviewBatch:
    """Data class for review batch information."""
    batch_id: str
    batch_name: str
    created_at: str
    created_by: str
    total_files: int
    pending_files: int
    approved_files: int
    rejected_files: int
    batch_status: str  # 'active', 'completed', 'cancelled'
    batch_notes: str
    processing_settings: Dict[str, Any]
    review_deadline: Optional[str]

class ReviewWorkflow:
    """
    Comprehensive review workflow system for Casedoxx file processing.
    
    This class manages the entire review process from file upload to approval
    for processing, including metadata validation, content preview, and
    integrity checks.
    """
    
    def __init__(self, review_data_dir: str = "review_data"):
        """
        Initialize the review workflow system.
        
        Args:
            review_data_dir: Directory to store review data and files
        """
        self.review_data_dir = Path(review_data_dir)
        self.review_data_dir.mkdir(exist_ok=True)
        
        # Initialize subdirectories
        (self.review_data_dir / "batches").mkdir(exist_ok=True)
        (self.review_data_dir / "files").mkdir(exist_ok=True)
        (self.review_data_dir / "reports").mkdir(exist_ok=True)
        (self.review_data_dir / "approved").mkdir(exist_ok=True)
        (self.review_data_dir / "rejected").mkdir(exist_ok=True)
        
        # Initialize LoadFile Creator for metadata extraction
        self.loadfile_creator = LoadFileCreator()
        
        # Load existing review data
        self.batches = self._load_batches()
        self.file_reviews = self._load_file_reviews()
        
        # Supported file types for review
        self.supported_types = {
            'pdf', 'docx', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'eml',
            'tif', 'tiff', 'bmp', 'gif', 'doc', 'xls', 'ppt', 'pptx'
        }
        
        logger.info("Review workflow system initialized")
    
    def _load_batches(self) -> Dict[str, ReviewBatch]:
        """Load existing review batches from storage."""
        batches_file = self.review_data_dir / "batches" / "batches.json"
        if batches_file.exists():
            try:
                with open(batches_file, 'r') as f:
                    data = json.load(f)
                    return {batch_id: ReviewBatch(**batch_data) 
                           for batch_id, batch_data in data.items()}
            except Exception as e:
                logger.error(f"Error loading batches: {e}")
        return {}
    
    def _save_batches(self):
        """Save review batches to storage."""
        batches_file = self.review_data_dir / "batches" / "batches.json"
        with open(batches_file, 'w') as f:
            json.dump({batch_id: asdict(batch) 
                      for batch_id, batch in self.batches.items()}, f, indent=2)
    
    def _load_file_reviews(self) -> Dict[str, FileReview]:
        """Load existing file reviews from storage."""
        reviews_file = self.review_data_dir / "files" / "reviews.json"
        if reviews_file.exists():
            try:
                with open(reviews_file, 'r') as f:
                    data = json.load(f)
                    return {file_id: FileReview(**review_data) 
                           for file_id, review_data in data.items()}
            except Exception as e:
                logger.error(f"Error loading file reviews: {e}")
        return {}
    
    def _save_file_reviews(self):
        """Save file reviews to storage."""
        reviews_file = self.review_data_dir / "files" / "reviews.json"
        with open(reviews_file, 'w') as f:
            json.dump({file_id: asdict(review) 
                      for file_id, review in self.file_reviews.items()}, f, indent=2)
    
    def create_review_batch(self, batch_name: str, files: List[str], 
                           created_by: str, processing_settings: Dict[str, Any] = None,
                           review_deadline: Optional[str] = None) -> str:
        """
        Create a new review batch with uploaded files.
        
        Args:
            batch_name: Name for the review batch
            files: List of file paths to review
            created_by: User creating the batch
            processing_settings: Settings for processing after approval
            review_deadline: Optional deadline for review completion
            
        Returns:
            Batch ID for the created batch
        """
        batch_id = str(uuid.uuid4())
        
        # Create batch directory
        batch_dir = self.review_data_dir / "batches" / batch_id
        batch_dir.mkdir(exist_ok=True)
        
        # Copy files to batch directory
        copied_files = []
        for file_path in files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                dest_path = batch_dir / filename
                shutil.copy2(file_path, dest_path)
                copied_files.append(str(dest_path))
        
        # Create file reviews for each file
        for file_path in copied_files:
            self._create_file_review(file_path, batch_id)
        
        # Create batch record
        batch = ReviewBatch(
            batch_id=batch_id,
            batch_name=batch_name,
            created_at=datetime.datetime.now().isoformat(),
            created_by=created_by,
            total_files=len(copied_files),
            pending_files=len(copied_files),
            approved_files=0,
            rejected_files=0,
            batch_status='active',
            batch_notes='',
            processing_settings=processing_settings or {},
            review_deadline=review_deadline
        )
        
        self.batches[batch_id] = batch
        self._save_batches()
        
        logger.info(f"Created review batch '{batch_name}' with {len(copied_files)} files")
        return batch_id
    
    def _create_file_review(self, file_path: str, batch_id: str) -> str:
        """
        Create a file review record for a single file.
        
        Args:
            file_path: Path to the file
            batch_id: ID of the batch this file belongs to
            
        Returns:
            File review ID
        """
        file_id = str(uuid.uuid4())
        
        # Get file information
        file_stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        
        # Determine file type
        mime_type, _ = mimetypes.guess_type(file_path)
        file_extension = Path(file_path).suffix.lower().lstrip('.')
        
        # Calculate file hash
        hash_value = self._calculate_file_hash(file_path)
        
        # Extract metadata using LoadFile Creator
        metadata = self._extract_file_metadata(file_path)
        
        # Get content preview
        content_preview = self._get_content_preview(file_path)
        
        # Check for integrity issues
        integrity_issues = self._check_file_integrity(file_path)
        
        # Determine family group (for emails, etc.)
        family_group = self._identify_family_group(file_path, metadata)
        
        # Estimate page count
        estimated_pages = self._estimate_page_count(file_path, file_extension)
        
        # Create file review
        file_review = FileReview(
            file_id=file_id,
            filename=filename,
            filepath=file_path,
            file_size=file_stat.st_size,
            file_type=file_extension,
            mime_type=mime_type or 'application/octet-stream',
            hash_value=hash_value,
            metadata=metadata,
            review_status='pending',
            review_notes='',
            reviewed_by='',
            reviewed_at=None,
            review_reason='',
            processing_priority=1,
            estimated_pages=estimated_pages,
            content_preview=content_preview,
            integrity_issues=integrity_issues,
            family_group=family_group
        )
        
        self.file_reviews[file_id] = file_review
        self._save_file_reviews()
        
        return file_id
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from file using LoadFile Creator."""
        try:
            # Use LoadFile Creator's parsing capabilities
            file_extension = Path(file_path).suffix.lower().lstrip('.')
            
            if file_extension == 'pdf':
                parsed = self.loadfile_creator.chunk_pdf_and_parse(file_path)
            else:
                from tika import parser
                parsed = parser.from_file(file_path, requestOptions={'timeout': 300})
            
            if parsed and 'metadata' in parsed:
                return parsed['metadata']
            else:
                return {}
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def _get_content_preview(self, file_path: str, max_length: int = 500) -> str:
        """Get a preview of file content."""
        try:
            file_extension = Path(file_path).suffix.lower().lstrip('.')
            
            if file_extension in ['txt', 'csv', 'log']:
                # Text files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_length)
                    return content + ('...' if len(content) == max_length else '')
            
            elif file_extension in ['pdf', 'docx', 'xlsx', 'eml']:
                # Use LoadFile Creator to extract text
                if file_extension == 'pdf':
                    parsed = self.loadfile_creator.chunk_pdf_and_parse(file_path)
                else:
                    from tika import parser
                    parsed = parser.from_file(file_path, requestOptions={'timeout': 300})
                
                if parsed and 'content' in parsed and parsed['content']:
                    content = parsed['content'].strip()
                    return content[:max_length] + ('...' if len(content) > max_length else '')
            
            elif file_extension in ['jpg', 'jpeg', 'png', 'tif', 'tiff']:
                return f"[Image file: {os.path.basename(file_path)}]"
            
            else:
                return f"[Binary file: {os.path.basename(file_path)}]"
                
        except Exception as e:
            logger.warning(f"Error getting content preview from {file_path}: {e}")
            return f"[Error reading content: {str(e)}]"
    
    def _check_file_integrity(self, file_path: str) -> List[str]:
        """Check file integrity and identify potential issues."""
        issues = []
        
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                issues.append("Empty file")
            elif file_size > 100 * 1024 * 1024:  # 100MB
                issues.append("Very large file (>100MB)")
            
            # Check file type consistency
            file_extension = Path(file_path).suffix.lower().lstrip('.')
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type:
                expected_extensions = {
                    'application/pdf': ['pdf'],
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
                    'text/plain': ['txt'],
                    'image/jpeg': ['jpg', 'jpeg'],
                    'image/png': ['png'],
                    'image/tiff': ['tif', 'tiff'],
                    'message/rfc822': ['eml']
                }
                
                if mime_type in expected_extensions:
                    if file_extension not in expected_extensions[mime_type]:
                        issues.append(f"MIME type ({mime_type}) doesn't match extension (.{file_extension})")
            
            # Check for corrupted files
            if file_extension in ['pdf', 'docx', 'xlsx']:
                try:
                    if file_extension == 'pdf':
                        from PyPDF2 import PdfReader
                        with open(file_path, 'rb') as f:
                            PdfReader(f)
                    elif file_extension == 'docx':
                        import zipfile
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            zf.testzip()
                    elif file_extension == 'xlsx':
                        import zipfile
                        with zipfile.ZipFile(file_path, 'r') as zf:
                            zf.testzip()
                except Exception as e:
                    issues.append(f"File appears corrupted: {str(e)}")
            
        except Exception as e:
            issues.append(f"Error checking integrity: {str(e)}")
        
        return issues
    
    def _identify_family_group(self, file_path: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Identify if file belongs to a family group (e.g., email thread)."""
        try:
            file_extension = Path(file_path).suffix.lower().lstrip('.')
            
            if file_extension == 'eml':
                # Check for email thread indicators
                message_id = metadata.get('Message-ID', '')
                thread_index = metadata.get('Thread-Index', '')
                subject = metadata.get('Subject', '')
                
                if message_id or thread_index:
                    return f"email_thread_{hashlib.md5((message_id + thread_index + subject).encode()).hexdigest()[:8]}"
            
            return None
        except Exception as e:
            logger.warning(f"Error identifying family group for {file_path}: {e}")
            return None
    
    def _estimate_page_count(self, file_path: str, file_extension: str) -> Optional[int]:
        """Estimate the number of pages in a document."""
        try:
            if file_extension == 'pdf':
                from PyPDF2 import PdfReader
                with open(file_path, 'rb') as f:
                    pdf = PdfReader(f)
                    return len(pdf.pages)
            
            elif file_extension in ['docx', 'xlsx']:
                # Rough estimation based on file size
                file_size = os.path.getsize(file_path)
                if file_extension == 'docx':
                    return max(1, file_size // 5000)  # Rough estimate
                elif file_extension == 'xlsx':
                    return max(1, file_size // 10000)  # Rough estimate
            
            elif file_extension in ['tif', 'tiff']:
                from PIL import Image
                with Image.open(file_path) as img:
                    if hasattr(img, 'n_frames'):
                        return img.n_frames
                    else:
                        return 1
            
            return None
        except Exception as e:
            logger.warning(f"Error estimating page count for {file_path}: {e}")
            return None
    
    def get_batch_files(self, batch_id: str) -> List[FileReview]:
        """Get all files in a review batch."""
        return [review for review in self.file_reviews.values() 
                if review.filepath.startswith(str(self.review_data_dir / "batches" / batch_id))]
    
    def preview_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get detailed metadata preview for a file."""
        if file_id not in self.file_reviews:
            raise ValueError(f"File review {file_id} not found")
        
        review = self.file_reviews[file_id]
        
        return {
            'file_info': {
                'filename': review.filename,
                'file_size': review.file_size,
                'file_type': review.file_type,
                'mime_type': review.mime_type,
                'hash_value': review.hash_value,
                'estimated_pages': review.estimated_pages,
                'family_group': review.family_group
            },
            'metadata': review.metadata,
            'content_preview': review.content_preview,
            'integrity_issues': review.integrity_issues,
            'review_status': review.review_status,
            'review_notes': review.review_notes
        }
    
    def approve_file(self, file_id: str, approved_by: str, notes: str = "", 
                    priority: int = 1) -> bool:
        """Approve a file for processing."""
        if file_id not in self.file_reviews:
            return False
        
        review = self.file_reviews[file_id]
        review.review_status = 'approved'
        review.reviewed_by = approved_by
        review.reviewed_at = datetime.datetime.now().isoformat()
        review.review_notes = notes
        review.processing_priority = priority
        
        # Update batch statistics
        batch_id = self._get_batch_id_from_file_path(review.filepath)
        if batch_id and batch_id in self.batches:
            batch = self.batches[batch_id]
            batch.pending_files -= 1
            batch.approved_files += 1
            
            # Check if batch is complete
            if batch.pending_files == 0:
                batch.batch_status = 'completed'
        
        self._save_file_reviews()
        self._save_batches()
        
        logger.info(f"File {review.filename} approved by {approved_by}")
        return True
    
    def reject_file(self, file_id: str, rejected_by: str, reason: str, 
                   notes: str = "") -> bool:
        """Reject a file from processing."""
        if file_id not in self.file_reviews:
            return False
        
        review = self.file_reviews[file_id]
        review.review_status = 'rejected'
        review.reviewed_by = rejected_by
        review.reviewed_at = datetime.datetime.now().isoformat()
        review.review_reason = reason
        review.review_notes = notes
        
        # Update batch statistics
        batch_id = self._get_batch_id_from_file_path(review.filepath)
        if batch_id and batch_id in self.batches:
            batch = self.batches[batch_id]
            batch.pending_files -= 1
            batch.rejected_files += 1
        
        self._save_file_reviews()
        self._save_batches()
        
        logger.info(f"File {review.filename} rejected by {rejected_by}: {reason}")
        return True
    
    def _get_batch_id_from_file_path(self, file_path: str) -> Optional[str]:
        """Extract batch ID from file path."""
        try:
            path_parts = Path(file_path).parts
            for i, part in enumerate(path_parts):
                if part == "batches" and i + 1 < len(path_parts):
                    return path_parts[i + 1]
        except Exception:
            pass
        return None
    
    def get_approved_files_for_processing(self, batch_id: str) -> List[str]:
        """Get list of approved file paths for processing."""
        approved_files = []
        for review in self.file_reviews.values():
            if (review.review_status == 'approved' and 
                review.filepath.startswith(str(self.review_data_dir / "batches" / batch_id))):
                approved_files.append(review.filepath)
        return approved_files
    
    def generate_review_report(self, batch_id: str) -> Dict[str, Any]:
        """Generate a comprehensive review report for a batch."""
        if batch_id not in self.batches:
            raise ValueError(f"Batch {batch_id} not found")
        
        batch = self.batches[batch_id]
        batch_files = self.get_batch_files(batch_id)
        
        # Calculate statistics
        total_size = sum(f.file_size for f in batch_files)
        total_pages = sum(f.estimated_pages or 0 for f in batch_files)
        
        file_types = {}
        for f in batch_files:
            file_types[f.file_type] = file_types.get(f.file_type, 0) + 1
        
        integrity_issues = []
        for f in batch_files:
            integrity_issues.extend(f.integrity_issues)
        
        family_groups = {}
        for f in batch_files:
            if f.family_group:
                family_groups[f.family_group] = family_groups.get(f.family_group, 0) + 1
        
        report = {
            'batch_info': {
                'batch_id': batch_id,
                'batch_name': batch.batch_name,
                'created_at': batch.created_at,
                'created_by': batch.created_by,
                'total_files': batch.total_files,
                'pending_files': batch.pending_files,
                'approved_files': batch.approved_files,
                'rejected_files': batch.rejected_files,
                'batch_status': batch.batch_status
            },
            'statistics': {
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'total_pages': total_pages,
                'file_types': file_types,
                'family_groups': family_groups,
                'integrity_issues_count': len(integrity_issues),
                'unique_integrity_issues': list(set(integrity_issues))
            },
            'files': [
                {
                    'filename': f.filename,
                    'file_size': f.file_size,
                    'file_type': f.file_type,
                    'review_status': f.review_status,
                    'estimated_pages': f.estimated_pages,
                    'integrity_issues': f.integrity_issues,
                    'family_group': f.family_group,
                    'review_notes': f.review_notes
                }
                for f in batch_files
            ]
        }
        
        return report
    
    def export_review_report(self, batch_id: str, format: str = 'json') -> str:
        """Export review report to file."""
        report = self.generate_review_report(batch_id)
        batch = self.batches[batch_id]
        
        if format == 'json':
            report_file = self.review_data_dir / "reports" / f"review_report_{batch_id}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        elif format == 'csv':
            report_file = self.review_data_dir / "reports" / f"review_report_{batch_id}.csv"
            df = pd.DataFrame(report['files'])
            df.to_csv(report_file, index=False)
        
        elif format == 'html':
            report_file = self.review_data_dir / "reports" / f"review_report_{batch_id}.html"
            self._generate_html_report(report, report_file)
        
        return str(report_file)
    
    def _generate_html_report(self, report: Dict[str, Any], output_file: Path):
        """Generate HTML report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Review Report - {report['batch_info']['batch_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .file-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .file-table th, .file-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .file-table th {{ background-color: #f2f2f2; }}
                .status-approved {{ color: green; }}
                .status-rejected {{ color: red; }}
                .status-pending {{ color: orange; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Review Report</h1>
                <h2>{report['batch_info']['batch_name']}</h2>
                <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>Files</h3>
                    <p>Total: {report['batch_info']['total_files']}</p>
                    <p>Approved: {report['batch_info']['approved_files']}</p>
                    <p>Rejected: {report['batch_info']['rejected_files']}</p>
                    <p>Pending: {report['batch_info']['pending_files']}</p>
                </div>
                <div class="stat-card">
                    <h3>Size</h3>
                    <p>Total: {report['statistics']['total_size_mb']:.2f} MB</p>
                    <p>Pages: {report['statistics']['total_pages']}</p>
                </div>
                <div class="stat-card">
                    <h3>File Types</h3>
                    {''.join(f'<p>{ext}: {count}</p>' for ext, count in report['statistics']['file_types'].items())}
                </div>
            </div>
            
            <h3>Files</h3>
            <table class="file-table">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Type</th>
                        <th>Size (MB)</th>
                        <th>Pages</th>
                        <th>Status</th>
                        <th>Issues</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{f['filename']}</td>
                        <td>{f['file_type']}</td>
                        <td>{f['file_size'] / (1024*1024):.2f}</td>
                        <td>{f['estimated_pages'] or 'N/A'}</td>
                        <td class="status-{f['review_status']}">{f['review_status'].title()}</td>
                        <td>{', '.join(f['integrity_issues']) if f['integrity_issues'] else 'None'}</td>
                    </tr>
                    ''' for f in report['files'])}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """Get overall review statistics."""
        total_batches = len(self.batches)
        total_files = len(self.file_reviews)
        
        status_counts = {}
        for review in self.file_reviews.values():
            status_counts[review.review_status] = status_counts.get(review.review_status, 0) + 1
        
        file_type_counts = {}
        for review in self.file_reviews.values():
            file_type_counts[review.file_type] = file_type_counts.get(review.file_type, 0) + 1
        
        total_size = sum(review.file_size for review in self.file_reviews.values())
        
        return {
            'total_batches': total_batches,
            'total_files': total_files,
            'status_counts': status_counts,
            'file_type_counts': file_type_counts,
            'total_size_mb': total_size / (1024 * 1024),
            'average_file_size_mb': (total_size / total_files) / (1024 * 1024) if total_files > 0 else 0
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize review workflow
    workflow = ReviewWorkflow()
    
    # Example: Create a review batch
    test_files = [
        "tests/inputs/sample_document.pdf",
        "tests/inputs/sample_email.eml",
        "tests/inputs/sample_image.jpg"
    ]
    
    # Filter existing files
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if existing_files:
        batch_id = workflow.create_review_batch(
            batch_name="Test Review Batch",
            files=existing_files,
            created_by="test_user",
            processing_settings={
                "bates_prefix": "TEST",
                "start_number": 1000,
                "include_metadata": True
            }
        )
        
        print(f"Created review batch: {batch_id}")
        
        # Get batch files
        batch_files = workflow.get_batch_files(batch_id)
        print(f"Batch contains {len(batch_files)} files")
        
        # Preview first file
        if batch_files:
            first_file = batch_files[0]
            metadata = workflow.preview_file_metadata(first_file.file_id)
            print(f"First file metadata: {metadata['file_info']}")
        
        # Generate report
        report = workflow.generate_review_report(batch_id)
        print(f"Report generated with {len(report['files'])} files")
        
        # Export report
        report_file = workflow.export_review_report(batch_id, 'html')
        print(f"Report exported to: {report_file}")
    else:
        print("No test files found. Please ensure test files exist in tests/inputs/") 