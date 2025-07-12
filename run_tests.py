#!/usr/bin/env python3
"""
TestMaster Test Runner for LoadFile Creator

This script runs the complete test suite for the LoadFile Creator application.
It creates test files, runs the program, validates outputs, and generates reports.

Usage:
    python run_tests.py [--create-tests] [--verbose]
"""

import sys
import os
from pathlib import Path
from test_harness import TestMaster

def main():
    """Main test runner function."""
    print("🧪 TestMaster Test Runner for LoadFile Creator")
    print("=" * 60)
    
    # Create test harness
    test_master = TestMaster()
    
    # Check if test files exist, create if needed
    if not test_master.input_dir.exists() or not list(test_master.input_dir.glob("*")):
        print("📁 Creating test files...")
        test_master.create_test_files()
    
    # Run the full test suite
    print("\n🚀 Starting TestMaster test suite...")
    success = test_master.run_full_test_suite()
    
    if success:
        print("\n✅ All tests passed! LoadFile Creator is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the test report for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 