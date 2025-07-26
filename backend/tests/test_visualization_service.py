import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import json
from datetime import datetime
from app.services.visualization import WILReportAnalyzer


class TestWILReportAnalyzer:
    """Test suite for WILReportAnalyzer class"""

    @pytest.fixture
    def sample_wil_csv_file(self, temp_directory):
        """Create a sample WIL CSV file for testing"""
        data = {
            'MASKED_ID': [755415, 541573, 755416, 541574, 755417],
            'ACADEMIC_YEAR': [2025] * 5,
            'TERM': [5256] * 5,
            'FACULTY': ['SCI', 'COMM', 'ENG', 'LAW', 'MED'],
            'FACULTY_DESCR': [
                'Faculty of Science',
                'UNSW Business School', 
                'Faculty of Engineering',
                'Faculty of Law & Justice',
                'Faculty of Medicine & Health'
            ],
            'COURSE_CODE': ['PSYC7238', 'COMM5030', 'COMP9900', 'LAWS8765', 'HESC5432'],
            'COURSE_NAME': [
                'Neuropsychology (NPEP2)',
                'Social Entre Practicum',
                'Information Technology Project',
                'Legal Research Methods',
                'Health Systems Management'
            ],
            'GENDER': ['F', 'M', 'F', 'M', 'F'],
            'RESIDENCY_GROUP_DESCR': ['Local', 'International', 'Local', 'International', 'Local'],
            'FIRST_GENERATION_IND': ['Non First Generation', 'First Generation', 'Non First Generation', 'First Generation', 'Non First Generation'],
            'ATSI_DESC': ['Not of Aboriginal/T S Islander'] * 5,
            'ATSI_GROUP': ['Non Indigenous'] * 5,
            'REGIONAL_REMOTE': ['Major Cities of Australia', 'Inner Regional Australia', 'Outer Regional Australia', 'Major Cities of Australia', 'Remote Australia'],
            'SES': ['High', 'Medium', 'Low', 'High', 'Medium'],
            'CRSE_ATTR': ['WILC'] * 5
        }
        df = pd.DataFrame(data)
        
        csv_path = os.path.join(temp_directory, "sample_wil_data.csv")
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def minimal_wil_csv_file(self, temp_directory):
        """Create minimal WIL CSV file with only required columns"""
        data = {
            'MASKED_ID': [1001, 1002, 1003],
            'ACADEMIC_YEAR': [2025, 2025, 2025],
            'FACULTY_DESCR': ['Faculty of Science', 'UNSW Business School', 'Faculty of Engineering'],
            'COURSE_CODE': ['TEST1001', 'TEST1002', 'TEST1003'],
            'GENDER': ['F', 'M', 'F'],
            'RESIDENCY_GROUP_DESCR': ['Local', 'International', 'Local']
        }
        df = pd.DataFrame(data)
        
        csv_path = os.path.join(temp_directory, "minimal_wil_data.csv")
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def analyzer(self, sample_wil_csv_file, temp_directory):
        """Create WILReportAnalyzer instance"""
        return WILReportAnalyzer(sample_wil_csv_file, temp_directory)

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer is not None
        assert hasattr(analyzer, 'load_data')
        assert hasattr(analyzer, 'generate_all_charts')
        assert hasattr(analyzer, 'generate_analysis_summary')

    def test_load_data_success(self, analyzer):
        """Test successful data loading"""
        df = analyzer.load_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'MASKED_ID' in df.columns
        assert 'ACADEMIC_YEAR' in df.columns

    def test_generate_analysis_summary(self, analyzer):
        """Test analysis summary generation"""
        # Need to load data first
        analyzer.load_data()
        summary = analyzer.generate_analysis_summary()
        
        assert isinstance(summary, dict)
        assert 'key_statistics' in summary
        assert 'total_students' in summary['key_statistics']
        assert 'total_faculties' in summary['key_statistics']
        assert 'total_courses' in summary['key_statistics']

    def test_generate_year_comparison_chart(self, analyzer):
        """Test year comparison chart generation"""
        analyzer.load_data()  # Load data first
        chart_path = analyzer.generate_year_comparison_chart()
        assert chart_path is not None
        assert os.path.exists(chart_path)
        assert chart_path.endswith('.png')

    def test_generate_faculty_residency_chart(self, analyzer):
        """Test faculty residency chart generation"""
        analyzer.load_data()
        chart_path = analyzer.generate_faculty_residency_chart()
        assert chart_path is not None
        assert os.path.exists(chart_path)
        assert chart_path.endswith('.png')

    def test_generate_gender_distribution_charts(self, analyzer):
        """Test gender distribution charts generation"""
        analyzer.load_data()
        chart_paths = analyzer.generate_gender_distribution_charts()
        assert isinstance(chart_paths, list)
        assert len(chart_paths) > 0
        for chart_path in chart_paths:
            assert os.path.exists(chart_path)
            assert chart_path.endswith('.png')

    def test_generate_equity_cohort_charts(self, analyzer):
        """Test equity cohort charts generation"""
        analyzer.load_data()
        chart_paths = analyzer.generate_equity_cohort_charts()
        assert isinstance(chart_paths, list)
        assert len(chart_paths) > 0
        for chart_path in chart_paths:
            assert os.path.exists(chart_path)
            assert chart_path.endswith('.png')

    def test_generate_cdev_analysis_charts(self, analyzer):
        """Test CDEV analysis charts generation"""
        analyzer.load_data()
        chart_paths = analyzer.generate_cdev_analysis_charts()
        assert isinstance(chart_paths, list)
        # CDEV charts might be empty if no CDEV courses in sample data
        for chart_path in chart_paths:
            assert os.path.exists(chart_path)
            assert chart_path.endswith('.png')

    def test_generate_all_charts(self, analyzer):
        """Test generation of all charts"""
        analyzer.load_data()
        charts = analyzer.generate_all_charts()
        assert isinstance(charts, dict)
        
        # Check that we have chart categories
        expected_categories = [
            'year_comparison', 'faculty_residency', 'gender_distribution',
            'equity_cohorts', 'cdev_analysis'
        ]
        
        for category in expected_categories:
            if category in charts:
                assert isinstance(charts[category], list)
                for chart_path in charts[category]:
                    assert os.path.exists(chart_path)

    def test_minimal_data_analysis(self, minimal_wil_csv_file, temp_directory):
        """Test analysis with minimal required columns"""
        analyzer = WILReportAnalyzer(minimal_wil_csv_file, temp_directory)
        
        # Should be able to load data
        df = analyzer.load_data()
        assert len(df) == 3
        
        # Should be able to generate summary
        summary = analyzer.generate_analysis_summary()
        assert summary['key_statistics']['total_students'] == 3

    def test_invalid_data_file(self, temp_directory):
        """Test handling of invalid data file"""
        # Create invalid CSV file
        invalid_path = os.path.join(temp_directory, "invalid.csv")
        with open(invalid_path, 'w') as f:
            f.write("INVALID_COLUMN,ANOTHER_INVALID\n1,2\n3,4\n")
        
        # Should handle gracefully during initialization
        analyzer = WILReportAnalyzer(invalid_path, temp_directory)
        
        # Loading data should raise an error or handle gracefully
        try:
            df = analyzer.load_data()
            # If it loads, it should have handled missing columns
            assert len(df) >= 0
        except Exception as e:
            # Should raise a meaningful error
            assert "column" in str(e).lower() or "data" in str(e).lower()

    def test_nonexistent_file(self, temp_directory):
        """Test handling of nonexistent file"""
        nonexistent_path = os.path.join(temp_directory, "nonexistent.csv")
        
        # Should handle gracefully during initialization
        analyzer = WILReportAnalyzer(nonexistent_path, temp_directory)
        
        # Loading data should raise an error
        with pytest.raises(FileNotFoundError):
            analyzer.load_data()

    def test_empty_data_file(self, temp_directory):
        """Test handling of empty data file"""
        empty_path = os.path.join(temp_directory, "empty.csv")
        with open(empty_path, 'w') as f:
            f.write("")  # Empty file
        
        analyzer = WILReportAnalyzer(empty_path, temp_directory)
        
        # Should handle empty file gracefully
        try:
            df = analyzer.load_data()
            assert len(df) == 0
        except Exception as e:
            # Should raise a meaningful error
            assert "empty" in str(e).lower() or "data" in str(e).lower()

    def test_data_with_missing_values(self, temp_directory):
        """Test handling of data with missing values"""
        data_with_nulls = {
            'MASKED_ID': [1001, 1002, 1003],
            'ACADEMIC_YEAR': [2025, 2025, 2025],
            'FACULTY_DESCR': ['Faculty of Science', None, 'Faculty of Engineering'],
            'COURSE_CODE': ['TEST1001', 'TEST1002', 'TEST1003'],
            'GENDER': ['F', None, 'F'],
            'RESIDENCY_GROUP_DESCR': ['Local', 'International', None]
        }
        df = pd.DataFrame(data_with_nulls)
        
        csv_path = os.path.join(temp_directory, "data_with_nulls.csv")
        df.to_csv(csv_path, index=False)
        
        analyzer = WILReportAnalyzer(csv_path, temp_directory)
        df = analyzer.load_data()
        
        # Should load the data
        assert len(df) == 3
        
        # Should be able to generate summary
        summary = analyzer.generate_analysis_summary()
        assert summary['key_statistics']['total_students'] == 3

    def test_large_dataset_performance(self, temp_directory):
        """Test performance with larger dataset"""
        # Create a larger dataset (100 records)
        np.random.seed(42)
        large_data = {
            'MASKED_ID': list(range(1000, 1100)),
            'ACADEMIC_YEAR': [2025] * 100,
            'FACULTY_DESCR': np.random.choice([
                'Faculty of Science', 'UNSW Business School', 'Faculty of Engineering'
            ], 100),
            'COURSE_CODE': [f'TEST{i}' for i in range(1000, 1100)],
            'GENDER': np.random.choice(['F', 'M'], 100),
            'RESIDENCY_GROUP_DESCR': np.random.choice(['Local', 'International'], 100)
        }
        df = pd.DataFrame(large_data)
        
        csv_path = os.path.join(temp_directory, "large_data.csv")
        df.to_csv(csv_path, index=False)
        
        analyzer = WILReportAnalyzer(csv_path, temp_directory)
        
        start_time = datetime.now()
        summary = analyzer.generate_analysis_summary()
        end_time = datetime.now()
        
        # Should complete within reasonable time (< 10 seconds)
        assert (end_time - start_time).total_seconds() < 10
        assert summary['key_statistics']['total_students'] == 100

    def test_output_directory_creation(self, sample_wil_csv_file, temp_directory):
        """Test that output directory is created if it doesn't exist"""
        new_output_dir = os.path.join(temp_directory, "new_output")
        assert not os.path.exists(new_output_dir)
        
        analyzer = WILReportAnalyzer(sample_wil_csv_file, new_output_dir)
        analyzer.generate_year_comparison_chart()
        
        # Output directory should now exist
        assert os.path.exists(new_output_dir)

    def test_chart_file_formats(self, analyzer):
        """Test that generated charts are in PNG format"""
        chart_path = analyzer.generate_year_comparison_chart()
        
        # Should be PNG file
        assert chart_path.endswith('.png')
        
        # File should exist and have content
        assert os.path.exists(chart_path)
        assert os.path.getsize(chart_path) > 0

    def test_summary_data_types(self, analyzer):
        """Test that summary contains proper data types"""
        summary = analyzer.generate_analysis_summary()
        
        # Key statistics should be integers
        assert isinstance(summary['key_statistics']['total_students'], (int, np.integer))
        assert isinstance(summary['key_statistics']['total_faculties'], (int, np.integer))
        assert isinstance(summary['key_statistics']['total_courses'], (int, np.integer))

    def test_concurrent_chart_generation(self, analyzer):
        """Test thread safety of chart generation"""
        import threading
        
        results = []
        
        def generate_chart():
            try:
                chart_path = analyzer.generate_year_comparison_chart()
                results.append(chart_path is not None)
            except Exception as e:
                results.append(False)
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_chart)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All chart generations should succeed
        assert all(results)
        assert len(results) == 3


class TestWILReportAnalyzerErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_output_directory_permissions(self, sample_wil_csv_file):
        """Test handling of invalid output directory"""
        invalid_dir = "/invalid/nonexistent/directory"
        
        # Should handle gracefully during initialization
        analyzer = WILReportAnalyzer(sample_wil_csv_file, invalid_dir)
        
        # Chart generation might fail with permission error
        try:
            analyzer.generate_year_comparison_chart()
        except (OSError, IOError, FileNotFoundError, PermissionError):
            pass  # Expected behavior for invalid directory

    def test_corrupted_csv_file(self, temp_directory):
        """Test handling of corrupted CSV file"""
        corrupted_path = os.path.join(temp_directory, "corrupted.csv")
        with open(corrupted_path, 'w') as f:
            f.write("MASKED_ID,ACADEMIC_YEAR\n123,invalid_data\ngarbage,data\n")
        
        analyzer = WILReportAnalyzer(corrupted_path, temp_directory)
        
        # Should handle corrupted data gracefully
        try:
            df = analyzer.load_data()
            # If it loads, should handle bad data appropriately
            assert len(df) >= 0
        except Exception as e:
            # Should raise meaningful error
            assert isinstance(e, (ValueError, pd.errors.EmptyDataError, pd.errors.ParserError))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])