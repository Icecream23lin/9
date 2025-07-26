#!/usr/bin/env python3
"""
Test runner script for WIL data analysis and visualization functionality

Usage:
    python run_visualization_tests.py              # Run all tests
    python run_visualization_tests.py --unit       # Run only unit tests
    python run_visualization_tests.py --api        # Run only API tests
    python run_visualization_tests.py --fast       # Run tests excluding slow ones
    python run_visualization_tests.py --coverage   # Run with coverage report
"""

import sys
import os
import subprocess
import argparse


def run_tests(test_type=None, coverage=False, verbose=True):
    """
    Run visualization tests with specified configuration
    
    Args:
        test_type: Type of tests to run ('unit', 'api', 'integration', 'all')
        coverage: Whether to generate coverage report
        verbose: Whether to use verbose output
    """
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test files based on type
    if test_type == 'unit':
        cmd.append('tests/test_visualization_service.py')
    elif test_type == 'api' or test_type == 'integration':
        cmd.append('tests/test_visualization_api.py')
    elif test_type == 'fast':
        cmd.extend(['tests/', '-m', 'not slow'])
    else:  # all tests
        cmd.extend(['tests/test_visualization_api.py', 'tests/test_visualization_service.py'])
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            '--cov=app.services.visualization',
            '--cov=app.api.visualization', 
            '--cov-report=html',
            '--cov-report=term-missing'
        ])
    
    # Add verbose flag
    if verbose:
        cmd.append('-v')
    
    # Add colored output
    cmd.append('--color=yes')
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 80)
    
    return subprocess.run(cmd)


def check_dependencies():
    """Check if required test dependencies are installed"""
    required_packages = ['pytest', 'pandas', 'matplotlib', 'seaborn']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + ' '.join(missing_packages))
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Run WIL visualization tests')
    parser.add_argument('--unit', action='store_true', 
                       help='Run only unit tests (service layer)')
    parser.add_argument('--api', action='store_true',
                       help='Run only API integration tests')
    parser.add_argument('--fast', action='store_true',
                       help='Run tests excluding slow performance tests')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Determine test type
    test_type = 'all'
    if args.unit:
        test_type = 'unit'
    elif args.api:
        test_type = 'api'
    elif args.fast:
        test_type = 'fast'
    
    print("WIL Data Analysis and Visualization Test Suite")
    print("=" * 50)
    print(f"Test type: {test_type}")
    print(f"Coverage: {'enabled' if args.coverage else 'disabled'}")
    print(f"Verbose: {'disabled' if args.quiet else 'enabled'}")
    print()
    
    # Run tests
    result = run_tests(
        test_type=test_type,
        coverage=args.coverage,
        verbose=not args.quiet
    )
    
    print("-" * 80)
    if result.returncode == 0:
        print("✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print("❌ Some tests failed!")
        print(f"Exit code: {result.returncode}")
    
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()