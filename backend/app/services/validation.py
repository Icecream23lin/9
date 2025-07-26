"""
Data validation service for uploaded files
"""
import pandas as pd
import os
from typing import Dict, List, Tuple, Optional, Any
import re


class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass


class DataValidator:
    """Validates uploaded data files"""
    
    def __init__(self):
        self.required_columns = []
        self.optional_columns = []
        self.validation_rules = {}
    
    def validate_file_structure(self, file_path: str, filename: str) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Validate file structure and return file information
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Tuple of (file_info_dict, error_message)
        """
        try:
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            # Read file based on extension
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                return None, "Unsupported file format"
            
            # Basic structure validation
            if df.empty:
                return None, "File is empty"
            
            if len(df.columns) == 0:
                return None, "No columns found in file"
            
            # Check for completely empty rows
            non_empty_rows = df.dropna(how='all')
            if len(non_empty_rows) == 0:
                return None, "File contains no data rows"
            
            # Detect data types
            column_types = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                if dtype.startswith('int'):
                    column_types[col] = 'integer'
                elif dtype.startswith('float'):
                    column_types[col] = 'float'
                elif dtype == 'object':
                    # Try to determine if it's numeric or text
                    non_null_values = df[col].dropna()
                    if len(non_null_values) > 0:
                        try:
                            pd.to_numeric(non_null_values.iloc[:min(100, len(non_null_values))])
                            column_types[col] = 'numeric'
                        except:
                            column_types[col] = 'text'
                    else:
                        column_types[col] = 'text'
                else:
                    column_types[col] = 'other'
            
            # File information
            file_info = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'column_types': column_types,
                'file_size': os.path.getsize(file_path),
                'non_empty_rows': len(non_empty_rows),
                'has_headers': self._detect_headers(df)
            }
            
            return file_info, None
            
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
    
    def _detect_headers(self, df: pd.DataFrame) -> bool:
        """
        Detect if the first row contains headers
        """
        if df.empty:
            return False
        
        first_row = df.iloc[0]
        
        # Check if first row contains mostly strings while other rows contain numbers
        string_count = 0
        for value in first_row:
            if isinstance(value, str) and not str(value).replace('.', '').replace('-', '').isdigit():
                string_count += 1
        
        # If more than half of first row values are strings, likely headers
        return string_count > len(first_row) / 2
    
    def validate_data_quality(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Perform data quality validation
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Dictionary containing data quality metrics and issues
        """
        try:
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                raise FileValidationError("Unsupported file format")
            
            quality_report = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_data': {},
                'duplicate_rows': 0,
                'data_types': {},
                'warnings': [],
                'errors': []
            }
            
            # Check for missing data
            for col in df.columns:
                missing_count = df[col].isnull().sum()
                missing_percentage = (missing_count / len(df)) * 100
                quality_report['missing_data'][col] = {
                    'count': int(missing_count),
                    'percentage': round(missing_percentage, 2)
                }
                
                if missing_percentage > 50:
                    quality_report['warnings'].append(
                        f"Column '{col}' has {missing_percentage:.1f}% missing values"
                    )
            
            # Check for duplicate rows
            duplicate_count = df.duplicated().sum()
            quality_report['duplicate_rows'] = int(duplicate_count)
            
            if duplicate_count > 0:
                quality_report['warnings'].append(
                    f"Found {duplicate_count} duplicate rows"
                )
            
            # Analyze data types
            for col in df.columns:
                dtype = str(df[col].dtype)
                quality_report['data_types'][col] = dtype
            
            # Check for columns with all same values
            for col in df.columns:
                unique_values = df[col].nunique()
                if unique_values == 1:
                    quality_report['warnings'].append(
                        f"Column '{col}' has only one unique value"
                    )
            
            return quality_report
            
        except Exception as e:
            return {
                'errors': [f"Error analyzing data quality: {str(e)}"],
                'warnings': [],
                'total_rows': 0,
                'total_columns': 0,
                'missing_data': {},
                'duplicate_rows': 0,
                'data_types': {}
            }
    
    def validate_multiple_files(self, file_paths: List[str], filenames: List[str]) -> List[Dict[str, Any]]:
        """
        Validate multiple files and return validation results for each
        
        Args:
            file_paths: List of paths to uploaded files
            filenames: List of original filenames
            
        Returns:
            List of validation results for each file
        """
        results = []
        
        for file_path, filename in zip(file_paths, filenames):
            result = {
                'filename': filename,
                'valid': False,
                'file_info': None,
                'quality_report': None,
                'error': None
            }
            
            try:
                # Validate file structure
                file_info, error = self.validate_file_structure(file_path, filename)
                if error:
                    result['error'] = error
                    results.append(result)
                    continue
                
                # Validate data quality
                quality_report = self.validate_data_quality(file_path, filename)
                
                result['valid'] = True
                result['file_info'] = file_info
                result['quality_report'] = quality_report
                
            except Exception as e:
                result['error'] = str(e)
            
            results.append(result)
        
        return results

    def validate_business_rules(self, file_path: str, filename: str, rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate against business rules
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            rules: Dictionary of business rules to validate against
            
        Returns:
            Dictionary containing validation results
        """
        if rules is None:
            rules = {}
        
        try:
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                raise FileValidationError("Unsupported file format")
            
            validation_results = {
                'passed': True,
                'errors': [],
                'warnings': [],
                'rules_checked': []
            }
            
            # Check required columns
            if 'required_columns' in rules:
                missing_columns = []
                for col in rules['required_columns']:
                    if col not in df.columns:
                        missing_columns.append(col)
                
                if missing_columns:
                    validation_results['passed'] = False
                    validation_results['errors'].append(
                        f"Missing required columns: {', '.join(missing_columns)}"
                    )
                
                validation_results['rules_checked'].append('required_columns')
            
            # Check minimum row count
            if 'min_rows' in rules:
                min_rows = rules['min_rows']
                if len(df) < min_rows:
                    validation_results['passed'] = False
                    validation_results['errors'].append(
                        f"File must have at least {min_rows} rows, but has {len(df)}"
                    )
                
                validation_results['rules_checked'].append('min_rows')
            
            # Check column data types
            if 'column_types' in rules:
                for col, expected_type in rules['column_types'].items():
                    if col in df.columns:
                        actual_type = str(df[col].dtype)
                        if expected_type == 'numeric' and not actual_type.startswith(('int', 'float')):
                            validation_results['warnings'].append(
                                f"Column '{col}' expected to be numeric but appears to be {actual_type}"
                            )
                
                validation_results['rules_checked'].append('column_types')
            
            return validation_results
            
        except Exception as e:
            return {
                'passed': False,
                'errors': [f"Error validating business rules: {str(e)}"],
                'warnings': [],
                'rules_checked': []
            }


def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename for security and compliance
    
    Args:
        filename: The filename to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        if char in filename:
            return False, f"Filename contains invalid character: {char}"
    
    # Check length
    if len(filename) > 255:
        return False, "Filename is too long (max 255 characters)"
    
    if len(filename) == 0:
        return False, "Filename cannot be empty"
    
    # Check for valid extension
    valid_extensions = ['.csv', '.xlsx', '.xls']
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        return False, f"Invalid file extension. Allowed: {', '.join(valid_extensions)}"
    
    return True, None


def validate_file_content(file_path, filename):
    """
    Legacy function for backward compatibility
    Validate file content and return basic info
    """
    validator = DataValidator()
    return validator.validate_file_structure(file_path, filename)