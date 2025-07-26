import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Any
import os
from datetime import datetime


class DataCleaner:
    """
    Data cleaning class for processing WIL (Work Integrated Learning) data
    """
    
    def __init__(self):
        self.cleaning_log = []
        self.quality_report = {}
        self.original_shape = None
        self.cleaned_shape = None
        
        # Define fields that should be integer type
        self.integer_fields = [
            'ACADEMIC_YEAR', 'TERM', 'ACAD_PROG', 'COURSE_ID', 
            'OFFER_NUMBER', 'CATALOG_NUMBER', 'MASKED_ID'
        ]
        
        # Define expected values for categorical variables
        self.categorical_expectations = {
            'RESIDENCY_GROUP_DESCR': ['Local', 'International'],
            'FIRST_GENERATION_IND': ['First Generation', 'Non First Generation'],
            'ATSI_GROUP': ['Indigenous', 'Non Indigenous'],
            'SES': ['High', 'Medium', 'Low', 'Unknown'],
            'GENDER': ['M', 'F', 'U'],
            'CRSE_ATTR': ['WILC']
        }
        
        # Text fields that need cleaning
        self.text_fields = [
            'FACULTY_DESCR', 'SCHOOL_NAME', 'COURSE_NAME', 
            'TERM_DESCR', 'ACADEMIC_PROGRAM_DESCR', 'ATSI_DESC',
            'REGIONAL_REMOTE', 'ADMISSION_PATHWAY', 'COURSE_CODE'
        ]

    def log_action(self, action: str, details: str = ""):
        """Log cleaning operations"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cleaning_log.append(f"[{timestamp}] {action}: {details}")

    def read_data(self, file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        Read CSV or Excel file with proper handling
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension in ['.xlsx', '.xls']:
                # Read Excel file
                df = pd.read_excel(file_path, engine='openpyxl' if file_extension == '.xlsx' else 'xlrd')
                self.log_action("Data Reading", f"Successfully read Excel file {file_path}, shape: {df.shape}")
            elif file_extension == '.csv':
                # Read CSV file with encoding handling
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    self.log_action("Data Reading", f"Successfully read CSV file {file_path}, shape: {df.shape}")
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                        self.log_action("Data Reading", f"Read CSV file using GBK encoding {file_path}, shape: {df.shape}")
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='latin1')
                        self.log_action("Data Reading", f"Read CSV file using Latin1 encoding {file_path}, shape: {df.shape}")
            else:
                raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: .csv, .xlsx, .xls")
                
        except Exception as e:
            self.log_action("Data Reading Error", f"Failed to read file {file_path}: {str(e)}")
            raise
        
        self.original_shape = df.shape
        return df

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values and empty strings
        """
        # Convert empty strings to NaN
        df = df.replace('', np.nan)
        df = df.replace(' ', np.nan)
        
        # Record missing value statistics
        missing_stats = df.isnull().sum()
        self.quality_report['missing_values_before'] = missing_stats.to_dict()
        
        # Keep "Unknown" as a valid category, don't remove or replace
        # Other missing values remain as NaN for subsequent processing
        
        self.log_action("Missing Value Handling", f"Converted empty strings to NaN, total missing: {df.isnull().sum().sum()}")
        return df

    def convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert data types
        """
        conversion_errors = []
        
        for field in self.integer_fields:
            if field in df.columns:
                try:
                    # Handle potential null values first
                    df[field] = pd.to_numeric(df[field], errors='coerce')
                    df[field] = df[field].astype('Int64')  # Use nullable integer type
                    self.log_action("Data Type Conversion", f"{field} converted to integer type")
                except Exception as e:
                    conversion_errors.append(f"{field}: {str(e)}")
        
        # Convert other fields to string type
        for col in df.columns:
            if col not in self.integer_fields:
                df[col] = df[col].astype(str)
                df[col] = df[col].replace('nan', np.nan)  # Convert string 'nan' back to NaN
        
        if conversion_errors:
            self.log_action("Data Type Conversion Errors", "; ".join(conversion_errors))
        
        return df

    def clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean text fields
        """
        for field in self.text_fields:
            if field in df.columns:
                # Remove leading and trailing whitespace
                df[field] = df[field].astype(str).str.strip()
                # Convert 'nan' string back to NaN
                df[field] = df[field].replace('nan', np.nan)
                
        self.log_action("Text Cleaning", f"Cleaned {len([f for f in self.text_fields if f in df.columns])} text fields")
        return df

    def fill_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill missing values for business requirements
        - Numeric fields: fill with 0
        - Categorical fields: fill with "Unknown"
        """
        filled_count = 0
        
        for column in df.columns:
            if column in self.integer_fields:
                # Fill numeric fields with 0
                missing_before = df[column].isnull().sum()
                df[column] = df[column].fillna(0)
                filled_count += missing_before
                if missing_before > 0:
                    self.log_action("Missing Value Fill", f"{column}: filled {missing_before} missing values with 0")
            else:
                # Fill categorical/text fields with "Unknown"
                missing_before = df[column].isnull().sum()
                df[column] = df[column].fillna("Unknown")
                filled_count += missing_before
                if missing_before > 0:
                    self.log_action("Missing Value Fill", f"{column}: filled {missing_before} missing values with 'Unknown'")
        
        self.log_action("Missing Value Fill Complete", f"Total filled: {filled_count} missing values")
        return df

    def standardize_gender(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize gender field
        """
        if 'GENDER' in df.columns:
            # Map 'U' to represent 'Unknown', but keep as 'U'
            gender_mapping = {'U': 'U', 'M': 'M', 'F': 'F'}
            
            # Check for other values
            unique_genders = df['GENDER'].dropna().unique()
            unexpected_genders = [g for g in unique_genders if g not in gender_mapping.keys()]
            
            if unexpected_genders:
                self.log_action("Gender Field Anomaly", f"Found unexpected gender values: {unexpected_genders}")
            
            self.log_action("Gender Field Standardization", f"Gender distribution: {df['GENDER'].value_counts().to_dict()}")
        
        return df

    def validate_categorical_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate categorical variable values
        """
        validation_issues = []
        
        for field, expected_values in self.categorical_expectations.items():
            if field in df.columns:
                unique_values = df[field].dropna().unique().tolist()
                unexpected_values = [v for v in unique_values if v not in expected_values]
                
                if unexpected_values:
                    validation_issues.append(f"{field}: Found unexpected values {unexpected_values}")
                
                # Record value distribution
                value_counts = df[field].value_counts().to_dict()
                self.quality_report[f'{field}_distribution'] = value_counts
        
        if validation_issues:
            self.log_action("Categorical Variable Validation", "; ".join(validation_issues))
        else:
            self.log_action("Categorical Variable Validation", "All categorical variables meet expectations")
        
        return df

    def check_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Check and handle duplicate records
        """
        # Check for completely duplicate rows
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > 0:
            df = df.drop_duplicates()
            self.log_action("Duplicate Records", f"Removed {duplicate_rows} completely duplicate rows")
        
        # Check for same student taking same course in same term
        if all(col in df.columns for col in ['MASKED_ID', 'TERM', 'COURSE_CODE']):
            subset_duplicates = df.duplicated(subset=['MASKED_ID', 'TERM', 'COURSE_CODE']).sum()
            if subset_duplicates > 0:
                df = df.drop_duplicates(subset=['MASKED_ID', 'TERM', 'COURSE_CODE'])
                self.log_action("Business Duplicate Records", f"Removed {subset_duplicates} duplicate records for same student/term/course")
        
        return df

    def check_data_consistency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Data consistency checks
        """
        consistency_issues = []
        
        # Check FACULTY and FACULTY_DESCR correspondence
        if 'FACULTY' in df.columns and 'FACULTY_DESCR' in df.columns:
            faculty_mapping = df.groupby('FACULTY')['FACULTY_DESCR'].nunique()
            inconsistent_faculties = faculty_mapping[faculty_mapping > 1]
            if not inconsistent_faculties.empty:
                consistency_issues.append(f"FACULTY-FACULTY_DESCR mapping inconsistent: {inconsistent_faculties.to_dict()}")
        
        # Check COURSE_CODE format
        if 'COURSE_CODE' in df.columns:
            course_pattern = re.compile(r'^[A-Z]{4}\d{4}$')
            invalid_courses = df[~df['COURSE_CODE'].str.match(course_pattern, na=False)]
            if not invalid_courses.empty:
                consistency_issues.append(f"Found {len(invalid_courses)} COURSE_CODE with incorrect format")
        
        # Check if all CRSE_ATTR are "WILC"
        if 'CRSE_ATTR' in df.columns:
            non_wilc = df[df['CRSE_ATTR'] != 'WILC']['CRSE_ATTR'].value_counts()
            if not non_wilc.empty:
                consistency_issues.append(f"Found non-WILC CRSE_ATTR values: {non_wilc.to_dict()}")
        
        # Check CATALOG_NUMBER consistency with COURSE_CODE
        if 'CATALOG_NUMBER' in df.columns and 'COURSE_CODE' in df.columns:
            def extract_number_from_course_code(course_code):
                match = re.search(r'\d{4}$', str(course_code))
                return int(match.group()) if match else None
            
            df['extracted_number'] = df['COURSE_CODE'].apply(extract_number_from_course_code)
            inconsistent = df[df['CATALOG_NUMBER'] != df['extracted_number']]
            if not inconsistent.empty:
                consistency_issues.append(f"Found {len(inconsistent)} records with CATALOG_NUMBER-COURSE_CODE inconsistency")
            df = df.drop('extracted_number', axis=1)
        
        if consistency_issues:
            self.log_action("Data Consistency Check", "; ".join(consistency_issues))
        else:
            self.log_action("Data Consistency Check", "Data consistency check passed")
        
        return df

    def generate_quality_report(self, df: pd.DataFrame) -> str:
        """
        Generate data quality report
        """
        self.cleaned_shape = df.shape
        
        report = []
        report.append("=" * 60)
        report.append("DATA CLEANING QUALITY REPORT")
        report.append("=" * 60)
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Data overview
        report.append("1. DATA OVERVIEW")
        report.append("-" * 30)
        report.append(f"Original records: {self.original_shape[0]:,}")
        report.append(f"Cleaned records: {self.cleaned_shape[0]:,}")
        report.append(f"Removed records: {self.original_shape[0] - self.cleaned_shape[0]:,}")
        report.append(f"Number of fields: {self.cleaned_shape[1]}")
        report.append("")
        
        # Missing value statistics
        report.append("2. MISSING VALUE STATISTICS")
        report.append("-" * 30)
        missing_stats = df.isnull().sum()
        for col, missing_count in missing_stats.items():
            if missing_count > 0:
                missing_pct = (missing_count / len(df)) * 100
                report.append(f"{col}: {missing_count:,} ({missing_pct:.2f}%)")
        report.append("")
        
        # Categorical variable distribution
        report.append("3. CATEGORICAL VARIABLE DISTRIBUTION")
        report.append("-" * 30)
        for field in self.categorical_expectations.keys():
            if field in df.columns and f'{field}_distribution' in self.quality_report:
                report.append(f"\n{field}:")
                for value, count in self.quality_report[f'{field}_distribution'].items():
                    pct = (count / len(df)) * 100
                    report.append(f"  {value}: {count:,} ({pct:.2f}%)")
        report.append("")
        
        # Data cleaning operation log
        report.append("4. DATA CLEANING OPERATION LOG")
        report.append("-" * 30)
        for log_entry in self.cleaning_log:
            report.append(log_entry)
        report.append("")
        
        return "\n".join(report)

    def save_cleaned_data(self, df: pd.DataFrame, output_dir: str = ".", year: str = None, batch_id: str = None) -> Tuple[str, str]:
        """
        Save cleaned data and report
        """
        if year is None:
            year = str(df['ACADEMIC_YEAR'].iloc[0]) if 'ACADEMIC_YEAR' in df.columns else "unknown"
        
        # Generate batch identifier if not provided
        if batch_id is None:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save cleaned data
        cleaned_file = os.path.join(output_dir, f"WIL_{year}_cleaned.csv")
        df.to_csv(cleaned_file, index=False, encoding='utf-8')
        
        # Save data quality report with year/batch info
        report_content = self.generate_quality_report(df)
        report_filename = f"data_cleaning_report_{year}_{batch_id}.txt"
        report_file = os.path.join(output_dir, report_filename)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.log_action("Data Saving", f"Cleaned data saved to: {cleaned_file}")
        self.log_action("Report Saving", f"Quality report saved to: {report_file}")
        
        return cleaned_file, report_file

    def clean_data(self, file_path: str, output_dir: str = ".", fill_missing: bool = False, batch_id: str = None) -> Tuple[pd.DataFrame, str, str]:
        """
        Complete data cleaning pipeline
        
        Args:
            file_path: Input CSV file path
            output_dir: Output directory
            fill_missing: Whether to fill missing values for business use
            batch_id: Custom batch identifier for output files
        """
        # 1. Read data
        df = self.read_data(file_path)
        
        # 2. Handle missing values
        df = self.handle_missing_values(df)
        
        # 3. Convert data types
        df = self.convert_data_types(df)
        
        # 4. Clean text fields
        df = self.clean_text_fields(df)
        
        # 5. Fill missing values if requested
        if fill_missing:
            df = self.fill_missing_values(df)
        
        # 6. Standardize gender field
        df = self.standardize_gender(df)
        
        # 7. Validate categorical variables
        df = self.validate_categorical_variables(df)
        
        # 8. Check duplicate records
        df = self.check_duplicates(df)
        
        # 9. Data consistency checks
        df = self.check_data_consistency(df)
        
        # 10. Save data and report
        cleaned_file, report_file = self.save_cleaned_data(df, output_dir, batch_id=batch_id)
        
        return df, cleaned_file, report_file


def clean_wil_data(input_file: str, output_dir: str = ".", fill_missing: bool = False, batch_id: str = None) -> Tuple[pd.DataFrame, str, str]:
    """
    Convenience function to clean WIL data
    
    Args:
        input_file: Input CSV file path
        output_dir: Output directory
        fill_missing: Whether to fill missing values for business use
        batch_id: Custom batch identifier for output files
    
    Returns:
        tuple: (cleaned DataFrame, cleaned data file path, quality report file path)
    """
    cleaner = DataCleaner()
    return cleaner.clean_data(input_file, output_dir, fill_missing, batch_id)


def clean_multiple_wil_data(input_files: List[str], output_dir: str = ".", fill_missing: bool = False, batch_id: str = None) -> List[Dict]:
    """
    Clean multiple WIL data files in batch
    
    Args:
        input_files: List of input file paths
        output_dir: Output directory
        fill_missing: Whether to fill missing values for business use
        batch_id: Custom batch identifier for output files
    
    Returns:
        list: List of dictionaries containing results for each file
        Each dictionary contains:
        - original_file: Original file path
        - status: 'success' or 'failed'
        - cleaned_df: Cleaned DataFrame (if successful)
        - cleaned_file: Path to cleaned file (if successful)
        - report_file: Path to quality report (if successful)
        - error: Error message (if failed)
    """
    if batch_id is None:
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    results = []
    
    for input_file in input_files:
        result = {
            'original_file': input_file,
            'status': 'failed',
            'cleaned_df': None,
            'cleaned_file': None,
            'report_file': None,
            'error': None
        }
        
        try:
            # Create a new cleaner instance for each file to avoid state contamination
            cleaner = DataCleaner()
            
            # Add file identifier to batch_id for unique output files
            file_basename = os.path.splitext(os.path.basename(input_file))[0]
            file_batch_id = f"{batch_id}_{file_basename}"
            
            # Clean the data
            cleaned_df, cleaned_file, report_file = cleaner.clean_data(
                input_file, output_dir, fill_missing, file_batch_id
            )
            
            result['status'] = 'success'
            result['cleaned_df'] = cleaned_df
            result['cleaned_file'] = cleaned_file
            result['report_file'] = report_file
            
        except Exception as e:
            result['error'] = str(e)
        
        results.append(result)
    
    return results