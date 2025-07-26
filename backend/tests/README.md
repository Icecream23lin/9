# WIL Data Analysis and Visualization Test Suite

This directory contains comprehensive tests for the WIL (Work Integrated Learning) data analysis and visualization functionality.

## 📁 Test Structure

```
tests/
├── conftest.py                     # Pytest configuration and shared fixtures
├── pytest.ini                     # Pytest settings
├── test_visualization_api.py       # API endpoint integration tests
├── test_visualization_service.py   # Service layer unit tests
├── test_data/
│   └── sample_wil_data.csv        # Sample test data
└── README.md                      # This file
```

## 🧪 Test Categories

### 1. API Integration Tests (`test_visualization_api.py`)
Tests the REST API endpoints for data analysis and visualization:

- **Endpoint Testing**: All 4 main visualization endpoints
- **File Upload**: CSV, Excel file handling
- **Error Handling**: Invalid files, missing parameters
- **Response Validation**: JSON structure, ZIP file contents
- **Performance**: Large file processing, concurrent requests
- **Edge Cases**: Empty files, corrupted data, special characters

**Key Test Classes:**
- `TestVisualizationAPI`: Main API functionality tests
- `TestVisualizationErrorHandling`: Error scenarios and edge cases

### 2. Service Layer Unit Tests (`test_visualization_service.py`)
Tests the core `WILReportAnalyzer` class functionality:

- **Data Validation**: Required columns, data quality checks
- **Statistical Analysis**: Demographic calculations, summary statistics
- **Chart Generation**: All 10 chart types with file validation
- **Data Processing**: Missing data handling, data type consistency
- **Performance**: Large dataset processing, memory efficiency
- **Concurrency**: Thread safety testing

**Key Test Classes:**
- `TestWILReportAnalyzer`: Core analyzer functionality
- `TestWILReportAnalyzerErrorHandling`: Error scenarios and robustness

## 🚀 Running Tests

### Prerequisites
```bash
pip install pytest pandas matplotlib seaborn openpyxl psutil
```

### Quick Start
```bash
# Run all tests
python run_visualization_tests.py

# Run only unit tests (fast)
python run_visualization_tests.py --unit

# Run only API tests
python run_visualization_tests.py --api

# Run fast tests (exclude performance tests)
python run_visualization_tests.py --fast

# Run with coverage report
python run_visualization_tests.py --coverage
```

### Using Pytest Directly
```bash
# All tests with verbose output
pytest tests/ -v

# Only unit tests
pytest tests/test_visualization_service.py -v

# Only API tests
pytest tests/test_visualization_api.py -v

# Exclude slow tests
pytest tests/ -m "not slow" -v

# Run specific test
pytest tests/test_visualization_api.py::TestVisualizationAPI::test_analyze_endpoint_success -v
```

## 📊 Test Coverage

The test suite provides comprehensive coverage of:

- ✅ **API Endpoints** (4/4): All visualization endpoints tested
- ✅ **Chart Generation** (10/10): All chart types validated
- ✅ **Error Handling**: Invalid inputs, missing data, file corruption
- ✅ **Data Validation**: Required columns, data quality checks
- ✅ **Performance**: Large datasets, memory efficiency, concurrency
- ✅ **File Formats**: CSV, Excel (XLSX, XLS) support
- ✅ **Edge Cases**: Empty files, single records, unicode characters

### Coverage Report
Run with coverage to get detailed metrics:
```bash
python run_visualization_tests.py --coverage
# View report: open htmlcov/index.html
```

## 📋 Test Data

### Sample Data (`test_data/sample_wil_data.csv`)
- 20 sample WIL records
- Covers all major faculties and demographics
- Includes edge cases (missing values, special characters)
- Used for comprehensive integration testing

### Generated Test Data
Tests automatically generate various datasets:
- **Minimal Data**: 2-3 records for edge case testing
- **Large Data**: 1000+ records for performance testing
- **Invalid Data**: Missing columns, corrupted values
- **Unicode Data**: Special characters and encoding tests

## 🔧 Test Configuration

### Pytest Markers
Tests are marked for selective execution:
- `@pytest.mark.unit`: Service layer tests
- `@pytest.mark.integration`: API endpoint tests
- `@pytest.mark.slow`: Performance/large dataset tests

### Fixtures
Shared test fixtures provide:
- **Test App**: Flask application instance
- **Test Client**: HTTP client for API testing
- **Sample Data**: Various test datasets
- **Temp Directory**: Cleanup of test files
- **Matplotlib Cleanup**: Memory management

## 🚨 Troubleshooting

### Common Issues

1. **ImportError: No module named 'app'**
   ```bash
   # Run from backend directory
   cd backend
   python run_visualization_tests.py
   ```

2. **matplotlib backend issues**
   ```bash
   # Set environment variable
   export MPLBACKEND=Agg
   python run_visualization_tests.py
   ```

3. **Memory errors with large tests**
   ```bash
   # Run without performance tests
   python run_visualization_tests.py --fast
   ```

4. **File permission errors**
   ```bash
   # Ensure upload directory is writable
   chmod 755 uploads/
   ```

### Debug Mode
For detailed debugging:
```bash
pytest tests/ -v -s --tb=long
```

## 📈 Performance Benchmarks

Expected performance metrics on standard hardware:

| Test Category | Duration | Memory Usage |
|--------------|----------|--------------|
| Unit Tests | < 30s | < 50MB |
| API Tests | < 60s | < 100MB |
| Performance Tests | < 120s | < 200MB |
| Full Suite | < 180s | < 300MB |

## 🤝 Contributing

When adding new tests:

1. **Follow naming convention**: `test_feature_scenario`
2. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.slow`
3. **Clean up resources**: Use fixtures for temp files
4. **Document test purpose**: Clear docstrings
5. **Test edge cases**: Invalid inputs, boundary conditions

### Test Checklist
- [ ] Test passes individually
- [ ] Test passes with full suite
- [ ] Proper cleanup of resources
- [ ] Appropriate markers applied
- [ ] Clear documentation

## 📝 Test Results

Tests validate:
- ✅ Data analysis accuracy
- ✅ Chart generation quality
- ✅ API response structure  
- ✅ Error handling robustness
- ✅ Performance characteristics
- ✅ Memory efficiency
- ✅ Concurrent operation safety

The test suite ensures the WIL data analysis system is reliable, performant, and ready for production use.