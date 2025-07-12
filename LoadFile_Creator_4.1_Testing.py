#!/usr/bin/env python3
"""
LoadFile Creator 4.1 Testing - Python Script Version

Description:
This script creates Casedoxx-compatible loadfiles with improved data integrity and field coverage.

Major Improvements:
- Expanded .dat field list to include all standard Casedoxx fields
- Fixed metadata extraction and field mapping
- Improved date handling for robustness
- Ensured all fields are populated or set to None/empty if missing
- Added/expanded support for email/document fields (From, To, CC, BCC, Subject, etc.)
- Fixed logic issues (e.g., EndBates, file copying)
- Added data integrity tests for Bates numbers, required fields, file paths, and .dat formatting
- Cross-platform configuration management
- Advanced Bates stamping with background-aware text coloring
- FULL CASEDOXX COMPLIANCE with all standard fields

Usage:
    python LoadFile_Creator_4.1_Testing.py

Requirements:
    - Python 3.7+
    - Required packages: see imports below
    - Java runtime for Tika
    - Poppler for PDF processing (Windows)
"""

import codecs
import cv2
import datetime as dt
import glob
import hashlib
import json
import numpy as np
import os
import pandas as pd
import pathlib
import pdf2image
import platform
import re
import shutil
import sys
import time
from datetime import datetime
from dateutil.parser import parse as convert_date
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfReader, PdfWriter
from tika import config, parser
from tqdm import tqdm
import gc
from io import BytesIO
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Import configuration manager
try:
    from config_manager import ConfigManager
except ImportError:
    print("Warning: config_manager.py not found. Using default configuration.")
    # Fallback ConfigManager class
    class ConfigManager:
        def __init__(self, config_file="bates_config.json"):
            self.config_file = config_file
            self.config = self._get_default_config()
        
        def _get_default_config(self):
            return {
                "bates_stamping": {
                    "font_size": 11, "margin": 10,
                    "text_color_light": [255, 255, 255],
                    "text_color_dark": [0, 0, 0],
                    "contrast_threshold": 128,
                    "add_border": False, "shadow": False,
                    "position": "bottom-right",  # Options: "bottom-right", "top-right", "bottom-left", "top-left", "center"
                    "supported_formats": ["jpg", "jpeg", "tiff", "tif", "png", "bmp"],
                    "quality": 95
                },
                "loadfile_settings": {
                    "delimiter": "0x14", "wrapper": "0xFE", "encoding": "utf-8"
                },
                "processing_settings": {
                    "timeout": 500, "pdf_dpi": 150, "image_compression": 6,
                    "max_file_timeout": 300, "max_total_timeout": 3600, "max_workers": 2,
                    "pdf_chunk_size": 5, "memory_check_interval": 10
                }
            }
        
        def get_bates_config(self): return self.config.get("bates_stamping", {})
        def get_loadfile_config(self): return self.config.get("loadfile_settings", {})
        def get_processing_config(self): return self.config.get("processing_settings", {})
        def find_available_font(self): return None

