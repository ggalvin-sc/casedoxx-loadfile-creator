"""
Test Script for Review Workflow
==============================

This script demonstrates the review workflow functionality with sample files.
It shows how to create review batches, preview files, and approve/reject them.

Usage:
    python test_review_workflow.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from review_workflow import ReviewWorkflow

def create_sample_files():
    """Create sample files for testing."""
    sample_dir = Path("test_samples")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample text file
    text_file = sample_dir / "sample_document.txt"
    with open(text_file, 'w') as f:
        f.write("This is a sample text document for testing the review workflow.\n")
        f.write("It contains multiple lines of text to demonstrate content preview.\n")
        f.write("The review workflow should be able to extract this content.\n")
    
    # Create sample CSV file
    csv_file = sample_dir / "sample_data.csv"
    with open(csv_file, 'w') as f:
        f.write("Name,Email,Phone\n")
        f.write("John Doe,john@example.com,555-1234\n")
        f.write("Jane Smith,jane@example.com,555-5678\n")
    
    # Create sample email file
    email_file = sample_dir / "sample_email.eml"
    with open(email_file, 'w') as f:
        f.write("From: sender@example.com\n")
        f.write("To: recipient@example.com\n")
        f.write("Subject: Test Email for Review Workflow\n")
        f.write("Date: Mon, 1 Jan 2024 12:00:00 +0000\n")
        f.write("Message-ID: <test123@example.com>\n")
        f.write("\n")
        f.write("This is a sample email for testing the review workflow.\n")
        f.write("It contains email headers and body content.\n")
    
    return [str(text_file), str(csv_file), str(email_file)]

def test_review_workflow():
    """Test the review workflow functionality."""
    print("🔍 Testing Casedoxx Review Workflow")
    print("=" * 50)
    
    # Initialize workflow
    workflow = ReviewWorkflow()
    
    # Create sample files
    print("\n📁 Creating sample files...")
    sample_files = create_sample_files()
    print(f"✅ Created {len(sample_files)} sample files")
    
    # Create review batch
    print("\n📋 Creating review batch...")
    batch_id = workflow.create_review_batch(
        batch_name="Test Review Batch",
        files=sample_files,
        created_by="test_user",
        processing_settings={
            "bates_prefix": "TEST",
            "start_number": 1000,
            "include_metadata": True
        }
    )
    print(f"✅ Created review batch: {batch_id}")
    
    # Get batch files
    print("\n📄 Getting batch files...")
    batch_files = workflow.get_batch_files(batch_id)
    print(f"✅ Found {len(batch_files)} files in batch")
    
    # Preview file metadata
    print("\n🔍 Previewing file metadata...")
    for file_review in batch_files:
        print(f"\n📄 File: {file_review.filename}")
        print(f"   Type: {file_review.file_type}")
        print(f"   Size: {file_review.file_size} bytes")
        print(f"   Status: {file_review.review_status}")
        
        if file_review.integrity_issues:
            print(f"   ⚠️  Issues: {', '.join(file_review.integrity_issues)}")
        
        # Preview metadata
        metadata = workflow.preview_file_metadata(file_review.file_id)
        print(f"   Metadata keys: {len(metadata['metadata'])}")
        
        if metadata['content_preview']:
            preview = metadata['content_preview'][:100]
            print(f"   Content preview: {preview}...")
    
    # Approve some files
    print("\n✅ Approving files...")
    approved_count = 0
    for file_review in batch_files:
        if file_review.filename.endswith('.txt'):
            workflow.approve_file(
                file_review.file_id, 
                "test_user", 
                "Sample text file approved for testing", 
                1
            )
            approved_count += 1
            print(f"   ✅ Approved: {file_review.filename}")
    
    # Reject some files
    print("\n❌ Rejecting files...")
    rejected_count = 0
    for file_review in batch_files:
        if file_review.filename.endswith('.csv'):
            workflow.reject_file(
                file_review.file_id, 
                "test_user", 
                "Wrong file type", 
                "CSV files not supported in this test"
            )
            rejected_count += 1
            print(f"   ❌ Rejected: {file_review.filename}")
    
    # Get approved files
    print("\n📥 Getting approved files...")
    approved_files = workflow.get_approved_files_for_processing(batch_id)
    print(f"✅ Found {len(approved_files)} approved files ready for processing")
    
    # Generate report
    print("\n📊 Generating review report...")
    report = workflow.generate_review_report(batch_id)
    print(f"✅ Report generated with {len(report['files'])} files")
    print(f"   Total files: {report['batch_info']['total_files']}")
    print(f"   Approved: {report['batch_info']['approved_files']}")
    print(f"   Rejected: {report['batch_info']['rejected_files']}")
    print(f"   Pending: {report['batch_info']['pending_files']}")
    
    # Export report
    print("\n📄 Exporting report...")
    report_file = workflow.export_review_report(batch_id, 'html')
    print(f"✅ Report exported to: {report_file}")
    
    # Get statistics
    print("\n📈 Getting review statistics...")
    stats = workflow.get_review_statistics()
    print(f"✅ Statistics:")
    print(f"   Total batches: {stats['total_batches']}")
    print(f"   Total files: {stats['total_files']}")
    print(f"   Total size: {stats['total_size_mb']:.1f} MB")
    print(f"   File types: {list(stats['file_type_counts'].keys())}")
    
    print("\n🎉 Review workflow test completed successfully!")
    print(f"   - Created {len(sample_files)} sample files")
    print(f"   - Approved {approved_count} files")
    print(f"   - Rejected {rejected_count} files")
    print(f"   - Generated review report")
    
    return True

def cleanup_test_files():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    # Remove test samples
    if os.path.exists("test_samples"):
        shutil.rmtree("test_samples")
        print("   ✅ Removed test_samples directory")
    
    # Remove review data
    if os.path.exists("review_data"):
        shutil.rmtree("review_data")
        print("   ✅ Removed review_data directory")
    
    # Remove uploads
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")
        print("   ✅ Removed uploads directory")

if __name__ == "__main__":
    try:
        # Run test
        success = test_review_workflow()
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Ask user if they want to clean up
        response = input("\n🧹 Clean up test files? (y/n): ")
        if response.lower() in ['y', 'yes']:
            cleanup_test_files()
        else:
            print("   Test files preserved for inspection")
    
    print("\n📝 To run the review dashboard:")
    print("   streamlit run review_dashboard.py") 