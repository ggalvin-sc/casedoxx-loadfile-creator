#!/usr/bin/env python3
"""
TestMaster Diagnostic and Fix Tool

This script analyzes test failures and proposes fixes for the LoadFile Creator.
It implements steps 3 and 4 of the testing process: diagnose failures and apply fixes.

Usage:
    python diagnose_and_fix.py [--test-report path/to/report.txt]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from test_harness import TestMaster

class DiagnosticAndFix:
    """
    Diagnostic and fix tool for LoadFile Creator test failures.
    """
    
    def __init__(self):
        self.test_master = TestMaster()
        self.fixes_applied = []
        
    def analyze_test_report(self, report_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Analyze test report and identify issues."""
        if report_path is None:
            report_path = self.test_master.output_dir / "test_report.txt"
        
        if not report_path.exists():
            print(f"Test report not found: {report_path}")
            return []
        
        issues = []
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Parse test results
        lines = content.split('\n')
        current_test = None
        
        for line in lines:
            if line.startswith('✗'):
                # Failed test
                test_name = line.split(':')[0].replace('✗', '').strip()
                current_test = {
                    'test_name': test_name,
                    'status': 'failed',
                    'issues': []
                }
                issues.append(current_test)
            elif line.startswith('  -') and current_test:
                # Issue detail
                issue = line.strip()[3:]  # Remove "  - "
                current_test['issues'].append(issue)
        
        return issues
    
    def diagnose_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Diagnose issues and propose fixes."""
        diagnoses = []
        
        for issue in issues:
            diagnosis = {
                'test_name': issue['test_name'],
                'issues': issue['issues'],
                'root_cause': self._identify_root_cause(issue),
                'proposed_fix': self._propose_fix(issue),
                'fix_type': self._categorize_fix(issue)
            }
            diagnoses.append(diagnosis)
        
        return diagnoses
    
    def _identify_root_cause(self, issue: Dict[str, Any]) -> str:
        """Identify the root cause of a test failure."""
        issues_text = ' '.join(issue['issues']).lower()
        
        if 'loadfile not found' in issues_text:
            return "Program failed to create loadfile output"
        elif 'native files directory not found' in issues_text:
            return "Program failed to create native files directory"
        elif 'missing fields' in issues_text:
            return "Loadfile missing required Casedoxx fields"
        elif 'insufficient lines' in issues_text:
            return "Loadfile has incorrect format or structure"
        elif 'program failed' in issues_text:
            return "Program execution failed during processing"
        else:
            return "Unknown issue - requires manual investigation"
    
    def _propose_fix(self, issue: Dict[str, Any]) -> str:
        """Propose a fix for the identified issue."""
        issues_text = ' '.join(issue['issues']).lower()
        
        if 'loadfile not found' in issues_text:
            return """
            Fix: Ensure loadfile creation in write_loadfile method
            - Check if output directory exists
            - Verify file permissions
            - Add error handling for file writing
            """
        elif 'native files directory not found' in issues_text:
            return """
            Fix: Ensure native file copying in process_files method
            - Check if source files exist
            - Verify directory creation
            - Add error handling for file operations
            """
        elif 'missing fields' in issues_text:
            return """
            Fix: Update field list in write_loadfile method
            - Ensure all Casedoxx fields are included
            - Verify field mapping from metadata
            - Add missing field handling
            """
        elif 'insufficient lines' in issues_text:
            return """
            Fix: Validate loadfile format in write_loadfile method
            - Ensure header is written correctly
            - Verify data rows are properly formatted
            - Add format validation
            """
        else:
            return "Manual investigation required - check program logs"
    
    def _categorize_fix(self, issue: Dict[str, Any]) -> str:
        """Categorize the type of fix needed."""
        issues_text = ' '.join(issue['issues']).lower()
        
        if 'loadfile' in issues_text:
            return "loadfile_creation"
        elif 'native' in issues_text:
            return "file_processing"
        elif 'fields' in issues_text:
            return "field_mapping"
        elif 'format' in issues_text:
            return "output_format"
        else:
            return "general"
    
    def apply_fixes(self, diagnoses: List[Dict[str, Any]]) -> bool:
        """Apply proposed fixes to the LoadFile Creator code."""
        print("🔧 Applying fixes to LoadFile Creator...")
        
        fixes_applied = []
        
        for diagnosis in diagnoses:
            fix_type = diagnosis['fix_type']
            
            if fix_type == "loadfile_creation":
                success = self._fix_loadfile_creation()
                if success:
                    fixes_applied.append("loadfile_creation")
            
            elif fix_type == "file_processing":
                success = self._fix_file_processing()
                if success:
                    fixes_applied.append("file_processing")
            
            elif fix_type == "field_mapping":
                success = self._fix_field_mapping()
                if success:
                    fixes_applied.append("field_mapping")
            
            elif fix_type == "output_format":
                success = self._fix_output_format()
                if success:
                    fixes_applied.append("output_format")
        
        self.fixes_applied = fixes_applied
        return len(fixes_applied) > 0
    
    def _fix_loadfile_creation(self) -> bool:
        """Fix loadfile creation issues."""
        try:
            # Read the current LoadFile Creator code
            with open("LoadFile_Creator_4.1_Testing.py", 'r') as f:
                content = f.read()
            
            # Add error handling to write_loadfile method
            if 'def write_loadfile(' in content:
                # Check if error handling already exists
                if 'try:' not in content or 'except Exception' not in content:
                    # Add error handling
                    content = content.replace(
                        'def write_loadfile(self, output_dir: str, volume_name: str):',
                        '''    def write_loadfile(self, output_dir: str, volume_name: str):
        """Write Casedoxx loadfile with ALL standard fields."""
        try:'''
                    )
                    
                    # Add except block before the print statement
                    content = content.replace(
                        '        print(f"Loadfile written to: {loadfile_path}")',
                        '''        print(f"Loadfile written to: {loadfile_path}")
        except Exception as e:
            print(f"Error writing loadfile: {e}")
            raise'''
                    )
                    
                    # Write the updated content
                    with open("LoadFile_Creator_4.1_Testing.py", 'w') as f:
                        f.write(content)
                    
                    print("Added error handling to loadfile creation")
                    return True
            
            return False
        except Exception as e:
            print(f"Error applying loadfile fix: {e}")
            return False
    
    def _fix_file_processing(self) -> bool:
        """Fix file processing issues."""
        try:
            # Read the current LoadFile Creator code
            with open("LoadFile_Creator_4.1_Testing.py", 'r') as f:
                content = f.read()
            
            # Add directory creation and error handling to process_files method
            if 'def process_files(' in content:
                # Ensure directory creation exists
                if 'os.makedirs(' not in content:
                    # Add directory creation
                    content = content.replace(
                        '        # Copy native file',
                        '''        # Ensure output directories exist
        os.makedirs(os.path.join(outdir, os.path.dirname(nativedir)), exist_ok=True)
        os.makedirs(os.path.join(outdir, os.path.dirname(textdir)), exist_ok=True)
        
        # Copy native file'''
                    )
                    
                    # Write the updated content
                    with open("LoadFile_Creator_4.1_Testing.py", 'w') as f:
                        f.write(content)
                    
                    print("Added directory creation to file processing")
                    return True
            
            return False
        except Exception as e:
            print(f"Error applying file processing fix: {e}")
            return False
    
    def _fix_field_mapping(self) -> bool:
        """Fix field mapping issues."""
        try:
            # Read the current LoadFile Creator code
            with open("LoadFile_Creator_4.1_Testing.py", 'r') as f:
                content = f.read()
            
            # Ensure all Casedoxx fields are included
            required_fields = [
                'BegBates', 'EndBates', 'HashValue', 'FileExtension', 'Filename',
                'NativeLocation', 'TextLocation', 'BegAttach', 'EndAttach',
                'Custodian', 'Duplicate Custodian', 'Original FilePath', 'Subject',
                'Title', 'Author', 'From', 'To', 'CC', 'BCC', 'DateSent',
                'TimeSent', 'DateReceived', 'TimeReceived', 'DateCreated',
                'TimeCreated', 'DateLastModified', 'Message-ID', 'Thread-Index',
                'Foreign Language', 'Page Count', 'charsperpage', 'charcount',
                'Confidentiality', 'Privilege', 'RedactionType', 'DocType',
                'FamilyID', 'ParentID', 'Production Volume'
            ]
            
            # Check if all fields are present in the cols list
            if 'cols = [' in content:
                # Verify all required fields are included
                missing_fields = []
                for field in required_fields:
                    if field not in content:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"⚠️  Missing fields in loadfile: {missing_fields}")
                    return False
                else:
                    print("All required Concordance fields are present")
                    return True
            
            return False
        except Exception as e:
            print(f"Error applying field mapping fix: {e}")
            return False
    
    def _fix_output_format(self) -> bool:
        """Fix output format issues."""
        try:
            # Read the current LoadFile Creator code
            with open("LoadFile_Creator_4.1_Testing.py", 'r') as f:
                content = f.read()
            
            # Add format validation to write_loadfile method
            if 'def write_loadfile(' in content:
                # Add format validation after writing
                content = content.replace(
                    '        print(f"Loadfile written to: {loadfile_path}")',
                    '''        print(f"Loadfile written to: {loadfile_path}")
        
        # Validate loadfile format
        try:
            with open(loadfile_path, 'r', encoding=loadfile_config.get('encoding', 'utf-8')) as f:
                lines = f.readlines()
                if len(lines) < 2:
                    raise ValueError("Loadfile must have at least header and one data row")
                if not lines[0].strip():
                    raise ValueError("Loadfile header is empty")
            print("Loadfile format validated successfully")'''
                )
                
                # Write the updated content
                with open("LoadFile_Creator_4.1_Testing.py", 'w') as f:
                    f.write(content)
                
                print("Added format validation to loadfile creation")
                return True
            
            return False
        except Exception as e:
            print(f"Error applying output format fix: {e}")
            return False
    
    def generate_diagnostic_report(self, diagnoses: List[Dict[str, Any]]) -> str:
        """Generate a diagnostic report."""
        report = []
        report.append("=" * 80)
        report.append("TESTMASTER DIAGNOSTIC REPORT")
        report.append("=" * 80)
        report.append("")
        
        for diagnosis in diagnoses:
            report.append(f"Test: {diagnosis['test_name']}")
            report.append(f"Root Cause: {diagnosis['root_cause']}")
            report.append(f"Fix Type: {diagnosis['fix_type']}")
            report.append("Issues:")
            for issue in diagnosis['issues']:
                report.append(f"  - {issue}")
            report.append("Proposed Fix:")
            report.append(diagnosis['proposed_fix'])
            report.append("-" * 40)
            report.append("")
        
        # Save report
        report_path = self.test_master.output_dir / "diagnostic_report.txt"
        with open(report_path, 'w') as f:
            f.write('\n'.join(report))
        
        return '\n'.join(report)
    
    def run_diagnostic_and_fix(self) -> bool:
        """Run the complete diagnostic and fix process."""
        print("🔍 Running diagnostic and fix process...")
        
        # Step 1: Analyze test report
        issues = self.analyze_test_report()
        
        if not issues:
            print("✅ No issues found in test report")
            return True
        
        # Step 2: Diagnose issues
        diagnoses = self.diagnose_issues(issues)
        
        # Step 3: Generate diagnostic report
        self.generate_diagnostic_report(diagnoses)
        
        # Step 4: Apply fixes
        fixes_applied = self.apply_fixes(diagnoses)
        
        if fixes_applied:
            print(f"🔧 Applied {len(self.fixes_applied)} fixes")
            
            # Step 5: Re-run tests
            print("🔄 Re-running tests after fixes...")
            success = self.test_master.run_full_test_suite()
            
            if success:
                print("✅ All tests passed after fixes!")
                return True
            else:
                print("❌ Tests still failing after fixes")
                return False
        else:
            print("⚠️  No fixes were applied")
            return False

def main():
    """Main function to run diagnostic and fix process."""
    diagnostic = DiagnosticAndFix()
    
    success = diagnostic.run_diagnostic_and_fix()
    
    if success:
        print("\n🎉 Diagnostic and fix process completed successfully!")
        return 0
    else:
        print("\n❌ Diagnostic and fix process failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 