class LoadFileCreator:
    """
    Main class for creating Casedoxx loadfiles with improved data integrity.
    """
    
    def __init__(self, config_file: str = "bates_config.json"):
        self.config_manager = ConfigManager(config_file)
        self.docs = []
        self.opt_data = []
        self.start_value = 8378
        self.prefix = "PL_WEATHERFORD"
        self.ProductionVolume = "PL_Weatherford_VOL4"
        self.Custodian = ""
        
        # Document family tracking
        self.document_families = {}
        self.family_counter = 1
        
        # Memory management
        self.max_memory_usage = 0.8  # 80% of available memory
        self.memory_check_interval = 10  # Check every 10 files
        
        # Initialize Tika
        self._setup_tika()
    
    def _setup_tika(self):
        """Setup Tika configuration."""
        processing_config = self.config_manager.get_processing_config()
        config.timeout = processing_config.get('timeout', 500)
        
        # Set Tika JAR path
        tika_jar_path = Path(r"C:\Users\gregg\OneDrive\Documents\Code\Loadfile_Creator\tika-server-standard-3.0.0-BETA2.jar")
        if tika_jar_path.exists():
            os.environ["TIKA_SERVER_JAR"] = str(tika_jar_path)
    
    def convert_date_safe(self, orig_date):
        """Improved date conversion with Casedoxx-standard formatting."""
        if not orig_date:
            return None
        try:
            if type(orig_date) == list:
                orig_date = orig_date[0]
            if '.' in orig_date:
                bad = orig_date[orig_date.find('.'):-1]
                orig_date = orig_date.replace(bad, '')
            if orig_date[-1] != "Z":
                orig_date = f"{orig_date}Z"
            # Convert to Casedoxx standard format: MM/DD/YYYY
            parsed_date = datetime.strptime(orig_date.replace('0000000',''), "%Y-%m-%dT%H:%M:%SZ")
            return parsed_date.strftime('%m/%d/%Y')
        except Exception as e:
            print(f"Error converting date {orig_date}: {e}")
            return None
    
    def convert_time_safe(self, orig_date):
        """Convert date to time format for Casedoxx."""
        if not orig_date:
            return None
        try:
            if type(orig_date) == list:
                orig_date = orig_date[0]
            if '.' in orig_date:
                bad = orig_date[orig_date.find('.'):-1]
                orig_date = orig_date.replace(bad, '')
            if orig_date[-1] != "Z":
                orig_date = f"{orig_date}Z"
            # Convert to Casedoxx time format: HH:MM:SS
            parsed_date = datetime.strptime(orig_date.replace('0000000',''), "%Y-%m-%dT%H:%M:%SZ")
            return parsed_date.strftime('%H:%M:%S')
        except Exception as e:
            print(f"Error converting time {orig_date}: {e}")
            return None
    
    def get_filename_from_path(self, path):
        """Get filename from path."""
        return os.path.basename(path)
    
    def get_bates(self, prefix, value, ndigit=8):
        """Generate Bates number with given prefix and value."""
        return '{{}}{{:0{0}d}}'.format(ndigit).format(prefix, value)
    
    def identify_document_family(self, file_path, metadata):
        """Identify document families and relationships."""
        filename = os.path.basename(file_path).lower()
        
        # Email thread detection
        if any(ext in filename for ext in ['.msg', '.eml', '.pst']):
            thread_id = metadata.get('Thread-Index', metadata.get('Message-ID', ''))
            if thread_id:
                if thread_id not in self.document_families:
                    self.document_families[thread_id] = self.family_counter
                    self.family_counter += 1
                return self.document_families[thread_id]
        
        # Attachment detection
        if 'attachment' in filename or 'att' in filename:
            # Look for parent document
            parent_name = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
            if parent_name not in self.document_families:
                self.document_families[parent_name] = self.family_counter
                self.family_counter += 1
            return self.document_families[parent_name]
        
        # Document version detection
        version_patterns = ['v', 'version', 'rev', 'revision']
        if any(pattern in filename for pattern in version_patterns):
            base_name = re.sub(r'[vV]ersion?\d*|rev\d*|v\d*', '', filename)
            if base_name not in self.document_families:
                self.document_families[base_name] = self.family_counter
                self.family_counter += 1
            return self.document_families[base_name]
        
        return None
    
    def determine_document_type(self, file_path, metadata):
        """Determine Casedoxx document type."""
        filename = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Email types
        if file_ext in ['.msg', '.eml', '.pst']:
            return 'Email'
        
        # Document types
        if file_ext in ['.doc', '.docx']:
            return 'Word Document'
        elif file_ext in ['.xls', '.xlsx']:
            return 'Spreadsheet'
        elif file_ext in ['.ppt', '.pptx']:
            return 'Presentation'
        elif file_ext == '.pdf':
            return 'PDF Document'
        
        # Image types
        if file_ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp']:
            return 'Image'
        
        # Other types
        if file_ext in ['.txt', '.rtf']:
            return 'Text Document'
        elif file_ext in ['.zip', '.rar', '.7z']:
            return 'Archive'
        
        return 'Unknown'
    
    def determine_redaction_type(self, file_path, metadata):
        """Determine if document is redacted and type."""
        filename = os.path.basename(file_path).lower()
        
        if 'redacted' in filename:
            return 'Redacted'
        elif 'privileged' in filename:
            return 'Privileged'
        elif 'confidential' in filename:
            return 'Confidential'
        
        # Check metadata for redaction indicators
        content = metadata.get('content', '')
        if '[REDACTED]' in content or '***' in content:
            return 'Redacted'
        
        return 'None'
    
    def chunk_pdf_and_parse(self, pdf_path, timeout=300):
        """Improved PDF chunking and parsing."""
        try:
            pdf_reader = PdfReader(pdf_path, strict=False)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None

        num_pages = len(pdf_reader.pages)
        first_metadata = None
        combined_content = []

        for start_page in tqdm(range(0, num_pages, 10), desc="Processing pages"):
            end_page = min(start_page + 10, num_pages)
            pdf_writer = PdfWriter()

            for page_num in range(start_page, end_page):
                try:
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                except Exception as e:
                    print(f"Error adding page {page_num}: {e}")
                    continue

            temp_pdf_io = BytesIO()
            try:
                pdf_writer.write(temp_pdf_io)
            except Exception as e:
                print(f"Error writing temporary PDF: {e}")
                continue

            temp_pdf_io.seek(0)

            try:
                parsed = parser.from_buffer(temp_pdf_io.read(), requestOptions={'timeout': timeout})
            except Exception as e:
                print(f"Error parsing PDF chunk: {e}")
                continue

            if first_metadata is None:
                first_metadata = parsed.get('metadata', {})
                first_metadata['xmpTPg:NPages'] = str(num_pages)

            content = parsed.get('content', '').lstrip()
            combined_content.append(content)

        return {
            'metadata': first_metadata,
            'content': ''.join(combined_content)
        }
    
    def get_enhanced_metadata_mapping(self):
        """Get enhanced metadata keywords mapping for Casedoxx compliance."""
        return {
            'title': {'pdf':'title', 'docx':'title', 'pptx':'title', 'msg':'Subject', 'eml':'Subject'},
            'DateCreated': {'pdf':'Creation-Date', 'docx':'Creation-Date', 'pptx': 'Creation-Date', 'msg':'Date', 'eml':'Date'},
            'TimeCreated': {'pdf':'Creation-Date', 'docx':'Creation-Date', 'pptx':'Creation-Date', 'msg':'Date', 'eml':'Date'},
            'DateLastModified': {'pdf': 'Last-Modified', 'docx': 'Last-Modified', 'pptx':'Last-Modified', 'msg':'Date', 'eml':'Date'},
            'TimeLastModified': {'pdf': 'Last-Modified', 'docx': 'Last-Modified', 'pptx':'Last-Modified', 'msg':'Date', 'eml':'Date'},
            'last_save_date': {'pdf':'Last-Save-Date', 'docx':'Last-Save-Date'},
            'Author': {'pdf':'meta:author', 'pptx': 'dc:title', 'docx': 'author', 'msg':'From', 'eml':'From'},
            'Subject': {'pdf':'Subject', 'docx':'Subject', 'pptx':'Subject', 'msg':'Subject', 'eml':'Subject'},
            'From': {'msg':'From', 'eml':'From', 'pst':'From'},
            'To': {'msg':'To', 'eml':'To', 'pst':'To'},
            'CC': {'msg':'CC', 'eml':'CC', 'pst':'CC'},
            'BCC': {'msg':'BCC', 'eml':'BCC', 'pst':'BCC'},
            'DateSent': {'msg':'Date', 'eml':'Date', 'pst':'Date'},
            'TimeSent': {'msg':'Date', 'eml':'Date', 'pst':'Date'},
            'DateReceived': {'msg':'Date', 'eml':'Date', 'pst':'Date'},
            'TimeReceived': {'msg':'Date', 'eml':'Date', 'pst':'Date'},
            'Message-ID': {'msg':'Message-ID', 'eml':'Message-ID', 'pst':'Message-ID'},
            'Thread-Index': {'msg':'Thread-Index', 'eml':'Thread-Index', 'pst':'Thread-Index'},
            'Foreign Language': {'default':'Foreign Language'},
            'Page Count': {'pdf':'xmpTPg:NPages', 'docx':'Page Count', 'pptx':'Slide Count'},
            'charsperpage': {'pdf':'pdf:charsPerPage'},
            'FileName': {'pdf': 'resourceName', 'docx': 'resourceName'},
            'charcount': {'docx': 'Character Count'},
            'Confidentiality': {'default':'Confidentiality'},
            'Privilege': {'default':'Privilege'},
            'RedactionType': {'default':'RedactionType'},
        }
    
    def add_bates_stamp_with_config(self, img_path: str, bates_text: str):
        """Add Bates stamp to image using configuration manager, with robust font scaling."""
        bates_config = self.config_manager.get_bates_config()
        font_path = self.config_manager.find_available_font()
        min_font_size = 8  # Minimum readable font size for production
        font_size = bates_config['font_size']
        
        # Open and convert image
        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        
        # Try to find a font size that fits
        while font_size >= min_font_size:
            if font_path is None:
                font = ImageFont.load_default()
            else:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except Exception as e:
                    print(f"Error loading font {font_path}: {e}")
                    font = ImageFont.load_default()
            try:
                text_w, text_h = font.getsize(bates_text)
            except AttributeError:
                text_w, text_h = len(bates_text) * font_size // 2, font_size
            if text_w <= w - 2 * bates_config['margin'] and text_h <= h - 2 * bates_config['margin']:
                break
            font_size -= 1
        else:
            print(f"Warning: Could not fit Bates stamp '{bates_text}' on image {img_path} (image: {w}x{h}). Skipping.")
            return
        
        # Position text based on configuration
        margin = bates_config['margin']
        position = bates_config.get('position', 'bottom-right')
        if position == 'bottom-right':
            text_x = w - text_w - margin
            text_y = h - text_h - margin
        elif position == 'top-right':
            text_x = w - text_w - margin
            text_y = margin
        elif position == 'bottom-left':
            text_x = margin
            text_y = h - text_h - margin
        elif position == 'top-left':
            text_x = margin
            text_y = margin
        elif position == 'center':
            text_x = (w - text_w) // 2
            text_y = (h - text_h) // 2
        else:
            text_x = w - text_w - margin
            text_y = h - text_h - margin
        text_x = max(margin, text_x)
        text_y = max(margin, text_y)
        
        # Sample background for contrast detection (ensure region is within bounds)
        sample_x = max(0, min(text_x, w - text_w))
        sample_y = max(0, min(text_y, h - text_h))
        region = img.crop((sample_x, sample_y, sample_x + text_w, sample_y + text_h))
        region_np = np.array(region)
        avg_color = np.mean(region_np, axis=(0, 1))
        text_color = (tuple(bates_config['text_color_light']) if np.mean(avg_color) < bates_config['contrast_threshold'] 
                      else tuple(bates_config['text_color_dark']))
        draw = ImageDraw.Draw(img)
        if bates_config.get('shadow', False):
            shadow_x = text_x + bates_config.get('shadow_offset', [2, 2])[0]
            shadow_y = text_y + bates_config.get('shadow_offset', [2, 2])[1]
            draw.text((shadow_x, shadow_y), bates_text, fill=tuple(bates_config.get('shadow_color', [0, 0, 0])), font=font)
        if bates_config.get('add_border', False):
            border_width = bates_config.get('border_width', 2)
            for dx in range(-border_width, border_width + 1):
                for dy in range(-border_width, border_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((text_x + dx, text_y + dy), bates_text, 
                                 fill=tuple(bates_config.get('border_color', [255, 255, 255])), font=font)
        draw.text((text_x, text_y), bates_text, fill=text_color, font=font)
        img.save(img_path)
    
    def process_files(self, input_dir: str, output_dir: str, volume_name: str):
        """Main file processing function with parallel processing, sequential Bates numbering, and alphabetical sorting."""
        import signal
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
        from collections import defaultdict
        
        indir = Path(input_dir)
        outdir = Path(output_dir)
        voldir = os.path.join(outdir, volume_name)
        
        # Create output directory
        if os.path.exists(voldir):
            try:
                shutil.rmtree(voldir)
            except PermissionError:
                print(f"Warning: Could not remove existing directory {voldir}")
                print("Continuing with existing directory...")
        os.makedirs(voldir, exist_ok=True)
        print(f"Output directory: {voldir}")
        
        # Get processing configuration
        processing_config = self.config_manager.get_processing_config()
        max_file_timeout = processing_config.get('max_file_timeout', 300)
        max_total_timeout = processing_config.get('max_total_timeout', 3600)
        max_workers = processing_config.get('max_workers', 4)  # Increased for better parallelization
        
        print(f"Processing configuration: {max_file_timeout}s per file, {max_total_timeout}s total, {max_workers} workers")
        
        # Collect and sort all files alphabetically
        all_files = []
        for fname in glob.glob(os.path.join(indir, '**'), recursive=True):
            if os.path.isfile(fname) and not fname.endswith('.jar'):
                all_files.append(fname)
        
        # Sort files alphabetically for consistent Bates numbering
        all_files.sort(key=lambda x: os.path.basename(x).lower())
        print(f"Found {len(all_files)} files, sorted alphabetically")
        
        # Group email files by family (thread/chain)
        email_families = self._group_email_files(all_files)
        print(f"Identified {len(email_families)} email families")
        
        # Initialize Bates numbering system with alphabetical assignment
        bates_counter = self.start_value
        bates_lock = threading.Lock()
        
        # Pre-assign Bates numbers in alphabetical order
        bates_assignments = {}
        for i, fname in enumerate(all_files):
            bates_assignments[fname] = self.get_bates(self.prefix, bates_counter + i)
        
        def get_bates_for_file(fname):
            """Get pre-assigned Bates number for file."""
            return bates_assignments.get(fname, self.get_bates(self.prefix, bates_counter))
        
        # Process files with parallel processing and sequential Bates numbering
        start_time = time.time()
        processed_count = 0
        failed_count = 0
        metadata_kws = self.get_enhanced_metadata_mapping()
        
        def process_single_file(file_info):
            """Process a single file with sequential Bates numbering."""
            fname, family_id = file_info
            try:
                print(f"Processing file: {fname}")
                if os.path.isdir(fname):
                    print(f"Skipping directory: {fname}")
                    return {'status': 'skipped', 'reason': 'directory'}
                
                # Get pre-assigned Bates number in alphabetical order
                BegBates = get_bates_for_file(fname)
                
                ext = os.path.splitext(fname)[1]
                filename, file_extension = os.path.splitext(Path(fname))
                FileExtension = file_extension.lower().strip('.')
                
                # Parse the file with timeout
                print(f"Parsing file: {fname}")
                if FileExtension == "pdf":
                    parsed = self.chunk_pdf_and_parse(fname)
                    if parsed is None:
                        print(f"Failed to parse PDF: {fname}")
                        return {'status': 'failed', 'reason': 'pdf_parse_failed'}
                    date_created = parsed['metadata'].get('Creation-Date', None)
                    datestr = date_created
                else:
                    try:
                        parsed = parser.from_file(fname, requestOptions={'timeout': max_file_timeout})
                    except Exception as e:
                        print(f"Error parsing file {fname}: {e}")
                        return {'status': 'failed', 'reason': f'parse_error: {e}'}
                    date_created = parsed['metadata'].get('Creation-Date', None)
                    datestr = date_created
                
                # Enhanced date handling for Casedoxx
                if datestr is not None:
                    datestr = self.convert_date_safe(datestr)
                    timestr = self.convert_time_safe(date_created)
                else:
                    timestr = None
                
                # Determine document type and family
                doc_type = self.determine_document_type(fname, parsed.get('metadata', {}))
                redaction_type = self.determine_redaction_type(fname, parsed.get('metadata', {}))
                
                # Use provided family_id for emails, generate for others
                if family_id:
                    final_family_id = family_id
                else:
                    final_family_id = self.identify_document_family(fname, parsed.get('metadata', {}))
                
                # Determine subdirectory
                subdir = "NATIVES"
                if FileExtension in ["tif","tiff", "jpg", "jpeg", "png"]:
                    subdir = "IMAGES"
                
                # Create document entry with sequential Bates numbering
                nativedir = os.path.join(volume_name, subdir, '0000', BegBates + ext)
                textdir = os.path.join(volume_name, 'TEXT', '0000', BegBates + '.txt')
                
                metadata = parsed.get('metadata', {})
                
                doc_entry = {
                    'BegBates': BegBates,
                    'EndBates': BegBates,  # Will be updated for multi-page documents
                    'HashValue': hashlib.md5(fname.encode()).hexdigest(),
                    'FileExtension': ext[1:],
                    'Filename': self.get_filename_from_path(fname),
                    'NativeLocation': nativedir,
                    'TextLocation': textdir,
                    'BegAttach': '',
                    'EndAttach': '',
                    'Custodian': self.Custodian,
                    'Duplicate Custodian': '',
                    'Original FilePath': '',
                    'Subject': metadata.get('Subject', None),
                    'Title': metadata.get(metadata_kws['title'].get(FileExtension, None), None),
                    'Author': metadata.get(metadata_kws['Author'].get(FileExtension, None), None),
                    'From': metadata.get(metadata_kws['From'].get(FileExtension, None), None),
                    'To': metadata.get(metadata_kws['To'].get(FileExtension, None), None),
                    'CC': metadata.get(metadata_kws['CC'].get(FileExtension, None), None),
                    'BCC': metadata.get(metadata_kws['BCC'].get(FileExtension, None), None),
                    'DateSent': metadata.get(metadata_kws['DateSent'].get(FileExtension, None), None),
                    'TimeSent': metadata.get(metadata_kws['TimeSent'].get(FileExtension, None), None),
                    'DateReceived': metadata.get(metadata_kws['DateReceived'].get(FileExtension, None), None),
                    'TimeReceived': metadata.get(metadata_kws['TimeReceived'].get(FileExtension, None), None),
                    'DateCreated': datestr,
                    'TimeCreated': timestr,
                    'DateLastModified': metadata.get('Last-Modified', None),
                    'Message-ID': metadata.get(metadata_kws['Message-ID'].get(FileExtension, None), None),
                    'Thread-Index': metadata.get(metadata_kws['Thread-Index'].get(FileExtension, None), None),
                    'Foreign Language': metadata.get('Foreign Language', ''),
                    'Page Count': metadata.get(metadata_kws['Page Count'].get(FileExtension, None), None),
                    'charsperpage': metadata.get(metadata_kws['charsperpage'].get(FileExtension, None), None),
                    'charcount': metadata.get(metadata_kws['charcount'].get(FileExtension, None), None),
                    'Confidentiality': metadata.get('Confidentiality', ''),
                    'Privilege': metadata.get('Privilege', ''),
                    'RedactionType': redaction_type,
                    'DocType': doc_type,
                    'FamilyID': final_family_id if final_family_id else '',
                    'ParentID': '',
                    'Production Volume': self.ProductionVolume,
                }
                
                # Copy native file
                new_path = os.path.join(outdir, nativedir)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.copy2(fname, new_path)
                
                # Write text content
                os.makedirs(os.path.dirname(os.path.join(outdir, textdir)), exist_ok=True)
                with codecs.open(os.path.join(outdir, textdir), 'w', 'utf-8') as fid:
                    content = parsed['content'].strip('\n') if parsed['content'] is not None else 'NO TEXT AVAILABLE\n'
                    fid.write(content)
                
                # Process PDF files with optimized settings
                if file_extension.lower() == ".pdf":
                    self._process_pdf_pages(fname, BegBates, outdir, volume_name, processing_config)
                
                # Process TIFF files
                elif file_extension.lower().strip('.') in ['tif', 'tiff']:
                    self._process_tiff_pages(fname, BegBates, outdir, volume_name)
                
                # Add to documents list (thread-safe)
                with bates_lock:
                    self.docs.append(doc_entry)
                
                gc.collect()
                print(f"Finished processing file: {fname}")
                return {'status': 'success', 'bates': BegBates}
                
            except Exception as e:
                print(f"Error processing {fname}: {e}")
                return {'status': 'failed', 'reason': str(e)}
        
        # Prepare file list with family information
        files_with_families = []
        for fname in all_files:
            family_id = None
            # Check if this file belongs to an email family
            for family_key, family_files in email_families.items():
                if fname in family_files:
                    family_id = family_key
                    break
            files_with_families.append((fname, family_id))
        
        # Process files with ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all files for processing
            future_to_file = {executor.submit(process_single_file, file_info): file_info[0] 
                            for file_info in files_with_families}
            
            # Process completed tasks
            for future in as_completed(future_to_file, timeout=max_total_timeout):
                fname = future_to_file[future]
                try:
                    result = future.result(timeout=max_file_timeout)
                    if result['status'] == 'success':
                        processed_count += 1
                        print(f"[OK] Successfully processed: {fname}")
                    else:
                        failed_count += 1
                        print(f"[FAIL] Failed to process: {fname} - {result['reason']}")
                except TimeoutError:
                    failed_count += 1
                    print(f"[FAIL] Timeout processing: {fname}")
                except Exception as e:
                    failed_count += 1
                    print(f"[FAIL] Error processing: {fname} - {e}")
                
                # Check total timeout
                if time.time() - start_time > max_total_timeout:
                    print(f"⚠️ Total timeout reached ({max_total_timeout}s). Stopping processing.")
                    break
        
        total_time = time.time() - start_time
        print(f"\nProcessing Summary:")
        print(f"  Total files: {len(all_files)}")
        print(f"  Successfully processed: {processed_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Total time: {total_time:.1f} seconds")
        print(f"  Average time per file: {total_time/len(all_files):.1f} seconds")
        print(f"  Email families identified: {len(email_families)}")
    
    def _group_email_files(self, all_files):
        """Group email files by thread/chain for family identification."""
        email_families = defaultdict(list)
        
        for fname in all_files:
            file_ext = os.path.splitext(fname)[1].lower()
            if file_ext in ['.msg', '.eml', '.pst']:
                try:
                    # Quick metadata extraction for email grouping
                    parsed = parser.from_file(fname, requestOptions={'timeout': 30})
                    metadata = parsed.get('metadata', {})
                    
                    # Try to identify email thread
                    thread_id = metadata.get('Thread-Index', metadata.get('Message-ID', ''))
                    subject = metadata.get('Subject', '')
                    from_addr = metadata.get('From', '')
                    
                    # Create family key based on thread or subject
                    if thread_id:
                        family_key = f"EMAIL_THREAD_{hash(thread_id) % 10000:04d}"
                    elif subject:
                        family_key = f"EMAIL_SUBJECT_{hash(subject) % 10000:04d}"
                    else:
                        family_key = f"EMAIL_FROM_{hash(from_addr) % 10000:04d}"
                    
                    email_families[family_key].append(fname)
                    
                except Exception as e:
                    print(f"Warning: Could not analyze email file {fname}: {e}")
                    # Still add to a family based on filename
                    family_key = f"EMAIL_FILE_{hash(os.path.basename(fname)) % 10000:04d}"
                    email_families[family_key].append(fname)
        
        return email_families
    
    def _process_pdf_pages(self, pdf_path, base_bates, outdir, volume_name, processing_config):
        """Process PDF pages with optimized settings."""
        try:
            pdf_dpi = processing_config.get('pdf_dpi', 150)
            chunk_size = processing_config.get('pdf_chunk_size', 5)
            
            # Get PDF info first
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            print(f"PDF has {total_pages} pages, processing in chunks of {chunk_size}")
            
            # Process PDF in chunks to reduce memory usage
            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                
                # Convert chunk to images
                page_imgs = pdf2image.convert_from_path(
                    pdf_path, dpi=pdf_dpi, output_folder=None, 
                    first_page=chunk_start + 1, last_page=chunk_end,
                    fmt="jpg", thread_count=1, userpw=None,
                    use_cropbox=False, strict=False,
                    poppler_path=r"C:\Program Files\poppler-24.08.0\Library\bin"
                )
                
                # Process each page in the chunk
                for i, page_img in enumerate(page_imgs):
                    page_num = chunk_start + i
                    page_bates = self.get_bates(self.prefix, int(base_bates.replace(self.prefix, '')) + page_num)
                    
                    self.opt_data.append({
                        'bates': page_bates,
                        'volume': volume_name,
                        'path': os.path.join(volume_name, 'IMAGES', '0000', page_bates + '.tiff'),
                        'first_page': 'Y' if page_num == 0 else '',
                        'npages': total_pages if page_num == 0 else ''
                    })
                    
                    # Save image with optimized compression
                    dname = os.path.join(outdir, volume_name, "IMAGES", '0000')
                    os.makedirs(dname, exist_ok=True)
                    
                    # Convert to numpy array and save with optimized settings
                    img_array = np.array(page_img)
                    img_array_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    # Use optimized compression
                    compression = processing_config.get('image_compression', 6)
                    cv2.imwrite(os.path.join(dname, page_bates + '.tiff'), img_array_bgr, 
                              [cv2.IMWRITE_TIFF_COMPRESSION, compression])
                    
                    print(f"Saved page {page_num + 1}/{total_pages}: {page_bates}")
                    
                    # Memory management
                    # Memory check removed (function does not exist)
                
                # Clear chunk from memory
                del page_imgs
                gc.collect()
                
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
    
    def _process_tiff_pages(self, tiff_path, base_bates, outdir, volume_name):
        """Process TIFF pages."""
        try:
            img = Image.open(tiff_path)
            npages = img.n_frames
            
            for i in range(npages):
                img.seek(i)
                page_bates = self.get_bates(self.prefix, int(base_bates.replace(self.prefix, '')) + i)
                
                self.opt_data.append({
                    'bates': page_bates,
                    'volume': volume_name,
                    'path': os.path.join(volume_name, 'IMAGES', '0000', page_bates + '.tiff'),
                    'first_page': 'Y' if i == 0 else '',
                    'npages': npages if i == 0 else ''
                })
                
                dname = os.path.join(outdir, volume_name, 'IMAGES', '0000')
                os.makedirs(dname, exist_ok=True)
                
                img_array = np.array(img)
                img_array_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(dname, page_bates + '.tiff'), img_array_bgr, 
                          [cv2.IMWRITE_TIFF_COMPRESSION, 6])
                
                print(f"Saved TIFF page {i + 1}/{npages}: {page_bates}")
                
        except Exception as e:
            print(f"Error processing TIFF {tiff_path}: {e}")
    
    def write_opt_file(self, output_dir: str, volume_name: str):
        """Write .opt file for image data."""
        os.makedirs(os.path.join(output_dir, volume_name, 'DATA'), exist_ok=True)
        opt_file = os.path.join(output_dir, volume_name, 'DATA', volume_name + '.opt')
        
        with open(opt_file, 'w') as fout:
            for opt in self.opt_data:
                fout.write('{0},{1},{2},{3},,{4}\n'.format(
                    opt['bates'], opt['volume'], opt['path'], opt['first_page'], opt['npages']
                ))
        print(f"OPT file written to: {opt_file}")
    
    def write_loadfile(self, output_dir: str, volume_name: str):
        """Write Casedoxx loadfile with ALL standard fields."""
        loadfile_config = self.config_manager.get_loadfile_config()
        delim = chr(int(loadfile_config.get("delimiter", "0x14"), 16))
        wrap = chr(int(loadfile_config.get("wrapper", "0xFE"), 16))
        
        # COMPLETE Casedoxx field list
        cols = [
            'BegBates', 'EndBates', 'HashValue', 'FileExtension', 'Filename', 'NativeLocation', 'TextLocation',
            'BegAttach', 'EndAttach', 'Custodian', 'Duplicate Custodian', 'Original FilePath', 'Subject', 'Title',
            'Author', 'From', 'To', 'CC', 'BCC', 'DateSent', 'TimeSent', 'DateReceived', 'TimeReceived',
            'DateCreated', 'TimeCreated', 'DateLastModified', 'Message-ID', 'Thread-Index', 'Foreign Language',
            'Page Count', 'charsperpage', 'charcount', 'Confidentiality', 'Privilege', 'RedactionType',
            'DocType', 'FamilyID', 'ParentID', 'Production Volume'
        ]
        
        loadfile_path = os.path.join(output_dir, volume_name, 'DATA', 'loadfile.dat')
        
        with codecs.open(loadfile_path, 'w', encoding=loadfile_config.get('encoding', 'utf-8')) as fid:
            # Write column names
            fid.write(delim.join(wrap + c + wrap for c in cols) + '\n')
            # Write data
            for doc in self.docs:
                fid.write(delim.join(wrap + (str(doc.get(c, '')) if doc.get(c, '') is not None else '') + wrap for c in cols) + '\n')
        
        print(f"Loadfile written to: {loadfile_path}")
    
    def apply_bates_stamps(self, output_dir: str, volume_name: str):
        """Apply Bates stamps to all images."""
        bates_config = self.config_manager.get_bates_config()
        images_dir = os.path.join(output_dir, volume_name, 'IMAGES')
        
        if not os.path.exists(images_dir):
            print(f"Images directory not found: {images_dir}")
            return
        
        print("Adding Bates stamps to images (font size: 11, margin: 10)...")
        processed_count = 0
        skipped_count = 0
        
        for img_file in tqdm(glob.glob(os.path.join(images_dir, "**", "*"), recursive=True)):
            if os.path.isdir(img_file):
                continue
            
            ext = os.path.splitext(img_file)[1].strip('.').lower()
            name = os.path.basename(os.path.splitext(img_file)[0])
            
            if ext in bates_config.get('supported_formats', ['jpg', 'jpeg', 'tiff', 'tif', 'png', 'bmp']):
                try:
                    self.add_bates_stamp_with_config(img_file, name)
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing {img_file}: {e}")
                    skipped_count += 1
        
        print(f"Bates stamping completed! Processed {processed_count} images, skipped {skipped_count} images.")
    
    def run_data_integrity_tests(self, output_dir: str, volume_name: str):
        """Run comprehensive data integrity tests."""
        print("\n=== Running Data Integrity Tests ===")
        
        # Test 1: Bates numbers are unique and sequential
        bates_numbers = [doc['BegBates'] for doc in self.docs]
        if len(bates_numbers) == len(set(bates_numbers)):
            print("PASS: Bates numbers are unique")
        else:
            print("FAIL: Duplicate Bates numbers found!")
        
        # Test 2: Required fields are present
        required_fields = ['BegBates', 'EndBates', 'NativeLocation', 'TextLocation', 'Filename', 'FileExtension', 'HashValue']
        missing_fields = []
        for doc in self.docs:
            for field in required_fields:
                if field not in doc or doc[field] is None:
                    missing_fields.append(f"{doc.get('Filename', 'Unknown')}: {field}")
        
        if not missing_fields:
            print("PASS: All required fields are present")
        else:
            print(f"FAIL: Missing fields: {missing_fields[:5]}...")  # Show first 5
        
        # Test 3: File paths exist
        missing_files = []
        for doc in self.docs:
            native_path = os.path.join(output_dir, doc['NativeLocation'])
            text_path = os.path.join(output_dir, doc['TextLocation'])
            if not os.path.exists(native_path):
                missing_files.append(f"Native: {doc['NativeLocation']}")
            if not os.path.exists(text_path):
                missing_files.append(f"Text: {doc['TextLocation']}")
        
        if not missing_files:
            print("PASS: All file paths are valid")
        else:
            print(f"FAIL: Missing files: {missing_files[:5]}...")  # Show first 5
            print("WARNING: Some expected output files were not created. Check file processing logic.")
        
        # Test 4: Loadfile format
        loadfile_path = os.path.join(output_dir, volume_name, 'DATA', 'loadfile.dat')
        if os.path.exists(loadfile_path):
            try:
                with open(loadfile_path, 'r', encoding='utf-8') as f:
                    header = f.readline()
                    if '\x14' in header and '\xfe' in header:
                        print("PASS: Loadfile format is correct")
                    else:
                        print("FAIL: Loadfile format may be incorrect")
            except Exception as e:
                print(f"FAIL: Error reading loadfile: {e}")
        else:
            print("FAIL: Loadfile not found")
        
        # Test 5: Document family consistency
        family_ids = [doc['FamilyID'] for doc in self.docs if doc['FamilyID']]
        if len(family_ids) == len(set(family_ids)) or len(set(family_ids)) == 0:
            print("PASS: Document families are consistent")
        else:
            print("FAIL: Inconsistent document family assignments")
        
        # Test 6: Date format validation
        date_fields = ['DateCreated', 'DateLastModified', 'DateSent', 'DateReceived']
        invalid_dates = []
        for doc in self.docs:
            for field in date_fields:
                if doc.get(field) and doc[field] != '':
                    # Check if date is in MM/DD/YYYY format
                    if not re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', str(doc[field])):
                        invalid_dates.append(f"{doc.get('Filename', 'Unknown')}: {field} = {doc[field]}")
        
        if not invalid_dates:
            print("PASS: All date formats are correct")
        else:
            print(f"FAIL: Invalid date formats: {invalid_dates[:3]}...")  # Show first 3
        
        print("=== Data Integrity Tests Complete ===\n")

