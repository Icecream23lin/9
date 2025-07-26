import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
from typing import Dict, List
import warnings
import logging

warnings.filterwarnings('ignore', category=FutureWarning)

# Set up logging
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class ChartGenerationError(Exception):
    """Custom exception for chart generation errors."""
    pass

class WILReportAnalyzer:
    """
    Comprehensive analyzer for WIL report data with professional chart generation.
    
    This class handles all aspects of WIL data analysis including:
    - Data loading and preprocessing with validation
    - Statistical calculations
    - Chart generation with professional styling
    - Summary statistics export
    - Error handling and logging
    """
    
    # Required columns for WIL data analysis
    REQUIRED_COLUMNS = [
        'MASKED_ID', 'ACADEMIC_YEAR', 'FACULTY_DESCR', 'COURSE_CODE', 
        'GENDER', 'RESIDENCY_GROUP_DESCR'
    ]
    
    # Optional columns that enhance analysis if present
    OPTIONAL_COLUMNS = [
        'FIRST_GENERATION_IND', 'ATSI_GROUP', 'REGIONAL_REMOTE', 
        'SES', 'TERM', 'COURSE_NAME'
    ]
    
    def __init__(self, data_path: str, output_dir: str = "reports"):
        """
        Initialize the WIL Report Analyzer.
        
        Args:
            data_path: Path to the data file (CSV, XLSX, or XLS)
            output_dir: Directory to save generated charts and reports
            
        Raises:
            ValueError: If data_path is invalid or output_dir cannot be created
        """
        if not os.path.exists(data_path):
            raise ValueError(f"Data file not found: {data_path}")
            
        self.data_path = data_path
        self.output_dir = output_dir
        self.data = None
        self.date_str = datetime.now().strftime("%Y%m%d")
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create output directory {output_dir}: {str(e)}")
        
        # Set professional chart styling
        self._setup_chart_style()
        
        logger.info(f"WIL Report Analyzer initialized: {data_path} -> {output_dir}")
        
    def _setup_chart_style(self):
        """Setup professional chart styling for all visualizations."""
        plt.style.use('default')
        
        # Set global parameters for professional appearance
        plt.rcParams.update({
            'figure.figsize': (10, 6),
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'savefig.facecolor': 'white',
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.grid': True,
            'grid.alpha': 0.3,
            'grid.linewidth': 0.5,
            'font.size': 10,
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10
        })
        
        # Define professional color palettes
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'accent': '#2ca02c',
            'neutral': '#d62728',
            'blue_palette': ['#1f77b4', '#aec7e8', '#0d47a1'],
            'gender_palette': ['#1f77b4', '#ff7f0e', '#2ca02c'],
            'residency_palette': ['#1f77b4', '#ff7f0e'],
            'ses_palette': ['#1f77b4', '#4a90e2', '#87ceeb', '#d3d3d3'],
            'equity_palette': ['#d62728', '#1f77b4']
        }
    
    def load_data(self) -> pd.DataFrame:
        """
        Load and preprocess the WIL data.
        
        Returns:
            Loaded and cleaned DataFrame
        """
        try:
            # Get file extension to determine loading method
            file_extension = os.path.splitext(self.data_path)[1].lower()
            
            if file_extension == '.csv':
                self.data = pd.read_csv(self.data_path)
            elif file_extension in ['.xlsx', '.xls']:
                # Try different engines with fallback options
                try:
                    if file_extension == '.xlsx':
                        self.data = pd.read_excel(self.data_path, engine='openpyxl')
                    else:
                        self.data = pd.read_excel(self.data_path, engine='xlrd')
                except ImportError as e:
                    logger.error(f"Excel engine not available: {e}")
                    # Try alternative engine
                    try:
                        self.data = pd.read_excel(self.data_path)
                    except Exception as fallback_e:
                        raise Exception(f"Failed to read Excel file with available engines: {fallback_e}")
            else:
                raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: .csv, .xlsx, .xls")
            print(f" Data loaded successfully: {len(self.data)} records")
            
            # Minimal data preparation for visualization
            self._prepare_visualization_data()
            return self.data
            
        except Exception as e:
            raise Exception(f"Failed to load data from {self.data_path}: {str(e)}")
    
    def _prepare_visualization_data(self):
        """Prepare data for visualization (assumes data is already cleaned)."""
        # Ensure RESIDENCY_STATUS column exists for visualization
        if 'RESIDENCY_STATUS' not in self.data.columns and 'RESIDENCY_GROUP_DESCR' in self.data.columns:
            self.data['RESIDENCY_STATUS'] = self.data['RESIDENCY_GROUP_DESCR']
        
        # Ensure IS_CDEV column exists for CDEV analysis
        if 'IS_CDEV' not in self.data.columns and 'COURSE_CODE' in self.data.columns:
            self.data['IS_CDEV'] = self.data['COURSE_CODE'].str.contains('CDEV', na=False)
        
        print(f" Data preprocessing completed")
    
    def generate_year_comparison_chart(self):
        """
        Generate Year-on-Year Enrollment Comparison by Faculty.
        
        Compares enrollment data across faculties for available years using horizontal grouped bar chart.
        Shows specific enrollment numbers on bars and sorts by most recent year enrollment (descending).
        """
        try:
            # Check if we have data for multiple years
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            print(f"  Available years in data: {available_years}")
            
            if len(available_years) < 2:
                # Fallback to single year display
                return self._generate_single_year_chart()
            
            # Use the two most recent years for comparison
            year_1 = available_years[-2]  # Previous year
            year_2 = available_years[-1]  # Most recent year
            
            # Filter data for the two years
            data_year_1 = self.data[self.data['ACADEMIC_YEAR'] == year_1]
            data_year_2 = self.data[self.data['ACADEMIC_YEAR'] == year_2]
            
            if len(data_year_1) == 0 or len(data_year_2) == 0:
                print(f"  Missing data for {year_1} or {year_2}, falling back to single year chart")
                return self._generate_single_year_chart()
            
            # Calculate enrollment by faculty for each year
            enrollment_year_1 = data_year_1.groupby('FACULTY_DESCR')['MASKED_ID'].nunique()
            enrollment_year_2 = data_year_2.groupby('FACULTY_DESCR')['MASKED_ID'].nunique()
            
            # Get all faculties and fill missing values with 0
            all_faculties = sorted(set(enrollment_year_1.index) | set(enrollment_year_2.index))
            enrollment_year_1 = enrollment_year_1.reindex(all_faculties, fill_value=0)
            enrollment_year_2 = enrollment_year_2.reindex(all_faculties, fill_value=0)
            
            # Sort by most recent year enrollment (descending)
            sort_order = enrollment_year_2.sort_values(ascending=False).index
            enrollment_year_1 = enrollment_year_1.reindex(sort_order)
            enrollment_year_2 = enrollment_year_2.reindex(sort_order)
            
            # Create horizontal grouped bar chart
            fig, ax = plt.subplots(figsize=(14, 10))
            
            y_pos = np.arange(len(all_faculties))
            bar_height = 0.35
            
            # Create bars
            bars_year_1 = ax.barh(y_pos - bar_height/2, enrollment_year_1.values, 
                                 bar_height, label=str(year_1), color=self.colors['secondary'], alpha=0.8)
            bars_year_2 = ax.barh(y_pos + bar_height/2, enrollment_year_2.values, 
                                 bar_height, label=str(year_2), color=self.colors['primary'], alpha=0.8)
            
            # Add value labels on bars
            def add_value_labels(bars, values):
                for bar, value in zip(bars, values):
                    if value > 0:
                        width = bar.get_width()
                        ax.text(width + max(max(enrollment_year_1), max(enrollment_year_2)) * 0.01, 
                               bar.get_y() + bar.get_height()/2,
                               f'{int(value)}', ha='left', va='center', fontweight='bold', fontsize=10)
            
            add_value_labels(bars_year_1, enrollment_year_1.values)
            add_value_labels(bars_year_2, enrollment_year_2.values)
            
            # Customize chart
            ax.set_xlabel('Number of Students', fontsize=12, fontweight='bold')
            ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
            ax.set_title(f'Year-on-Year Enrollment Comparison by Faculty\n({year_1} vs {year_2})', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(sort_order, fontsize=10)
            ax.legend(loc='lower right', fontsize=11)
            
            # Add grid for better readability
            ax.grid(True, axis='x', alpha=0.3, linewidth=0.5)
            ax.set_axisbelow(True)
            
            plt.tight_layout()
            
            # Save chart
            filename = f"year_comparison_{self.date_str}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Print key findings
            total_year_1 = enrollment_year_1.sum()
            total_year_2 = enrollment_year_2.sum()
            growth = total_year_2 - total_year_1
            growth_pct = (growth / total_year_1 * 100) if total_year_1 > 0 else 0
            top_faculty = sort_order[0]
            print(f" Year Comparison Chart generated: {filename}")
            print(f"  Key findings: {year_1}: {total_year_1}, {year_2}: {total_year_2}, Growth: {growth} ({growth_pct:+.1f}%)")
            print(f"  Top faculty in {year_2}: {top_faculty} ({enrollment_year_2.iloc[0]} students)")
            
            return filepath
            
        except Exception as e:
            print(f" Failed to generate year comparison chart: {str(e)}")
            return self._generate_single_year_chart()
    
    def _generate_single_year_chart(self):
        """
        Fallback method to generate single year chart when year comparison data is not available.
        """
        try:
            # Calculate enrollment by faculty for available year
            faculty_enrollment = self.data.groupby('FACULTY_DESCR')['MASKED_ID'].nunique().sort_values(ascending=False)
            year = self.data['ACADEMIC_YEAR'].iloc[0] if 'ACADEMIC_YEAR' in self.data.columns else "Current Year"
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.barh(faculty_enrollment.index, faculty_enrollment.values, 
                          color=self.colors['primary'], alpha=0.8)
            
            # Add value labels on bars
            for bar in bars:
                width = bar.get_width()
                ax.text(width + max(faculty_enrollment) * 0.01, bar.get_y() + bar.get_height()/2,
                       f'{int(width)}', ha='left', va='center', fontweight='bold')
            
            ax.set_xlabel('Number of Students', fontsize=12, fontweight='bold')
            ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
            ax.set_title(f'Faculty Enrollment - {year}\n(Year-on-Year Comparison Not Available)', 
                        fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Save chart
            filename = f"year_comparison_{self.date_str}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Print key findings
            total_students = faculty_enrollment.sum()
            top_faculty = faculty_enrollment.index[0]
            print(f" Single Year Chart generated: {filename}")
            print(f"  Key findings: Total students: {total_students}, Top faculty: {top_faculty} ({faculty_enrollment.iloc[0]} students)")
            
            return filepath
            
        except Exception as e:
            print(f" Failed to generate single year chart: {str(e)}")
            return None
    
    def generate_wil_enrollment_comparison_table(self) -> Dict:
        """
        Generate WIL Enrollments year-over-year comparison table following the reference format.
        This creates Table 1: Year Comparison with % Change without extra Term column.
        
        Returns:
            Dictionary containing table data with exact column structure required
        """
        try:
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            print(f"  Available years for enrollment table: {available_years}")
            
            if len(available_years) < 2:
                print("WARNING: Insufficient years for comparison table - need at least 2 years")
                return {}
                
            # Use the two most recent years
            year_1 = available_years[-2]  # Earlier year (e.g., 2024)
            year_2 = available_years[-1]  # Later year (e.g., 2025)
            
            # Faculty order from reference code
            faculty_order = [
                'Division of Registrar and Deputy Principal',
                'DVC (A) Board of Studies', 
                'Faculty of Arts, Design and Architecture',
                'Faculty of Engineering',
                'Faculty of Law and Justice',
                'Faculty of Medicine and Health',
                'Faculty of Science',
                'UNSW Business School'
            ]
            
            # Calculate enrollments by faculty for each year using actual data
            data_year_1 = self.data[self.data['ACADEMIC_YEAR'] == year_1]
            data_year_2 = self.data[self.data['ACADEMIC_YEAR'] == year_2]
            
            enrollment_year_1 = data_year_1.groupby('FACULTY_DESCR')['MASKED_ID'].nunique()
            enrollment_year_2 = data_year_2.groupby('FACULTY_DESCR')['MASKED_ID'].nunique()
            
            # Use actual faculties from data, but try to follow the order if possible
            all_faculties_in_data = sorted(set(enrollment_year_1.index) | set(enrollment_year_2.index))
            
            # Build comparison table with actual faculty data
            comparison_table = []
            total_year_1 = 0
            total_year_2 = 0
            
            for faculty in all_faculties_in_data:
                # Get actual counts from data
                count_1 = enrollment_year_1.get(faculty, 0)
                count_2 = enrollment_year_2.get(faculty, 0)
                
                # Calculate percentage change with proper formatting (avoiding double %)
                if count_1 > 0:
                    pct_change = ((count_2 - count_1) / count_1) * 100
                    pct_change_str = f"{pct_change:.1f}%"
                elif count_2 > 0:
                    pct_change_str = "New"
                else:
                    pct_change_str = "N/A"
                
                comparison_table.append({
                    'Faculty': faculty,  # Keep 'Faculty' as the correct column name
                    str(year_1): int(count_1),
                    str(year_2): int(count_2),
                    '% Change': pct_change_str
                })
                
                total_year_1 += count_1
                total_year_2 += count_2
            
            # Calculate grand total percentage change (avoiding double %)
            if total_year_1 > 0:
                total_pct_change = ((total_year_2 - total_year_1) / total_year_1) * 100
                total_pct_change_str = f"{total_pct_change:.1f}%"
            else:
                total_pct_change_str = "New" if total_year_2 > 0 else "N/A"
            
            # Add Grand Total row
            comparison_table.append({
                'Faculty': 'Grand Total',
                str(year_1): int(total_year_1),
                str(year_2): int(total_year_2),
                '% Change': total_pct_change_str
            })
            
            table_data = {
                'title': f'Table 1: Year Comparison with % Change',
                'headers': ['Faculty', str(year_1), str(year_2), '% Change'],
                'rows': comparison_table,
                'summary': {
                    'year_1': str(year_1),
                    'year_2': str(year_2),
                    'total_change': int(total_year_2 - total_year_1),
                    'total_change_pct': total_pct_change_str,
                    'change_description': f"Overall enrollment changed by {int(total_year_2 - total_year_1)} students ({total_pct_change_str}) from {year_1} to {year_2}"
                }
            }
            
            print(f" WIL Enrollments comparison table generated: {len(comparison_table)} rows")
            print(f"  Year {year_1}: {total_year_1} students, Year {year_2}: {total_year_2} students")
            print(f"  {table_data['summary']['change_description']}")
            return table_data
            
        except Exception as e:
            print(f" Failed to generate WIL enrollment comparison table: {str(e)}")
            return {}
    
    def generate_term_breakdown_table(self) -> Dict:
        """
        Generate detailed term breakdown table by Faculty and Term with actual data calculations.
        
        Returns:
            Dictionary containing term breakdown data with hierarchical column structure
        """
        try:
            # Check if TERM column exists
            if 'TERM' not in self.data.columns:
                print("WARNING: TERM column not found, cannot generate term breakdown table")
                return {}
                
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            print(f"  Available years for term breakdown: {available_years}")
            
            if len(available_years) < 2:
                print("WARNING: Insufficient years for term breakdown table")
                return {}
                
            year_1 = available_years[-2]  # e.g., 2024
            year_2 = available_years[-1]  # e.g., 2025
            
            # Get all faculties from actual data (sorted alphabetically)
            all_faculties_in_data = sorted(self.data['FACULTY_DESCR'].unique())
            
            # Get available terms from actual data
            available_terms = sorted(self.data['TERM'].unique())
            print(f"  Available terms in data: {available_terms}")
            
            # Create term breakdown table with actual data structure
            table_rows = []
            grand_totals = {}
            
            # Initialize term columns based on actual data
            term_columns = []
            for year in [year_1, year_2]:
                for term in available_terms:
                    column_name = f'{year} {term}'
                    term_columns.append(column_name)
                    grand_totals[column_name] = 0
            
            for faculty in all_faculties_in_data:
                # Initialize row
                row = {
                    'Count of WIL Enrolments': '',
                    'Term': faculty
                }
                
                faculty_data = self.data[self.data['FACULTY_DESCR'] == faculty]
                
                # Calculate counts for each term using actual data
                for year in [year_1, year_2]:
                    year_data = faculty_data[faculty_data['ACADEMIC_YEAR'] == year]
                    
                    for term_name in available_terms:
                        term_data = year_data[year_data['TERM'] == term_name]
                        count = term_data['MASKED_ID'].nunique()
                        
                        column_name = f'{year} {term_name}'
                        row[column_name] = int(count)
                        grand_totals[column_name] += count
                
                table_rows.append(row)
            
            # Add Grand Total row
            grand_total_row = {
                'Count of WIL Enrolments': '',
                'Term': 'Grand Total'
            }
            
            for col in term_columns:
                grand_total_row[col] = grand_totals[col]
            
            table_rows.append(grand_total_row)
            
            # Create hierarchical headers structure based on actual terms
            level1_headers = ['Count of WIL Enrolments', 'Term']
            level2_headers = ['', '']
            
            for year in [year_1, year_2]:
                for _ in available_terms:
                    level1_headers.append(str(year))
                    
            for year in [year_1, year_2]:
                for term in available_terms:
                    level2_headers.append(term)
            
            # Simple headers for basic processing
            simple_headers = ['Count of WIL Enrolments', 'Term'] + term_columns
            
            table_data = {
                'title': f'Table 2: Term Breakdown ({year_1}-{year_2})',
                'headers': simple_headers,
                'hierarchical_headers': {
                    'level1': level1_headers,
                    'level2': level2_headers
                },
                'rows': table_rows,
                'summary': {
                    'total_students': sum(grand_totals.values()),
                    'total_faculties': len([r for r in table_rows if r['Term'] != 'Grand Total']),
                    'years_covered': [str(year_1), str(year_2)],
                    'terms_included': available_terms
                }
            }
            
            print(f" Term breakdown table generated: {len(table_rows)} rows")
            print(f"  Total term enrollments: {sum(grand_totals.values())}")
            return table_data
            
        except Exception as e:
            print(f" Failed to generate term breakdown table: {str(e)}")
            return {}
    
    def generate_distinct_student_count_table(self) -> Dict:
        """
        Generate Table 3: Multi-Year Student Demographics Analysis with Academic Levels comparison.
        This compares academic levels (Non-Award, Postgraduate, Undergraduate, Research) between years
        for each faculty, following the reference format.
        
        Returns:
            Dictionary containing distinct student count data with Faculty sections and academic level breakdowns
        """
        try:
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            print(f"  Available years for student count table: {available_years}")
            
            if len(available_years) < 2:
                print("WARNING: Insufficient years for student count table")
                return {}
                
            year_1 = available_years[-2]  # e.g., 2024
            year_2 = available_years[-1]  # e.g., 2025
            
            # Enhanced academic level determination based on reference format
            def determine_academic_level(course_code):
                if pd.isna(course_code):
                    return 'Undergraduate'  # Default fallback
                
                course_code = str(course_code).upper().strip()
                
                # Non-Award level (only explicit non-award courses)
                if ('NON-AWARD' in course_code or
                    any(pattern in course_code for pattern in ['0000', '00'])):
                    return 'Non-Award'
                
                # CDEV courses are typically undergraduate-level career development
                elif 'CDEV' in course_code:
                    return 'Undergraduate'
                
                # Research level (PhD, Masters by Research, etc.)
                elif (any(pattern in course_code for pattern in ['PHD', 'RESEARCH', 'RES']) or
                      # High-level research codes
                      any(code in course_code for code in ['80', '90']) and 'RES' in course_code):
                    return 'Research'
                
                # Postgraduate level (Masters, Graduate Diploma, etc.)
                elif (any(code in course_code for code in ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99']) or
                      any(pattern in course_code for pattern in ['MAST', 'GRAD', 'PG'])):
                    return 'Postgraduate'
                
                # Undergraduate level (Bachelor, Diploma, etc.) - covers 1000-8999 level
                elif (any(code in course_code for code in ['10', '20', '30', '40', '50', '60', '70', '80']) or
                      any(pattern in course_code for pattern in ['BACH', 'UG', 'DIP']) or
                      # Numeric course codes in undergraduate range
                      any(course_code.startswith(str(i)) for i in range(1000, 9000, 1000))):
                    return 'Undergraduate'
                
                # Default to Undergraduate for unknown patterns
                else:
                    return 'Undergraduate'
            
            # Add academic level to data
            data_with_level = self.data.copy()
            data_with_level['ACADEMIC_LEVEL'] = data_with_level['COURSE_CODE'].apply(determine_academic_level)
            
            # Get all faculties from actual data (sorted alphabetically)
            all_faculties_in_data = sorted(data_with_level['FACULTY_DESCR'].unique())
            
            # Define academic levels in preferred order (matching reference)
            preferred_level_order = ['Non-Award', 'Postgraduate', 'Undergraduate', 'Research']
            actual_levels = data_with_level['ACADEMIC_LEVEL'].unique()
            
            # Use preferred order, but only include levels that exist in data AND have actual students
            # First check which levels actually have student data
            levels_with_data = set()
            for level in actual_levels:
                level_data = data_with_level[data_with_level['ACADEMIC_LEVEL'] == level]
                if not level_data.empty:
                    levels_with_data.add(level)
            
            # Only include levels that have data, maintaining preferred order
            ordered_levels = [level for level in preferred_level_order if level in levels_with_data]
            # Add any additional levels not in the preferred order
            additional_levels = [level for level in levels_with_data if level not in preferred_level_order]
            ordered_levels.extend(sorted(additional_levels))
            
            print(f"  Academic levels found in data: {ordered_levels}")
            
            # Calculate distinct students by year for overall totals
            year_1_students = set(data_with_level[data_with_level['ACADEMIC_YEAR'] == year_1]['MASKED_ID'].unique())
            year_2_students = set(data_with_level[data_with_level['ACADEMIC_YEAR'] == year_2]['MASKED_ID'].unique())
            
            table_rows = []
            
            for faculty in all_faculties_in_data:
                # Add Faculty header row with total counts and percentage change
                faculty_data = data_with_level[data_with_level['FACULTY_DESCR'] == faculty]
                faculty_year_1_total = len(set(faculty_data[faculty_data['ACADEMIC_YEAR'] == year_1]['MASKED_ID'].unique()))
                faculty_year_2_total = len(set(faculty_data[faculty_data['ACADEMIC_YEAR'] == year_2]['MASKED_ID'].unique()))
                
                # Calculate faculty-level percentage change
                if faculty_year_1_total > 0:
                    faculty_pct_change = ((faculty_year_2_total - faculty_year_1_total) / faculty_year_1_total) * 100
                    faculty_pct_change_str = f"{faculty_pct_change:.1f}%"
                elif faculty_year_2_total > 0:
                    faculty_pct_change_str = "New"
                else:
                    faculty_pct_change_str = "N/A"
                
                faculty_row = {
                    'Distinct Count of WIL Students': faculty,
                    str(year_1): faculty_year_1_total,
                    str(year_2): faculty_year_2_total,
                    '% Change': faculty_pct_change_str  # Show faculty-level percentage change
                }
                table_rows.append(faculty_row)
                
                # Track faculty totals (distinct students only)
                faculty_students_year_1 = set()
                faculty_students_year_2 = set()
                
                faculty_data = data_with_level[data_with_level['FACULTY_DESCR'] == faculty]
                
                # Debug: Print faculty data info
                print(f"    Processing {faculty}: {len(faculty_data)} total records")
                if len(faculty_data) > 0:
                    faculty_levels = faculty_data['ACADEMIC_LEVEL'].unique()
                    print(f"    Academic levels in {faculty}: {faculty_levels}")
                
                # Add level rows (indented) for levels that exist in this faculty, using ordered levels
                for level in ordered_levels:
                    level_data = faculty_data[faculty_data['ACADEMIC_LEVEL'] == level]
                    
                    level_students_year_1 = set(level_data[level_data['ACADEMIC_YEAR'] == year_1]['MASKED_ID'].unique())
                    level_students_year_2 = set(level_data[level_data['ACADEMIC_YEAR'] == year_2]['MASKED_ID'].unique())
                    
                    year_1_count = len(level_students_year_1)
                    year_2_count = len(level_students_year_2)
                    
                    # Debug: Print level info
                    if year_1_count > 0 or year_2_count > 0:
                        print(f"      {level}: {year_1_count} ({year_1}) -> {year_2_count} ({year_2})")
                    
                    # Only add row if there are students in this level
                    if year_1_count > 0 or year_2_count > 0:
                        # Calculate percentage change for this level
                        if year_1_count > 0:
                            level_change = ((year_2_count - year_1_count) / year_1_count) * 100
                            level_change_str = f"{level_change:.1f}%"
                        elif year_2_count > 0:
                            level_change_str = "New"
                        else:
                            level_change_str = "N/A"
                        
                        level_row = {
                            'Distinct Count of WIL Students': f'    {level}',  # Indented academic level
                            str(year_1): int(year_1_count),
                            str(year_2): int(year_2_count),
                            '% Change': level_change_str
                        }
                        table_rows.append(level_row)
                    
                    # Add students to faculty totals (maintaining distinctness)
                    faculty_students_year_1.update(level_students_year_1)
                    faculty_students_year_2.update(level_students_year_2)
                
                # Add Faculty subtotal (distinct students only)
                faculty_total_year_1 = len(faculty_students_year_1)
                faculty_total_year_2 = len(faculty_students_year_2)
                
                if faculty_total_year_1 > 0:
                    faculty_change = ((faculty_total_year_2 - faculty_total_year_1) / faculty_total_year_1) * 100
                    faculty_change_str = f"{faculty_change:.1f}%"
                elif faculty_total_year_2 > 0:
                    faculty_change_str = "New"
                else:
                    faculty_change_str = "N/A"
                
                # Only add subtotal if there are any students
                if faculty_total_year_1 > 0 or faculty_total_year_2 > 0:
                    subtotal_row = {
                        'Distinct Count of WIL Students': '  Total',  # Just "Total", slightly indented
                        str(year_1): int(faculty_total_year_1),
                        str(year_2): int(faculty_total_year_2),
                        '% Change': faculty_change_str
                    }
                    table_rows.append(subtotal_row)
            
            # Calculate grand total percentage change (distinct students overall)
            grand_total_year_1 = len(year_1_students)
            grand_total_year_2 = len(year_2_students)
            
            if grand_total_year_1 > 0:
                grand_change = ((grand_total_year_2 - grand_total_year_1) / grand_total_year_1) * 100
                grand_change_str = f"{grand_change:.1f}%"
            else:
                grand_change_str = "New" if grand_total_year_2 > 0 else "N/A"
            
            # Add Grand Total row
            grand_total_row = {
                'Distinct Count of WIL Students': 'Grand Total',
                str(year_1): int(grand_total_year_1),
                str(year_2): int(grand_total_year_2),
                '% Change': grand_change_str
            }
            table_rows.append(grand_total_row)
            
            table_data = {
                'title': f'Table 3: Multi-Year Student Demographics Analysis ({year_1} vs {year_2})',
                'headers': ['Distinct Count of WIL Students', str(year_1), str(year_2), '% Change'],
                'rows': table_rows,
                'summary': {
                    'year_1': str(year_1),
                    'year_2': str(year_2),
                    'total_change': int(grand_total_year_2 - grand_total_year_1),
                    'total_change_pct': grand_change_str,
                    'levels_included': ordered_levels,
                    'description': f'Year-over-year comparison of Academic Levels (Postgraduate, Undergraduate, Research) between {year_1} and {year_2} for each faculty, showing distinct student counts and enrollment trends'
                }
            }
            
            print(f" Distinct student count table generated: {len(table_rows)} rows")
            print(f"  Total distinct students: {year_1}: {grand_total_year_1}, {year_2}: {grand_total_year_2}")
            return table_data
            
        except Exception as e:
            print(f" Failed to generate distinct student count table: {str(e)}")
            return {}
    
    def generate_table_visualizations(self) -> List[str]:
        """
        Generate visual chart representations of the analysis tables.
        
        Returns:
            List of file paths to generated table chart images
        """
        charts_generated = []
        
        try:
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            if len(available_years) < 2:
                print("WARNING: Need at least 2 years for table visualizations")
                return charts_generated
            
            year_1 = available_years[-2]
            year_2 = available_years[-1]
            
            # 1. Faculty Enrollment Comparison Chart (Table 1 visualization)
            try:
                data_year_1 = self.data[self.data['ACADEMIC_YEAR'] == year_1]
                data_year_2 = self.data[self.data['ACADEMIC_YEAR'] == year_2]
                
                enrollment_year_1 = data_year_1.groupby('FACULTY_DESCR')['MASKED_ID'].nunique()
                enrollment_year_2 = data_year_2.groupby('FACULTY_DESCR')['MASKED_ID'].nunique()
                
                # Combine and sort by total enrollment
                all_faculties = sorted(set(enrollment_year_1.index) | set(enrollment_year_2.index))
                enrollment_year_1 = enrollment_year_1.reindex(all_faculties, fill_value=0)
                enrollment_year_2 = enrollment_year_2.reindex(all_faculties, fill_value=0)
                
                total_enrollment = enrollment_year_1 + enrollment_year_2
                sort_order = total_enrollment.sort_values(ascending=True).index
                
                # Create horizontal grouped bar chart
                fig, ax = plt.subplots(figsize=(14, 10))
                
                y_pos = np.arange(len(all_faculties))
                bar_height = 0.35
                
                bars_year_1 = ax.barh(y_pos - bar_height/2, enrollment_year_1[sort_order].values, 
                                     bar_height, label=str(year_1), color=self.colors['secondary'], alpha=0.8)
                bars_year_2 = ax.barh(y_pos + bar_height/2, enrollment_year_2[sort_order].values, 
                                     bar_height, label=str(year_2), color=self.colors['primary'], alpha=0.8)
                
                # Add value labels
                for i, (bar1, bar2) in enumerate(zip(bars_year_1, bars_year_2)):
                    val1 = enrollment_year_1[sort_order].iloc[i]
                    val2 = enrollment_year_2[sort_order].iloc[i]
                    if val1 > 0:
                        ax.text(val1 + max(enrollment_year_1.max(), enrollment_year_2.max()) * 0.01, 
                               bar1.get_y() + bar1.get_height()/2, f'{int(val1)}', 
                               ha='left', va='center', fontweight='bold', fontsize=9)
                    if val2 > 0:
                        ax.text(val2 + max(enrollment_year_1.max(), enrollment_year_2.max()) * 0.01, 
                               bar2.get_y() + bar2.get_height()/2, f'{int(val2)}', 
                               ha='left', va='center', fontweight='bold', fontsize=9)
                
                ax.set_xlabel('Number of Students', fontsize=12, fontweight='bold')
                ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
                ax.set_title(f'Table 1 Visualization: Faculty Enrollment Comparison\n({year_1} vs {year_2})', 
                            fontsize=14, fontweight='bold', pad=20)
                ax.set_yticks(y_pos)
                ax.set_yticklabels([f.split()[-1] if len(f.split()) > 3 else f for f in sort_order], fontsize=9)
                ax.legend(loc='lower right', fontsize=11)
                ax.grid(True, axis='x', alpha=0.3)
                
                plt.tight_layout()
                
                filename = f"table1_faculty_comparison_chart_{self.date_str}.png"
                filepath = os.path.join(self.output_dir, filename)
                plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                charts_generated.append(filepath)
                print(f"  Generated Table 1 visualization: {filename}")
                
            except Exception as e:
                print(f"  Failed to generate Table 1 visualization: {str(e)}")
            
            # 2. Academic Level Distribution Chart (Table 3 visualization)
            try:
                # Determine academic levels
                def determine_academic_level(course_code):
                    if pd.isna(course_code):
                        return 'Unknown'
                    course_code = str(course_code).upper()
                    
                    if any(code in course_code for code in ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99']):
                        return 'Postgraduate'
                    elif any(code in course_code for code in ['10', '20', '30', '40', '50', '60', '70', '80']):
                        return 'Undergraduate'
                    elif 'RESEARCH' in course_code or 'PHD' in course_code:
                        return 'Research'
                    elif 'CDEV' in course_code or any(code in course_code for code in ['0000', '00']):
                        return 'Non-Award'
                    else:
                        return 'Undergraduate'
                
                data_with_level = self.data.copy()
                data_with_level['ACADEMIC_LEVEL'] = data_with_level['COURSE_CODE'].apply(determine_academic_level)
                
                # Calculate level distribution for both years
                level_year_1 = data_with_level[data_with_level['ACADEMIC_YEAR'] == year_1].groupby('ACADEMIC_LEVEL')['MASKED_ID'].nunique()
                level_year_2 = data_with_level[data_with_level['ACADEMIC_YEAR'] == year_2].groupby('ACADEMIC_LEVEL')['MASKED_ID'].nunique()
                
                # Only include levels that have actual data (non-zero values)
                all_levels_raw = sorted(set(level_year_1.index) | set(level_year_2.index))
                all_levels = [level for level in all_levels_raw if (level_year_1.get(level, 0) > 0 or level_year_2.get(level, 0) > 0)]
                level_year_1 = level_year_1.reindex(all_levels, fill_value=0)
                level_year_2 = level_year_2.reindex(all_levels, fill_value=0)
                
                # Create stacked bar chart
                fig, ax = plt.subplots(figsize=(12, 8))
                
                x_pos = np.arange(len(all_levels))
                bar_width = 0.35
                
                bars1 = ax.bar(x_pos - bar_width/2, level_year_1.values, bar_width, 
                              label=str(year_1), color=self.colors['secondary'], alpha=0.8)
                bars2 = ax.bar(x_pos + bar_width/2, level_year_2.values, bar_width, 
                              label=str(year_2), color=self.colors['primary'], alpha=0.8)
                
                # Add value labels
                for bar1, bar2, val1, val2 in zip(bars1, bars2, level_year_1.values, level_year_2.values):
                    if val1 > 0:
                        ax.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height() + max(level_year_1.max(), level_year_2.max()) * 0.01,
                               f'{int(val1)}', ha='center', va='bottom', fontweight='bold')
                    if val2 > 0:
                        ax.text(bar2.get_x() + bar2.get_width()/2, bar2.get_height() + max(level_year_1.max(), level_year_2.max()) * 0.01,
                               f'{int(val2)}', ha='center', va='bottom', fontweight='bold')
                
                ax.set_xlabel('Academic Level', fontsize=12, fontweight='bold')
                ax.set_ylabel('Number of Students', fontsize=12, fontweight='bold')
                ax.set_title(f'Table 3 Visualization: Academic Level Distribution\n({year_1} vs {year_2})', 
                            fontsize=14, fontweight='bold', pad=20)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(all_levels, rotation=45, ha='right')
                ax.legend()
                ax.grid(True, axis='y', alpha=0.3)
                
                plt.tight_layout()
                
                filename = f"table3_academic_levels_chart_{self.date_str}.png"
                filepath = os.path.join(self.output_dir, filename)
                plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                charts_generated.append(filepath)
                print(f"  Generated Table 3 visualization: {filename}")
                
            except Exception as e:
                print(f"  Failed to generate Table 3 visualization: {str(e)}")
            
            print(f" Table visualizations generated: {len(charts_generated)} charts")
            return charts_generated
            
        except Exception as e:
            print(f" Failed to generate table visualizations: {str(e)}")
            return charts_generated

    def generate_all_analysis_tables(self) -> Dict[str, Dict]:
        """
        Generate all analysis tables for year-over-year comparison.
        Only generates tables if multiple years are available.
        
        Returns:
            Dictionary containing all generated tables
        """
        print("\n" + "=" * 60)
        print("GENERATING ANALYSIS TABLES")
        print("=" * 60)
        
        # Check if we have sufficient years for comparison
        if 'ACADEMIC_YEAR' not in self.data.columns:
            print("WARNING: ACADEMIC_YEAR column not found - cannot generate comparison tables")
            return {}
        
        available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
        print(f"Available years in data: {available_years}")
        
        if len(available_years) < 2:
            print("INFO: Only one year of data available - comparison tables not generated")
            print("      Comparison tables require at least 2 years of data")
            return {}
        
        tables = {}
        
        # 1. WIL Enrollments Comparison Table
        print("\n1. Generating WIL Enrollments Comparison Table...")
        enrollment_table = self.generate_wil_enrollment_comparison_table()
        if enrollment_table:
            tables['wil_enrollment_comparison'] = enrollment_table
        
        # 2. Term Breakdown Table
        print("\n2. Generating Term Breakdown Table...")
        term_table = self.generate_term_breakdown_table()
        if term_table:
            tables['term_breakdown'] = term_table
        
        # 3. Distinct Student Count Table
        print("\n3. Generating Distinct Student Count Table...")
        student_count_table = self.generate_distinct_student_count_table()
        if student_count_table:
            tables['distinct_student_count'] = student_count_table
        
        # Save all tables to JSON with proper serialization
        if tables:
            tables_path = os.path.join(self.output_dir, f"analysis_tables_{self.date_str}.json")
            
            # Convert numpy int64 to Python int for JSON serialization
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                else:
                    return obj
            
            tables_serializable = convert_numpy_types(tables)
            
            with open(tables_path, 'w', encoding='utf-8') as f:
                json.dump(tables_serializable, f, indent=2, ensure_ascii=False)
            
            print(f"\n" + "=" * 60)
            print(f"ANALYSIS TABLES COMPLETE")
            print("=" * 60)
            print(f"Total tables generated: {len(tables)}")
            print(f"Years compared: {available_years[-2]} vs {available_years[-1]}")
            print(f"Tables saved to: analysis_tables_{self.date_str}.json")
            print(f"Output directory: {self.output_dir}")
            
            tables['_metadata'] = {
                'generation_date': datetime.now().isoformat(),
                'output_file': f"analysis_tables_{self.date_str}.json",
                'total_tables': len(tables),
                'years_compared': available_years,
                'comparison_years': [available_years[-2], available_years[-1]]
            }
        else:
            print("\n" + "=" * 60)
            print("NO TABLES GENERATED")
            print("=" * 60)
            print("All table generation failed - check data structure and requirements")
        
        return tables
    
    def generate_faculty_residency_chart(self):
        """Generate Year-on-Year Comparison by Faculty and Residency Status grouped bar chart."""
        try:
            # Check if we have data for multiple years
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            print(f"  Available years for faculty-residency comparison: {available_years}")
            
            if len(available_years) < 2:
                # Fallback to single year display
                return self._generate_single_year_faculty_residency_chart()
            
            # Use the two most recent years for comparison
            year_1 = available_years[-2]  # Previous year
            year_2 = available_years[-1]  # Most recent year
            
            # Filter data for the two years
            data_year_1 = self.data[self.data['ACADEMIC_YEAR'] == year_1]
            data_year_2 = self.data[self.data['ACADEMIC_YEAR'] == year_2]
            
            if len(data_year_1) == 0 or len(data_year_2) == 0:
                print(f"  Missing data for {year_1} or {year_2}, falling back to single year chart")
                return self._generate_single_year_faculty_residency_chart()
            
            # Calculate enrollment by faculty and residency for each year
            faculty_residency_year_1 = data_year_1.groupby(['FACULTY_DESCR', 'RESIDENCY_STATUS'])['MASKED_ID'].nunique().unstack(fill_value=0)
            faculty_residency_year_2 = data_year_2.groupby(['FACULTY_DESCR', 'RESIDENCY_STATUS'])['MASKED_ID'].nunique().unstack(fill_value=0)
            
            # Get all faculties and residency statuses
            all_faculties = sorted(set(faculty_residency_year_1.index) | set(faculty_residency_year_2.index))
            all_residency_types = sorted(set(faculty_residency_year_1.columns) | set(faculty_residency_year_2.columns))
            
            # Reindex to ensure consistent structure
            faculty_residency_year_1 = faculty_residency_year_1.reindex(index=all_faculties, columns=all_residency_types, fill_value=0)
            faculty_residency_year_2 = faculty_residency_year_2.reindex(index=all_faculties, columns=all_residency_types, fill_value=0)
            
            # Sort faculties by total enrollment in most recent year (descending)
            total_year_2 = faculty_residency_year_2.sum(axis=1)
            sort_order = total_year_2.sort_values(ascending=False).index
            faculty_residency_year_1 = faculty_residency_year_1.reindex(sort_order)
            faculty_residency_year_2 = faculty_residency_year_2.reindex(sort_order)
            
            # Create grouped bar chart with 4 bars per faculty
            fig, ax = plt.subplots(figsize=(16, 10))
            
            x_pos = np.arange(len(all_faculties))
            bar_width = 0.2
            
            # Define colors for the 4 categories
            colors = {
                f'{year_1}_International': '#ff9999',  # Light red
                f'{year_1}_Local': '#99ccff',         # Light blue  
                f'{year_2}_International': '#ff3333', # Dark red
                f'{year_2}_Local': '#3366cc'          # Dark blue
            }
            
            bars = {}
            
            # Create bars for each combination
            for i, residency in enumerate(['International', 'Local']):
                # Previous year bars
                if residency in faculty_residency_year_1.columns:
                    pos_year_1 = x_pos + (i * 2 - 1.5) * bar_width
                    bars[f'{year_1}_{residency}'] = ax.bar(
                        pos_year_1, faculty_residency_year_1[residency].values,
                        bar_width, label=f'{year_1} {residency}',
                        color=colors[f'{year_1}_{residency}'], alpha=0.8
                    )
                
                # Current year bars  
                if residency in faculty_residency_year_2.columns:
                    pos_year_2 = x_pos + (i * 2 - 0.5) * bar_width
                    bars[f'{year_2}_{residency}'] = ax.bar(
                        pos_year_2, faculty_residency_year_2[residency].values,
                        bar_width, label=f'{year_2} {residency}',
                        color=colors[f'{year_2}_{residency}'], alpha=0.8
                    )
            
            # Add value labels on bars
            for key, bar_group in bars.items():
                for bar in bar_group:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                               f'{int(height)}', ha='center', va='bottom', 
                               fontweight='bold', fontsize=8, rotation=90)
            
            # Customize chart
            ax.set_xlabel('Faculty', fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Students', fontsize=12, fontweight='bold')
            ax.set_title(f'Year-on-Year Comparison by Faculty and Residency Status\n({year_1} vs {year_2})', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(sort_order, rotation=45, ha='right', fontsize=10)
            ax.legend(loc='upper right', fontsize=10)
            
            # Add grid for better readability
            ax.grid(True, axis='y', alpha=0.3, linewidth=0.5)
            ax.set_axisbelow(True)
            
            plt.tight_layout()
            
            # Save chart
            filename = f"faculty_residency_{self.date_str}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Print key findings
            total_local = faculty_residency_year_2.get('Local', pd.Series([0])).sum()
            total_international = faculty_residency_year_2.get('International', pd.Series([0])).sum()
            print(f" Faculty-Residency Chart generated: {filename}")
            print(f"  Key findings: Local: {total_local}, International: {total_international}")
            
            return filepath
            
        except Exception as e:
            print(f" Failed to generate faculty-residency chart: {str(e)}")
            return self._generate_single_year_faculty_residency_chart()
    
    def _generate_single_year_faculty_residency_chart(self):
        """
        Fallback method to generate single year faculty-residency chart.
        """
        try:
            # Calculate enrollment by faculty and residency status
            faculty_residency = self.data.groupby(['FACULTY_DESCR', 'RESIDENCY_STATUS'])['MASKED_ID'].nunique().unstack(fill_value=0)
            
            # Create grouped bar chart
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Plot grouped bars
            bar_width = 0.35
            x_pos = np.arange(len(faculty_residency.index))
            
            bars1 = ax.bar(x_pos - bar_width/2, faculty_residency.get('Local', 0), 
                          bar_width, label='Local', color=self.colors['residency_palette'][0], alpha=0.8)
            bars2 = ax.bar(x_pos + bar_width/2, faculty_residency.get('International', 0), 
                          bar_width, label='International', color=self.colors['residency_palette'][1], alpha=0.8)
            
            # Add value labels on bars
            def add_value_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                               f'{int(height)}', ha='center', va='bottom', fontweight='bold')
            
            add_value_labels(bars1)
            add_value_labels(bars2)
            
            year = self.data['ACADEMIC_YEAR'].iloc[0] if 'ACADEMIC_YEAR' in self.data.columns else "Current Year"
            ax.set_xlabel('Faculty', fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Students', fontsize=12, fontweight='bold')
            ax.set_title(f'Student Enrollment by Faculty and Residency Status - {year}\n(Year-on-Year Comparison Not Available)', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(faculty_residency.index, rotation=45, ha='right')
            ax.legend()
            
            plt.tight_layout()
            
            # Save chart
            filename = f"faculty_residency_{self.date_str}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Print key findings
            total_local = faculty_residency.get('Local', pd.Series([0])).sum()
            total_international = faculty_residency.get('International', pd.Series([0])).sum()
            print(f" Single Year Faculty-Residency Chart generated: {filename}")
            print(f"  Key findings: Local: {total_local}, International: {total_international}")
            
            return filepath
            
        except Exception as e:
            print(f" Failed to generate single year faculty-residency chart: {str(e)}")
            return None
    
    def generate_gender_distribution_charts(self):
        """Generate Gender Distribution pie chart and stacked bar chart."""
        charts_generated = []
        
        # Check if GENDER column exists
        if 'GENDER' not in self.data.columns:
            print("WARNING:  Skipping gender distribution charts - GENDER column not found in WIL data")
            return charts_generated
        
        try:
            # 3.1 Overall Gender Distribution Pie Chart
            gender_counts = self.data['GENDER'].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = self.colors['gender_palette'][:len(gender_counts)]
            
            wedges, texts, autotexts = ax.pie(gender_counts.values, labels=gender_counts.index,
                                            autopct='%1.1f%%', colors=colors, startangle=90)
            
            # Enhance text appearance
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(12)
            
            ax.set_title('Overall Gender Distribution', fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Save pie chart
            filename1 = f"gender_distribution_pie_{self.date_str}.png"
            filepath1 = os.path.join(self.output_dir, filename1)
            plt.savefig(filepath1, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            charts_generated.append(filepath1)
            
            # 3.2 Faculty Gender Ratio Horizontal Stacked Bar Chart
            faculty_gender = self.data.groupby(['FACULTY_DESCR', 'GENDER'])['MASKED_ID'].nunique().unstack(fill_value=0)
            
            # Calculate percentages
            faculty_gender_pct = faculty_gender.div(faculty_gender.sum(axis=1), axis=0) * 100
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create stacked horizontal bar chart
            faculty_gender_pct.plot(kind='barh', stacked=True, ax=ax, 
                                  color=self.colors['gender_palette'][:len(faculty_gender_pct.columns)],
                                  alpha=0.8)
            
            ax.set_xlabel('Percentage (%)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
            ax.set_title('Gender Distribution by Faculty', fontsize=14, fontweight='bold', pad=20)
            ax.legend(title='Gender', bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Add percentage labels
            for i, faculty in enumerate(faculty_gender_pct.index):
                cumulative = 0
                for j, gender in enumerate(faculty_gender_pct.columns):
                    value = faculty_gender_pct.loc[faculty, gender]
                    if value > 5:  # Only show labels for segments > 5%
                        ax.text(cumulative + value/2, i, f'{value:.1f}%',
                               ha='center', va='center', fontweight='bold', color='white')
                    cumulative += value
            
            plt.tight_layout()
            
            # Save stacked bar chart
            filename2 = f"gender_distribution_faculty_{self.date_str}.png"
            filepath2 = os.path.join(self.output_dir, filename2)
            plt.savefig(filepath2, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            charts_generated.append(filepath2)
            
            # Print key findings
            total_students = gender_counts.sum()
            male_pct = (gender_counts.get('Male', 0) / total_students) * 100
            female_pct = (gender_counts.get('Female', 0) / total_students) * 100
            print(f" Gender Distribution Charts generated: {len(charts_generated)} files")
            print(f"  Key findings: Male: {male_pct:.1f}%, Female: {female_pct:.1f}%")
            
            return charts_generated
            
        except Exception as e:
            print(f" Failed to generate gender distribution charts: {str(e)}")
            return charts_generated
    
    def generate_equity_cohort_charts(self):
        """Generate Equity Cohort Participation analysis charts."""
        charts_generated = []
        
        # Check which equity columns are available
        available_equity_columns = []
        if 'FIRST_GENERATION_IND' in self.data.columns:
            available_equity_columns.append('FIRST_GENERATION_IND')
        if 'ATSI_GROUP' in self.data.columns:
            available_equity_columns.append('ATSI_GROUP')
        if 'SES' in self.data.columns:
            available_equity_columns.append('SES')
        if 'REGIONAL_REMOTE' in self.data.columns:
            available_equity_columns.append('REGIONAL_REMOTE')
            
        if not available_equity_columns:
            print("WARNING: No equity demographic columns available - skipping equity cohort charts")
            return charts_generated
        
        try:
            # 4.1 First Generation Student Participation Rate (only if column exists)
            if 'FIRST_GENERATION_IND' in self.data.columns:
                first_gen_data = self.data.groupby('FACULTY_DESCR')['FIRST_GENERATION_IND'].apply(
                    lambda x: (x == 'First Generation').sum() / len(x) * 100
                ).sort_values(ascending=True)
                
                fig, ax = plt.subplots(figsize=(12, 8))
                bars = ax.barh(first_gen_data.index, first_gen_data.values, 
                              color=self.colors['equity_palette'][0], alpha=0.8)
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                           f'{width:.1f}%', ha='left', va='center', fontweight='bold')
                
                ax.set_xlabel('First Generation Student Percentage (%)', fontsize=12, fontweight='bold')
                ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
                ax.set_title('First Generation Student Participation by Faculty', 
                            fontsize=14, fontweight='bold', pad=20)
                
                plt.tight_layout()
                
                filename1 = f"first_generation_participation_{self.date_str}.png"
                filepath1 = os.path.join(self.output_dir, filename1)
                plt.savefig(filepath1, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                charts_generated.append(filepath1)
                print(f" Generated first generation participation chart: {filename1}")
            else:
                print("WARNING: FIRST_GENERATION_IND column not available - skipping first generation chart")
            
            # 4.2 SES Distribution by Faculty (Stacked Horizontal Bar) - only if column exists
            if 'SES' in self.data.columns:
                ses_faculty = self.data.groupby(['FACULTY_DESCR', 'SES'])['MASKED_ID'].nunique().unstack(fill_value=0)
                ses_faculty_pct = ses_faculty.div(ses_faculty.sum(axis=1), axis=0) * 100
                
                fig, ax = plt.subplots(figsize=(12, 8))
                ses_faculty_pct.plot(kind='barh', stacked=True, ax=ax, 
                                   color=self.colors['ses_palette'][:len(ses_faculty_pct.columns)],
                                   alpha=0.8)
                
                ax.set_xlabel('Percentage (%)', fontsize=12, fontweight='bold')
                ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
                ax.set_title('Socioeconomic Status (SES) Distribution by Faculty', 
                            fontsize=14, fontweight='bold', pad=20)
                ax.legend(title='SES Level', bbox_to_anchor=(1.05, 1), loc='upper left')
                
                plt.tight_layout()
                
                filename2 = f"ses_distribution_{self.date_str}.png"
                filepath2 = os.path.join(self.output_dir, filename2)
                plt.savefig(filepath2, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                charts_generated.append(filepath2)
                print(f" Generated SES distribution chart: {filename2}")
            else:
                print("WARNING: SES column not available - skipping SES distribution chart")
            
            # 4.3 Indigenous Student Participation Rate - only if column exists
            if 'ATSI_GROUP' in self.data.columns:
                indigenous_data = self.data.groupby('FACULTY_DESCR')['ATSI_GROUP'].apply(
                    lambda x: (x != 'Non Indigenous').sum() / len(x) * 100
                ).sort_values(ascending=True)
                
                fig, ax = plt.subplots(figsize=(12, 8))
                bars = ax.barh(indigenous_data.index, indigenous_data.values, 
                              color=self.colors['accent'], alpha=0.8)
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 0.05, bar.get_y() + bar.get_height()/2,
                           f'{width:.1f}%', ha='left', va='center', fontweight='bold')
                
                ax.set_xlabel('Indigenous Student Percentage (%)', fontsize=12, fontweight='bold')
                ax.set_ylabel('Faculty', fontsize=12, fontweight='bold')
                ax.set_title('Indigenous Student Participation by Faculty', 
                            fontsize=14, fontweight='bold', pad=20)
                
                plt.tight_layout()
                
                filename3 = f"indigenous_participation_{self.date_str}.png"
                filepath3 = os.path.join(self.output_dir, filename3)
                plt.savefig(filepath3, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                charts_generated.append(filepath3)
                print(f" Generated indigenous participation chart: {filename3}")
            else:
                print("WARNING: ATSI_GROUP column not available - skipping indigenous participation chart")
            
            # 4.4 Regional Distribution Pie Chart - only if column exists
            if 'REGIONAL_REMOTE' in self.data.columns:
                regional_counts = self.data['REGIONAL_REMOTE'].value_counts()
                total_count = regional_counts.sum()
            
            # Group very small segments together to avoid overlap
            threshold_pct = 1.0  # Group segments smaller than 1%
            main_segments = {}
            small_segments = {}
            
            for region, count in regional_counts.items():
                pct = (count / total_count) * 100
                if pct >= threshold_pct:
                    main_segments[region] = count
                else:
                    small_segments[region] = count
            
            # If there are small segments, group them as "Others"
            if small_segments:
                others_count = sum(small_segments.values())
                main_segments['Others (Remote/Very Remote)'] = others_count
                display_counts = pd.Series(main_segments)
            else:
                display_counts = regional_counts
            
            # Custom autopct function
            def make_autopct(pct):
                absolute = int(pct/100. * total_count)
                if pct < 3:
                    return f'{pct:.1f}%'
                else:
                    return f'{pct:.1f}%\n({absolute:,})'
            
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Use explode to separate smaller segments
            explode = []
            colors = plt.cm.Set3(np.linspace(0, 1, len(display_counts)))
            
            for count in display_counts.values:
                pct = (count / total_count) * 100
                explode.append(0.08 if pct < 10 else 0.02)
            
            # Create pie chart with legend only (no labels on chart)
            wedges = ax.pie(
                display_counts.values, 
                labels=None,  # No labels on the pie chart
                autopct=None,  # No percentage text on the pie chart
                startangle=90,
                explode=explode,
                colors=colors,
                wedgeprops={'linewidth': 2, 'edgecolor': 'white'}
            )[0]  # Only get wedges when no labels/autopct
            
            ax.set_title('Regional Distribution of Students', fontsize=14, fontweight='bold', pad=20)
            
            # Create detailed legend showing all categories including grouped ones
            legend_labels = []
            for label, count in display_counts.items():
                pct = (count / total_count) * 100
                if label == 'Others (Remote/Very Remote)' and small_segments:
                    # Show breakdown of "Others" category
                    others_detail = ', '.join([f'{k}: {v}' for k, v in small_segments.items()])
                    legend_labels.append(f'{label}: {count:,} ({pct:.1f}%)\n   [{others_detail}]')
                else:
                    legend_labels.append(f'{label}: {count:,} ({pct:.1f}%)')
            
            ax.legend(wedges, legend_labels, title="Regional Categories", 
                     loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                     fontsize=9, title_fontsize=10)
            
            plt.tight_layout()
            
            filename4 = f"regional_distribution_{self.date_str}.png"
            filepath4 = os.path.join(self.output_dir, filename4)
            plt.savefig(filepath4, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            charts_generated.append(filepath4)
            
            print(f" Equity Cohort Charts generated: {len(charts_generated)} files")
            
            return charts_generated
            
        except Exception as e:
            print(f" Failed to generate equity cohort charts: {str(e)}")
            return charts_generated
    
    def generate_cdev_analysis_charts(self):
        """Generate CDEV course analysis charts."""
        charts_generated = []
        
        try:
            # Filter CDEV courses
            cdev_data = self.data[self.data['IS_CDEV']]
            
            if len(cdev_data) == 0:
                print("WARNING: No CDEV courses found in the data")
                return charts_generated
            
            # 5.1 CDEV Course Enrollment by Residency Status
            cdev_residency = cdev_data.groupby(['COURSE_CODE', 'RESIDENCY_STATUS'])['MASKED_ID'].nunique().unstack(fill_value=0)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            bar_width = 0.35
            x_pos = np.arange(len(cdev_residency.index))
            
            bars1 = ax.bar(x_pos - bar_width/2, cdev_residency.get('Local', 0), 
                          bar_width, label='Local', color=self.colors['residency_palette'][0], alpha=0.8)
            bars2 = ax.bar(x_pos + bar_width/2, cdev_residency.get('International', 0), 
                          bar_width, label='International', color=self.colors['residency_palette'][1], alpha=0.8)
            
            # Add value labels
            def add_value_labels(bars):
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                               f'{int(height)}', ha='center', va='bottom', fontweight='bold')
            
            add_value_labels(bars1)
            add_value_labels(bars2)
            
            ax.set_xlabel('CDEV Course Code', fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Students', fontsize=12, fontweight='bold')
            ax.set_title('CDEV Course Enrollment by Residency Status', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cdev_residency.index, rotation=45, ha='right')
            ax.legend()
            
            plt.tight_layout()
            
            filename1 = f"cdev_residency_{self.date_str}.png"
            filepath1 = os.path.join(self.output_dir, filename1)
            plt.savefig(filepath1, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            charts_generated.append(filepath1)
            
            # 5.2 CDEV Course Gender Distribution (Stacked Bar) - only if GENDER column exists
            if 'GENDER' in cdev_data.columns:
                cdev_gender = cdev_data.groupby(['COURSE_CODE', 'GENDER'])['MASKED_ID'].nunique().unstack(fill_value=0)
                cdev_gender_pct = cdev_gender.div(cdev_gender.sum(axis=1), axis=0) * 100
                
                fig, ax = plt.subplots(figsize=(12, 8))
                cdev_gender_pct.plot(kind='bar', stacked=True, ax=ax, 
                                   color=self.colors['gender_palette'][:len(cdev_gender_pct.columns)],
                                   alpha=0.8)
                
                ax.set_xlabel('CDEV Course Code', fontsize=12, fontweight='bold')
                ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
                ax.set_title('CDEV Course Gender Distribution', fontsize=14, fontweight='bold', pad=20)
                ax.legend(title='Gender')
                ax.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                
                filename2 = f"cdev_gender_{self.date_str}.png"
                filepath2 = os.path.join(self.output_dir, filename2)
                plt.savefig(filepath2, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                charts_generated.append(filepath2)
            else:
                print("WARNING:  Skipping CDEV gender chart - GENDER column not available in WIL data")
            
            print(f" CDEV Analysis Charts generated: {len(charts_generated)} files")
            
            return charts_generated
            
        except Exception as e:
            print(f" Failed to generate CDEV analysis charts: {str(e)}")
            return charts_generated
    
    def get_latest_year_data(self) -> pd.DataFrame:
        """Get data from the latest available year for key metrics calculation."""
        if 'ACADEMIC_YEAR' in self.data.columns:
            available_years = sorted(self.data['ACADEMIC_YEAR'].unique())
            if len(available_years) > 1:
                latest_year = available_years[-1]
                print(f"INFO: Using {latest_year} data for key metrics calculation (latest year with complete data)")
                return self.data[self.data['ACADEMIC_YEAR'] == latest_year]
        return self.data

    def generate_analysis_summary(self) -> Dict:
        """Generate comprehensive analysis summary with key statistics and PDF-ready content."""
        try:
            # Use latest year data for key metrics in multi-year analysis
            latest_year_data = self.get_latest_year_data()
            is_multi_year = len(self.data['ACADEMIC_YEAR'].unique()) > 1 if 'ACADEMIC_YEAR' in self.data.columns else False
            latest_year = latest_year_data['ACADEMIC_YEAR'].iloc[0] if 'ACADEMIC_YEAR' in latest_year_data.columns else "2025"
            
            summary = {
                "report_metadata": {
                    "generation_date": datetime.now().isoformat(),
                    "generation_date_formatted": datetime.now().strftime("%B %d, %Y"),
                    "data_source": self.data_path,
                    "total_records": len(self.data),
                    "academic_year": str(latest_year),
                    "report_title": "Work Integrated Learning (WIL) Data Analysis Report",
                    "report_version": "1.0",
                    "is_multi_year_analysis": is_multi_year,
                    "focus_year": str(latest_year) if is_multi_year else None
                },
                "key_statistics": {
                    "total_students": latest_year_data['MASKED_ID'].nunique(),
                    "total_faculties": latest_year_data['FACULTY_DESCR'].nunique(),
                    "total_courses": latest_year_data['COURSE_CODE'].nunique(),
                    "focus_year": str(latest_year) if is_multi_year else None
                },
                "faculty_breakdown": {},
                "residency_breakdown": {},
                "gender_breakdown": {},
                "equity_cohort_statistics": {},
                "cdev_statistics": {},
                "chart_descriptions": {},
                "key_insights": {},
                "pdf_ready_content": {}
            }
            
            # Faculty breakdown - use latest year data for key insights
            faculty_stats = latest_year_data.groupby('FACULTY_DESCR')['MASKED_ID'].nunique().to_dict()
            latest_year_total_students = sum(faculty_stats.values())
            summary["faculty_breakdown"] = {
                faculty: {
                    "count": count,
                    "percentage": round((count / latest_year_total_students) * 100, 1)
                }
                for faculty, count in faculty_stats.items()
            }
            
            # Residency breakdown - use latest year data  
            residency_stats = latest_year_data.groupby('RESIDENCY_GROUP_DESCR')['MASKED_ID'].nunique().to_dict()
            summary["residency_breakdown"] = {
                status: {
                    "count": count,
                    "percentage": round((count / latest_year_total_students) * 100, 1)
                }
                for status, count in residency_stats.items()
            }
            
            # Gender breakdown - prioritize latest year data for multi-year analysis
            if 'GENDER' in latest_year_data.columns:
                # Filter to only records with actual gender data (non-null) from latest year
                latest_year_gender_data = latest_year_data[latest_year_data['GENDER'].notna()]
                
                if len(latest_year_gender_data) > 0:
                    gender_stats = latest_year_gender_data['GENDER'].value_counts().to_dict()
                    total_with_gender = len(latest_year_gender_data)
                    
                    summary["gender_breakdown"] = {
                        gender: {
                            "count": count,
                            "percentage": round((count / total_with_gender) * 100, 1)
                        }
                        for gender, count in gender_stats.items()
                    }
                    
                    # Add metadata about gender data
                    summary["gender_metadata"] = {
                        "total_records_with_gender": total_with_gender,
                        "total_latest_year_records": len(latest_year_data),
                        "latest_year_used": str(latest_year),
                        "gender_data_coverage": round((total_with_gender / len(latest_year_data)) * 100, 1)
                    }
                    print(f"INFO: Gender analysis using {latest_year} data: {total_with_gender} records with gender information")
                else:
                    # GENDER column exists but no actual gender data in latest year
                    summary["gender_breakdown"] = {
                        "Not Available": {
                            "count": 0,
                            "percentage": 0.0
                        }
                    }
                    print(f"WARNING:  GENDER column found in {latest_year} but no gender data available")
            else:
                # GENDER column not available in latest year data
                summary["gender_breakdown"] = {
                    "Not Available": {
                        "count": 0,
                        "percentage": 0.0
                    }
                }
                print(f"WARNING:  GENDER column not found in {latest_year} data")
            
            # Equity cohort statistics - use latest year data
            first_gen_rate = ((latest_year_data['FIRST_GENERATION_IND'] == 'First Generation').sum() / len(latest_year_data) * 100 
                             if 'FIRST_GENERATION_IND' in latest_year_data.columns else 0)
            indigenous_rate = ((latest_year_data['ATSI_GROUP'] != 'Non Indigenous').sum() / len(latest_year_data) * 100 
                              if 'ATSI_GROUP' in latest_year_data.columns else 0)
            
            summary["equity_cohort_statistics"] = {
                "first_generation_rate": round(first_gen_rate, 1),
                "indigenous_participation_rate": round(indigenous_rate, 1),
                "ses_distribution": (self.data['SES'].value_counts().to_dict() 
                                   if 'SES' in self.data.columns else {}),
                "regional_distribution": (self.data['REGIONAL_REMOTE'].value_counts().to_dict() 
                                        if 'REGIONAL_REMOTE' in self.data.columns else {})
            }
            
            # CDEV statistics
            cdev_data = self.data[self.data['IS_CDEV']]
            summary["cdev_statistics"] = {
                "total_cdev_students": cdev_data['MASKED_ID'].nunique(),
                "total_cdev_courses": cdev_data['COURSE_CODE'].nunique(),
                "cdev_course_list": cdev_data['COURSE_CODE'].unique().tolist()
            }
            
            # Generate chart descriptions for PDF integration
            summary["chart_descriptions"] = self._generate_chart_descriptions(summary)
            
            # Generate key insights for PDF report
            summary["key_insights"] = self._generate_key_insights(summary)
            
            # Generate PDF-ready content sections
            summary["pdf_ready_content"] = self._generate_pdf_content(summary)
            
            # Generate analysis tables
            summary["analysis_tables"] = self.generate_all_analysis_tables()
            
            # Save summary to JSON file with proper serialization
            summary_path = os.path.join(self.output_dir, f"analysis_summary_{self.date_str}.json")
            
            # Convert numpy types for JSON serialization
            def convert_numpy_types(obj):
                if hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(v) for v in obj]
                else:
                    return obj
            
            summary_serializable = convert_numpy_types(summary)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_serializable, f, indent=2, ensure_ascii=False)
            
            print(f" Analysis summary generated: analysis_summary_{self.date_str}.json")
            
            return summary
            
        except Exception as e:
            print(f" Failed to generate analysis summary: {str(e)}")
            return {}
    
    def generate_all_charts(self) -> Dict[str, List[str]]:
        """
        Generate all required charts for the WIL report.
        
        Returns:
            Dictionary containing paths to all generated chart files
        """
        print("=" * 60)
        print("WIL REPORT CHART GENERATION")
        print("=" * 60)
        
        if self.data is None:
            self.load_data()
        
        results = {
            "year_comparison": [],
            "faculty_residency": [],
            "gender_distribution": [],
            "equity_cohort": [],
            "cdev_analysis": [],
            "table_visualizations": [],
            "summary_file": None
        }
        
        # Generate all chart types
        print("\n1. Generating Year-over-Year Comparison Chart...")
        year_chart = self.generate_year_comparison_chart()
        if year_chart:
            results["year_comparison"].append(year_chart)
        
        print("\n2. Generating Faculty and Residency Status Chart...")
        faculty_chart = self.generate_faculty_residency_chart()
        if faculty_chart:
            results["faculty_residency"].append(faculty_chart)
        
        print("\n3. Generating Gender Distribution Charts...")
        gender_charts = self.generate_gender_distribution_charts()
        results["gender_distribution"].extend(gender_charts)
        
        print("\n4. Generating Equity Cohort Participation Charts...")
        equity_charts = self.generate_equity_cohort_charts()
        results["equity_cohort"].extend(equity_charts)
        
        print("\n5. Generating CDEV Course Analysis Charts...")
        cdev_charts = self.generate_cdev_analysis_charts()
        results["cdev_analysis"].extend(cdev_charts)
        
        print("\n6. Generating Table Visualizations...")
        table_charts = self.generate_table_visualizations()
        results["table_visualizations"].extend(table_charts)
        
        print("\n7. Generating Analysis Summary...")
        summary = self.generate_analysis_summary()
        if summary:
            results["summary_file"] = f"analysis_summary_{self.date_str}.json"
        
        # Print final summary
        total_charts = sum(len(charts) for charts in results.values() if isinstance(charts, list))
        print("\n" + "=" * 60)
        print(f"CHART GENERATION COMPLETE")
        print("=" * 60)
        print(f"Total charts generated: {total_charts}")
        print(f"Output directory: {self.output_dir}")
        print(f"All files saved with date suffix: {self.date_str}")
        
        return results
    
    def _generate_chart_descriptions(self, summary: Dict) -> Dict:
        """Generate descriptive text for each chart type for PDF integration."""
        descriptions = {}
        
        # Year comparison description
        descriptions["year_comparison"] = {
            "title": "Faculty Enrollment Overview (2025)",
            "description": f"This chart displays the distribution of WIL students across {summary['key_statistics']['total_faculties']} faculties. " +
                          f"A total of {summary['key_statistics']['total_students']:,} students are enrolled in WIL programs.",
            "key_finding": f"The largest faculty by enrollment is {max(summary['faculty_breakdown'].items(), key=lambda x: x[1]['count'])[0]}."
        }
        
        # Faculty residency description
        descriptions["faculty_residency"] = {
            "title": "Student Distribution by Faculty and Residency Status",
            "description": "This grouped bar chart compares local and international student enrollment across different faculties, " +
                          "providing insights into the diversity and international appeal of each program.",
            "key_finding": f"Overall, {summary['residency_breakdown'].get('Local', {}).get('percentage', 0):.1f}% are local students " +
                          f"and {summary['residency_breakdown'].get('International', {}).get('percentage', 0):.1f}% are international students."
        }
        
        # Gender distribution description
        descriptions["gender_distribution"] = {
            "title": "Gender Representation Analysis", 
            "description": "These charts examine gender balance across the WIL program, showing both overall distribution " +
                          "and faculty-specific gender ratios to identify areas for diversity improvement.",
            "key_finding": (f"Gender distribution is {summary['gender_breakdown'].get('Female', {}).get('percentage', 0):.1f}% female " +
                          f"and {summary['gender_breakdown'].get('Male', {}).get('percentage', 0):.1f}% male." 
                          if 'Female' in summary['gender_breakdown'] or 'Male' in summary['gender_breakdown'] 
                          else "Gender information is not available in the WIL dataset.")
        }
        
        return descriptions
    
    def _generate_key_insights(self, summary: Dict) -> Dict:
        """Generate key insights and recommendations for PDF report."""
        insights = {}
        
        # Overall program insights
        insights["program_overview"] = [
            f"The WIL program serves {summary['key_statistics']['total_students']:,} students across {summary['key_statistics']['total_faculties']} faculties.",
            f"A total of {summary['key_statistics']['total_courses']} different courses are offered.",
            "The program demonstrates strong diversity in both academic disciplines and student demographics."
        ]
        
        # Diversity insights
        total_intl_pct = summary['residency_breakdown'].get('International', {}).get('percentage', 0)
        insights["diversity_analysis"] = [
            f"International student participation is {total_intl_pct:.1f}%.",
            (f"Gender balance shows {summary['gender_breakdown'].get('Female', {}).get('percentage', 0):.1f}% female participation." 
             if 'Female' in summary['gender_breakdown'] else 
             "Gender information is not available in WIL data."),
            f"First-generation student representation is {summary['equity_cohort_statistics']['first_generation_rate']:.1f}%."
        ]
        
        return insights
    
    def _generate_pdf_content(self, summary: Dict) -> Dict:
        """Generate structured content ready for PDF template integration."""
        pdf_content = {}
        
        # Executive summary
        pdf_content["executive_summary"] = {
            "total_students": f"{summary['key_statistics']['total_students']:,}",
            "total_faculties": str(summary['key_statistics']['total_faculties']),
            "total_courses": str(summary['key_statistics']['total_courses']),
            "academic_year": summary['report_metadata']['academic_year'],
            "report_date": summary['report_metadata']['generation_date_formatted']
        }
        
        # Chart file mappings for PDF template - include table visualizations
        pdf_content["chart_files"] = {
            "year_comparison": f"year_comparison_{self.date_str}.png",
            "faculty_residency": f"faculty_residency_{self.date_str}.png", 
            "table1_faculty_comparison_chart": f"table1_faculty_comparison_chart_{self.date_str}.png",
            "table3_academic_levels_chart": f"table3_academic_levels_chart_{self.date_str}.png",
            "gender_pie": f"gender_distribution_pie_{self.date_str}.png",
            "gender_faculty": f"gender_distribution_faculty_{self.date_str}.png",
            "first_generation": f"first_generation_participation_{self.date_str}.png",
            "ses_distribution": f"ses_distribution_{self.date_str}.png",
            "indigenous_participation": f"indigenous_participation_{self.date_str}.png",
            "regional_distribution": f"regional_distribution_{self.date_str}.png",
            "cdev_residency": f"cdev_residency_{self.date_str}.png",
            "cdev_gender": f"cdev_gender_{self.date_str}.png"
        }
        
        # Key metrics for highlighting
        pdf_content["key_metrics"] = {
            "largest_faculty": max(summary['faculty_breakdown'].items(), key=lambda x: x[1]['count'])[0],
            "international_percentage": f"{summary['residency_breakdown'].get('International', {}).get('percentage', 0):.1f}%",
            "female_percentage": (f"{summary['gender_breakdown'].get('Female', {}).get('percentage', 0):.1f}%" 
                                 if 'Female' in summary['gender_breakdown'] else "N/A"),
            "first_gen_percentage": f"{summary['equity_cohort_statistics']['first_generation_rate']:.1f}%"
        }
        
        return pdf_content


def generate_wil_report_charts(data_path: str, output_dir: str = "reports") -> Dict[str, List[str]]:
    """
    Main function to generate all WIL report charts.
    
    Args:
        data_path: Path to the CSV data file
        output_dir: Directory to save generated charts and reports
        
    Returns:
        Dictionary containing paths to all generated chart files
    """
    try:
        # Initialize analyzer
        analyzer = WILReportAnalyzer(data_path, output_dir)
        
        # Load data
        analyzer.load_data()
        
        # Generate all charts
        results = analyzer.generate_all_charts()
        
        print("\n=> WIL Report Analysis Complete!")
        print(f"=> All files saved to: {output_dir}")
        
        return results
        
    except Exception as e:
        print(f"ERROR: Error in chart generation: {str(e)}")
        return {}


if __name__ == "__main__":
    # Example usage
    sample_data_path = "../../../sample_data/sampledata.csv"
    output_directory = "../../../reports"
    
    results = generate_wil_report_charts(sample_data_path, output_directory)