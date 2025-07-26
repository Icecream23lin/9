#!/usr/bin/env python3
"""
Simple test runner for core WIL visualization functionality

This runs a subset of the most important tests to verify basic functionality.
"""

import sys
import os
import subprocess

def main():
    """Run simple core tests"""
    
    print("🧪 Running Core WIL Visualization Tests")
    print("=" * 50)
    
    # Core tests to run
    core_tests = [
        "tests/test_visualization_service.py::TestWILReportAnalyzer::test_analyzer_initialization",
        "tests/test_visualization_service.py::TestWILReportAnalyzer::test_load_data_success",
        "tests/test_visualization_service.py::TestWILReportAnalyzer::test_generate_analysis_summary",
        "tests/test_visualization_api.py::TestVisualizationAPI::test_analyze_endpoint_no_file",
        "tests/test_visualization_api.py::TestVisualizationAPI::test_analyze_endpoint_invalid_file_type",
        "tests/test_visualization_api.py::TestVisualizationAPI::test_analyze_with_minimal_data",
    ]
    
    cmd = ['python', '-m', 'pytest'] + core_tests + ['-v', '--tb=short']
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd)
    
    print("-" * 50)
    if result.returncode == 0:
        print("✅ All core tests passed!")
        print("\n📊 Core functionality verified:")
        print("  • WILReportAnalyzer initialization")
        print("  • Data loading from CSV files") 
        print("  • Analysis summary generation")
        print("  • API endpoint error handling")
        print("  • File type validation")
        print("  • Minimal data processing")
    else:
        print("❌ Some core tests failed!")
        print(f"Exit code: {result.returncode}")
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())