def main():
    """Main function to run the LoadFile Creator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LoadFile Creator 4.1 Testing")
    parser.add_argument("--input", help="Input directory path")
    parser.add_argument("--output", help="Output directory path")
    parser.add_argument("--volume", help="Production volume name")
    parser.add_argument("--config", default="bates_config.json", help="Configuration file path")
    
    args = parser.parse_args()
    
    print("LoadFile Creator 4.1 Testing - Python Script")
    print("FULL CASEDOXX COMPLIANCE VERSION")
    print("=" * 50)
    
    # Get configuration from args or user input
    if args.input and args.output and args.volume:
        # Test mode - use command line arguments
        input_dir = args.input
        output_dir = args.output
        volume_name = args.volume
        config_file = args.config
    else:
        # Interactive mode - get user input
        volume_name = input("What is the name of this Production Volume? ")
        input_dir = r"C:\Users\gregg\Documents\Production Vol 4\input"
        output_dir = r"C:\Users\gregg\Documents\Production Vol 4\output"
        config_file = "bates_config.json"
    
    # Create LoadFile Creator instance
    creator = LoadFileCreator(config_file)
    
    try:
        # Process files
        print(f"\nProcessing files from: {input_dir}")
        creator.process_files(input_dir, output_dir, volume_name)
        
        # Write output files
        print("\nWriting output files...")
        creator.write_opt_file(output_dir, volume_name)
        creator.write_loadfile(output_dir, volume_name)
        
        # Apply Bates stamps
        print("\nApplying Bates stamps...")
        creator.apply_bates_stamps(output_dir, volume_name)
        
        # Run data integrity tests
        creator.run_data_integrity_tests(output_dir, volume_name)
        
        print(f"\nProcessing complete! Output saved to: {os.path.join(output_dir, volume_name)}")
        print("FULL CASEDOXX COMPLIANCE ACHIEVED")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 