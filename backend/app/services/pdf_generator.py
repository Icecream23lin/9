
import os
import json
import logging
import requests
import argparse
import zipfile
from io import BytesIO
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


# Resources Used:
# https://huggingface.co/google/flan-t5-base/tree/main
# https://www.geeksforgeeks.org/machine-learning/introduction-to-beam-search-algorithm/


# Encapsulate single file logic
def process_single_file(file_id):
    try:
        # step1: call the analyze service
        analyze_url = f"http://localhost:5050/api/analyze/pdf-ready/{file_id}"
        headers = {'Content-Type': 'application/json'}
        payload = {"report_title": "Work Integrated Learning Data Analysis Report"}
        analyze_response = requests.post(analyze_url, headers=headers, json=payload)
        if analyze_response.status_code != 200:
            return{
                'file_id': file_id,
                'success': False,
                'error': 'Failed to get analysis_id',
                'details': analyze_response.text
            }
        
        analysis_id = analyze_response.json().get('analysis_id')
        if not analysis_id:
            return {
                'file_id': file_id,
                'success': False,
                'error': 'Invalid analysis_id'
            }

        # step2: Download ZIP
        download_url = f"http://localhost:5050/api/download/{analysis_id}"
        zip_response = requests.get(download_url)
        if zip_response.status_code != 200:
            return{
                'file_id': file_id,
                'success': False,
                'error': 'Failed to download zip',
                'details': zip_response.text
            }
        
        zip_bytes = BytesIO(zip_response.content)

        # step3: unzip to extract json and generate NLP text
        pdf_data = load_json_from_zip(zip_bytes)
        trend_text = NLP_generation(pdf_data)

        # step4: generate PDF to persistent path in analysis results directory
        from flask import current_app
        pdf_filename = f"report_{analysis_id}.pdf"
        analysis_results_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        
        # Ensure the analysis results directory exists
        os.makedirs(analysis_results_dir, exist_ok=True)
        
        pdf_path = os.path.join(analysis_results_dir, pdf_filename)
        pdf_generation_from_zip(pdf_data, zip_bytes, trend_text, pdf_path)
        
        # Debug: Check if PDF was actually created
        if os.path.exists(pdf_path):
            print(f"SUCCESS: Single-file PDF successfully created at: {pdf_path}")
        else:
            print(f"ERROR: Single-file PDF creation failed: {pdf_path}")
            raise Exception(f"PDF file was not created at {pdf_path}")

        # step5: create download URL for the PDF
        download_url = f"/api/report/pdf/{analysis_id}"
        
        return{
                'file_id': file_id,
                'analysis_id': analysis_id,
                'success': True,
                'download_url': download_url,
                'message': 'PDF report generated successfully'
            }

    except Exception as e:
         return{
                'file_id': file_id,
                'success': False,
                'error': 'Unexpected error occurs',
                'details': str(e)
            }


# Multi-file processing logic
def process_multiple_files(file_ids, report_title=None):
    """Process multiple files for multi-year PDF generation"""
    try:
        # step1: call the multi-file analyze service
        analyze_url = f"http://localhost:5050/api/analyze/multi-file/pdf-ready"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "file_ids": file_ids,
            "report_title": report_title or "Multi-Year Work Integrated Learning Data Analysis Report"
        }
        
        analyze_response = requests.post(analyze_url, headers=headers, json=payload)
        if analyze_response.status_code != 200:
            return {
                'file_ids': file_ids,
                'success': False,
                'error': 'Failed to get analysis_id',
                'details': analyze_response.text
            }
        
        analysis_data = analyze_response.json()
        analysis_id = analysis_data.get('analysis_id')
        if not analysis_id:
            return {
                'file_ids': file_ids,
                'success': False,
                'error': 'Invalid analysis_id'
            }

        # step2: Download ZIP
        download_url = f"http://localhost:5050/api/download/{analysis_id}"
        zip_response = requests.get(download_url)
        if zip_response.status_code != 200:
            return {
                'file_ids': file_ids,
                'success': False,
                'error': 'Failed to download zip',
                'details': zip_response.text
            }
        
        zip_bytes = BytesIO(zip_response.content)

        # step3: unzip to extract json and generate NLP text for multi-year data
        pdf_data = load_json_from_zip(zip_bytes)
        trend_text = NLP_generation_multi_year(pdf_data)

        # step4: generate PDF to persistent path in analysis results directory
        from flask import current_app
        pdf_filename = f"multi_year_report_{analysis_id}.pdf"
        analysis_results_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'analysis_results', analysis_id)
        
        # Ensure the analysis results directory exists
        os.makedirs(analysis_results_dir, exist_ok=True)
        
        pdf_path = os.path.join(analysis_results_dir, pdf_filename)
        pdf_generation_from_zip_multi_year(pdf_data, zip_bytes, trend_text, pdf_path)
        
        # Debug: Check if PDF was actually created
        if os.path.exists(pdf_path):
            print(f"SUCCESS: Multi-year PDF successfully created at: {pdf_path}")
        else:
            print(f"ERROR: Multi-year PDF creation failed: {pdf_path}")
            raise Exception(f"PDF file was not created at {pdf_path}")

        # step5: create download URL for the PDF
        download_url = f"/api/report/pdf/{analysis_id}"
        
        return {
            'file_ids': file_ids,
            'analysis_id': analysis_id,
            'success': True,
            'download_url': download_url,
            'files_processed': analysis_data.get('files_processed', len(file_ids)),
            'years_analyzed': analysis_data.get('years_analyzed', []),
            'total_records': analysis_data.get('total_records', 0),
            'message': 'Multi-year PDF report generated successfully'
        }

    except Exception as e:
         return{
                'file_ids': file_ids,
                'success': False,
                'error': 'Unexpected error occurs',
                'details': str(e)
            }

#=========================================================#
#Step 1: Read in pdf_template_data.json file
#=========================================================#
def load_json_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        with zip_ref.open('content/pdf_template_data.json') as f:
            return json.load(f)

#=========================================================#
#Step 2: Use pre-trained model to generate predicted text
#=========================================================#
def NLP_generation(data_pdf):
    """Generate meaningful analysis text for single-year WIL program insights"""
    summary_text = data_pdf.get('executive_summary', {})
    metrics = data_pdf.get('key_metrics', {})
    key_insights = data_pdf.get('key_insights', {})
    
    # Debug: Print extracted data to check accuracy
    print(f"DEBUG - Executive Summary: {summary_text}")
    print(f"DEBUG - Key Metrics: {metrics}")
    print(f"DEBUG - Key Insights: {key_insights}")

    # Generate comprehensive analysis based on available data
    total_students = summary_text.get('total_students', 'N/A')
    total_faculties = summary_text.get('total_faculties', 'N/A')
    academic_year = summary_text.get('academic_year', 'N/A')
    
    # Build meaningful insights text
    insights = []
    
    # Overview
    if total_students != 'N/A' and total_faculties != 'N/A':
        insights.append(f"During the {academic_year} academic year, the WIL program engaged "
                       f"{total_students} students across {total_faculties} faculties, "
                       f"demonstrating the program's broad reach and cross-disciplinary impact.")
    
    # Diversity analysis
    int_pct = metrics.get('international_percentage', 'N/A')
    female_pct = metrics.get('female_percentage', 'N/A')
    first_gen_pct = metrics.get('first_generation_percentage', 'N/A')
    
    if int_pct != 'N/A' or female_pct != 'N/A':
        diversity_text = "The program's participant demographics reflect strong diversity: "
        diversity_parts = []
        if int_pct != 'N/A':
            diversity_parts.append(f"international students account for {int_pct}% of participants")
        if female_pct != 'N/A':
            diversity_parts.append(f"female students represent {female_pct}% of the cohort")
        if first_gen_pct != 'N/A':
            diversity_parts.append(f"first-generation university students comprise {first_gen_pct}%")
        
        if diversity_parts:
            insights.append(diversity_text + ", ".join(diversity_parts) + ".")
    
    # Faculty engagement
    largest_faculty = metrics.get('largest_faculty', 'N/A')
    if largest_faculty != 'N/A':
        insights.append(f"The {largest_faculty} demonstrates the highest level of WIL program participation, "
                       f"highlighting strong connections between academic study and industry practice in this field.")
    
    # Combine all insights or provide fallback
    if insights:
        return " ".join(insights)
    else:
        # Fallback content if data is insufficient
        return ("This analysis examines WIL program participation patterns, highlighting student engagement "
               "across different faculties and demographic groups. The data provides valuable insights into "
               "program accessibility, diversity representation, and the effectiveness of work-integrated "
               "learning opportunities in connecting academic study with practical industry experience.")


#=========================================================#
#Step 2b: Multi-year NLP generation for multiple files
#=========================================================#
def NLP_generation_multi_year(data_pdf):
    """Generate meaningful analysis text for multi-year WIL program insights - focusing on latest year"""
    summary_text = data_pdf.get('executive_summary', {})
    metrics = data_pdf.get('key_metrics', {})
    multi_year_insights = data_pdf.get('multi_year_insights', {})
    key_insights = data_pdf.get('key_insights', {})
    
    # Debug: Print extracted data to check accuracy
    print(f"DEBUG - Executive Summary: {summary_text}")
    print(f"DEBUG - Key Metrics: {metrics}")
    print(f"DEBUG - Multi-year Insights: {multi_year_insights}")
    print(f"DEBUG - Key Insights: {key_insights}")
    
    # Check for year-specific breakdown in full data
    full_stats = data_pdf.get('full_statistics', {})
    gender_data = full_stats.get('gender_breakdown', {})
    print(f"DEBUG - Gender Breakdown: {gender_data}")

    # Generate comprehensive analysis based on available data - focus on latest year
    years = multi_year_insights.get('years_analyzed', [])
    latest_year = max(years) if years else None
    total_students = summary_text.get('total_students', 'N/A')
    total_files = multi_year_insights.get('total_files_processed', 2)
    
    # Build meaningful insights text focusing on the latest year
    insights = []
    
    # Overview - emphasize latest year trends
    if years and total_students != 'N/A':
        year_range = f"{min(years)} to {max(years)}" if len(years) > 1 else str(years[0])
        if len(years) > 1:
            insights.append(f"This comprehensive analysis examines WIL program participation from {year_range}, "
                           f"with primary focus on {latest_year} trends and year-over-year comparisons. "
                           f"The analysis encompasses {total_students} total student records across {total_files} datasets.")
        else:
            insights.append(f"This analysis examines WIL program participation for {latest_year}, "
                           f"encompassing {total_students} student records.")
    
    # Latest year diversity insights - prioritize current data
    int_pct = metrics.get('international_percentage', 'N/A')
    female_pct = metrics.get('female_percentage', 'N/A')
    first_gen_pct = metrics.get('first_generation_percentage', 'N/A')
    
    if int_pct != 'N/A' or female_pct != 'N/A':
        if latest_year:
            diversity_text = f"In {latest_year}, the program demonstrates significant diversity: "
        else:
            diversity_text = "The program demonstrates significant diversity: "
        diversity_parts = []
        
        if int_pct != 'N/A' and int_pct != '0.0%':
            diversity_parts.append(f"international students comprise {int_pct}% of participants")
        if female_pct != 'N/A' and female_pct != '0.0%' and female_pct != 'N/A':
            diversity_parts.append(f"female participation stands at {female_pct}%")
        if first_gen_pct != 'N/A' and first_gen_pct != '0.0%':
            diversity_parts.append(f"first-generation students represent {first_gen_pct}%")
        
        if diversity_parts:
            insights.append(diversity_text + ", ".join(diversity_parts) + ".")
    
    # Latest year faculty participation trends
    largest_faculty = metrics.get('largest_faculty', 'N/A')
    if largest_faculty != 'N/A':
        if latest_year:
            insights.append(f"In {latest_year}, {largest_faculty} shows the highest WIL program engagement, "
                           f"indicating strong industry partnerships and practical learning opportunities in this domain.")
        else:
            insights.append(f"The {largest_faculty} shows the highest WIL program engagement, "
                           f"indicating strong industry partnerships and practical learning opportunities in this domain.")
    
    # Add year-over-year comparison if multiple years available
    if len(years) > 1:
        insights.append(f"The year-over-year comparison from {min(years)} to {max(years)} reveals evolving "
                       f"participation patterns and demographic trends in work-integrated learning programs.")
    
    # Combine all insights or provide fallback
    if insights:
        return " ".join(insights)
    else:
        # Fallback content with latest year emphasis
        if latest_year:
            return (f"This analysis provides insights into WIL program participation patterns for {latest_year}, "
                   "examining student engagement across different faculties and demographic groups. "
                   "The data reveals important trends in program accessibility and student diversity that inform "
                   "future program development and resource allocation decisions.")
        else:
            return ("This multi-year analysis provides insights into WIL program participation patterns, "
                   "examining student engagement across different faculties, demographic groups, and academic periods. "
                   "The data reveals important trends in program accessibility and student diversity that inform "
                   "future program development and resource allocation decisions.")

#===================================================================#
#Step 3: Generate final version of report along with NLP prediction
#===================================================================#
def pdf_generation_from_zip(pdf_data, zip_path, trend_text, output_path):
    
    # Create PDF file
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Self define format
    title_style = ParagraphStyle(
        'CustomTitle',parent=styles['Heading1'],
        fontSize=20, spaceAfter=30,
        textColor=colors.darkblue
    )

    # Title
    story.append(Paragraph(pdf_data.get('report_title', 'Work Integrated Learning Report'), title_style))
    story.append(Spacer(1, 0.3*inch))

    # Dealing with executive summary
    story.append(Paragraph("executive summary", styles['Heading2']))
    exec_summary = pdf_data.get('executive_summary', {})
    summary_data = [
    ['Metric', 'Value'],
    ['Total students: ', exec_summary.get('total_students', 'N/A')],
    ['Number of Faculty: ', exec_summary.get('total_faculties', 'N/A')],
    ['Academic Year: ', exec_summary.get('academic_year', 'N/A')],
    ['Report Date: ', exec_summary.get('report_date', 'N/A')]
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))

    # WIL program insights
    story.append(Paragraph("WIL Program Insights", styles['Heading2']))
    story.append(Paragraph(trend_text, styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    # Add analysis tables if available - check multiple possible data paths
    analysis_tables = pdf_data.get('analysis_tables', {})
    
    # If not found at top level, check in full_statistics
    if not analysis_tables:
        full_stats = pdf_data.get('full_statistics', {})
        analysis_tables = full_stats.get('analysis_tables', {})
    
    # Debug: Print analysis_tables structure
    print(f"DEBUG - PDF Single-file analysis_tables structure: {list(analysis_tables.keys()) if analysis_tables else 'None'}")
    
    if analysis_tables and len([k for k in analysis_tables.keys() if not k.startswith('_')]) > 0:  # Check for actual tables (excluding metadata)
        story.append(Paragraph("Statistical Analysis Tables", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # WIL Enrollments Comparison Table
        if 'wil_enrollment_comparison' in analysis_tables:
            table_data = analysis_tables['wil_enrollment_comparison']
            story.append(Paragraph(table_data.get('title', 'WIL Enrollments Comparison'), styles['Heading3']))
            
            # Convert table data to ReportLab format
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            if headers and rows:
                # Create table data with headers
                pdf_table_data = [headers]
                
                # Add data rows (limit to prevent page overflow)
                for row in rows[:15]:  # Show max 15 rows for better table coverage
                    pdf_row = []
                    for header in headers:
                        value = row.get(header, 'N/A')
                        # Format values nicely and handle various data types
                        if value is None or value == '':
                            pdf_row.append('')
                        elif isinstance(value, (int, float)) and header != '% Change':
                            # Format numbers with comma separators for readability
                            if isinstance(value, float) and value.is_integer():
                                pdf_row.append(f"{int(value):,}")
                            elif isinstance(value, int):
                                pdf_row.append(f"{value:,}")
                            else:
                                pdf_row.append(str(value))
                        else:
                            # Ensure all values are strings and handle any special characters
                            pdf_row.append(str(value).replace('\n', ' ').replace('\r', ''))
                    pdf_table_data.append(pdf_row)
                
                # Create and style the table - dynamic column widths based on headers and content
                num_cols = len(headers)
                # Check actual header names to determine proper layout
                if num_cols == 4 and 'Faculty' in headers and '% Change' in headers:
                    # Table 1 format: Faculty, Year1, Year2, % Change - wider Faculty column
                    col_widths = [3.2*inch, 1.0*inch, 1.0*inch, 0.8*inch]
                elif num_cols == 4 and 'Distinct Count of WIL Students' in headers and '% Change' in headers:
                    # Table 3 format: Distinct Count of WIL Students, Year1, Year2, % Change
                    col_widths = [5.2*inch, 0.6*inch, 0.6*inch, 0.6*inch]
                elif num_cols == 5:  # Other extended format with additional columns
                    col_widths = [0.5*inch, 2.2*inch, 1*inch, 1*inch, 1.3*inch]
                else:  # Fallback for other formats
                    col_widths = [6*inch/max(num_cols, 1)] * num_cols
                
                try:
                    enrollment_table = Table(pdf_table_data, colWidths=col_widths)
                except Exception as e:
                    print(f"Warning: Table creation failed, using default layout: {str(e)}")
                    enrollment_table = Table(pdf_table_data)
                enrollment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    # Highlight total row
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                story.append(enrollment_table)
                story.append(Spacer(1, 0.3*inch))
        
        # Term Breakdown Table (show summary only due to space constraints)
        if 'term_breakdown' in analysis_tables:
            table_data = analysis_tables['term_breakdown']
            story.append(Paragraph(table_data.get('title', 'Term Breakdown Summary'), styles['Heading3']))
            
            summary = table_data.get('summary', {})
            term_summary_data = [
                ['Metric', 'Value'],
                ['Total Students', str(summary.get('total_students', 'N/A'))],
                ['Total Faculties', str(summary.get('total_faculties', 'N/A'))],
                ['Years Covered', ', '.join(summary.get('years_covered', []))],
            ]
            
            term_summary_table = Table(term_summary_data, colWidths=[2*inch, 2*inch])
            term_summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ]))
            story.append(term_summary_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Multi-Year Student Demographics Analysis - Full Table
        if 'distinct_student_count' in analysis_tables:
            table_data = analysis_tables['distinct_student_count']
            story.append(Paragraph(table_data.get('title', 'Multi-Year Student Demographics Analysis'), styles['Heading3']))
            
            # Convert table data to ReportLab format - Full detailed table
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            if headers and rows:
                # Create table data with headers
                pdf_table_data = [headers]
                
                # Add data rows (limit to prevent page overflow)
                for row in rows[:25]:  # Show more rows for demographics table
                    pdf_row = []
                    for header in headers:
                        value = row.get(header, 'N/A')
                        # Format values nicely and handle various data types
                        if value is None or value == '':
                            pdf_row.append('')
                        elif isinstance(value, (int, float)) and header != '% Change':
                            # Format numbers with comma separators for readability
                            if isinstance(value, float) and value.is_integer():
                                pdf_row.append(f"{int(value):,}")
                            elif isinstance(value, int):
                                pdf_row.append(f"{value:,}")
                            else:
                                pdf_row.append(str(value))
                        else:
                            # Ensure all values are strings and handle any special characters
                            pdf_row.append(str(value).replace('\n', ' ').replace('\r', ''))
                    pdf_table_data.append(pdf_row)
                
                # Create and style the table - dynamic column widths based on headers and content
                num_cols = len(headers)
                # Check actual header names to determine proper layout
                if num_cols == 4 and 'Faculty' in headers and '% Change' in headers:
                    # Table 1 format: Faculty, Year1, Year2, % Change - wider Faculty column
                    col_widths = [3.2*inch, 1.0*inch, 1.0*inch, 0.8*inch]
                elif num_cols == 4 and 'Distinct Count of WIL Students' in headers and '% Change' in headers:
                    # Table 3 format: Distinct Count of WIL Students, Year1, Year2, % Change
                    col_widths = [5.2*inch, 0.6*inch, 0.6*inch, 0.6*inch]
                elif num_cols == 5:  # Other extended format with additional columns
                    col_widths = [0.5*inch, 2.2*inch, 1*inch, 1*inch, 1.3*inch]
                else:  # Fallback for other formats
                    col_widths = [6*inch/max(num_cols, 1)] * num_cols
                
                try:
                    demographics_table = Table(pdf_table_data, colWidths=col_widths)
                except Exception as e:
                    print(f"Warning: Demographics table creation failed, using default layout: {str(e)}")
                    demographics_table = Table(pdf_table_data)
                
                # Build table style with dynamic formatting for Faculty rows
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    # Highlight total row
                    ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]
                
                # Add special formatting for Faculty rows (rows that don't start with spaces and aren't "Grand Total")
                for i, row_data in enumerate(pdf_table_data[1:], 1):  # Skip header row
                    first_col_value = str(row_data[0]).strip()
                    # Faculty rows: don't start with spaces, aren't "Total" or "Grand Total"
                    if (not first_col_value.startswith('  ') and 
                        first_col_value not in ['Total', 'Grand Total'] and
                        first_col_value != ''):
                        table_style.extend([
                            ('BACKGROUND', (0, i), (-1, i), colors.lightsteelblue),
                            ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
                        ])
                
                demographics_table.setStyle(TableStyle(table_style))
                story.append(demographics_table)
                story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("Note: Complete detailed tables are available in the accompanying analysis files.", 
                             styles['Normal']))
        story.append(Spacer(1, 0.5*inch))

    # Charts section - Enhanced to include table visualizations
    story.append(Paragraph("Data Visualizations", styles['Heading2']))
    
    # Define chart priority order and display names
    chart_priority = {
        'year_comparison': 'Year-over-Year Faculty Enrollment Comparison',
        'faculty_residency': 'Faculty and Residency Status Analysis',
        'table1_faculty_comparison_chart': 'Table 1: Faculty Enrollment Comparison Chart',
        'table3_academic_levels_chart': 'Table 3: Academic Level Distribution Chart',
        'gender_distribution_pie': 'Overall Gender Distribution',
        'gender_distribution_faculty': 'Gender Distribution by Faculty',
        'first_generation_participation': 'First Generation Student Participation',
        'ses_distribution': 'Socioeconomic Status Distribution',
        'indigenous_participation': 'Indigenous Student Participation',
        'regional_distribution': 'Regional Distribution of Students',
        'cdev_residency': 'CDEV Course Enrollment by Residency',
        'cdev_gender': 'CDEV Course Gender Distribution'
    }
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get all available chart files
        available_charts = []
        chart_files = pdf_data.get('charts', {})
        
        # Add charts from the charts mapping
        for chart_key, chart_file in chart_files.items():
            image_zip_path = f"charts/{chart_file}"
            if image_zip_path in zip_ref.namelist():
                available_charts.append((chart_key, chart_file, image_zip_path))
        
        # Also look for table visualization charts directly in charts folder
        for file_info in zip_ref.namelist():
            if file_info.startswith('charts/') and file_info.endswith('.png'):
                filename = file_info.split('/')[-1]
                # Check for table visualization charts
                if 'table1_faculty_comparison_chart' in filename or 'table3_academic_levels_chart' in filename:
                    chart_key = filename.replace('.png', '').split('_')[:-1]  # Remove date suffix
                    chart_key = '_'.join(chart_key)
                    if chart_key not in [c[0] for c in available_charts]:
                        available_charts.append((chart_key, filename, file_info))
        
        # Sort charts by priority
        def get_priority(chart_tuple):
            chart_key = chart_tuple[0]
            for i, priority_key in enumerate(chart_priority.keys()):
                if priority_key in chart_key:
                    return i
            return len(chart_priority)  # Put unrecognized charts at the end
        
        available_charts.sort(key=get_priority)
        
        # Add charts to PDF
        charts_added = 0
        for chart_key, chart_file, image_zip_path in available_charts:
            try:
                with zip_ref.open(image_zip_path) as image_file:
                    image_data = BytesIO(image_file.read())
                    
                    # Get display name
                    display_name = None
                    for priority_key, display_name_candidate in chart_priority.items():
                        if priority_key in chart_key:
                            display_name = display_name_candidate
                            break
                    
                    if not display_name:
                        display_name = chart_key.replace("_", " ").title()
                    
                    story.append(Paragraph(display_name, styles['Heading3']))
                    story.append(Image(image_data, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 0.5*inch))
                    charts_added += 1
                    
            except Exception as e:
                print(f"Warning: Could not add chart {chart_key}: {str(e)}")
        
        print(f"DEBUG - Added {charts_added} charts to PDF")

    doc.build(story)
    print(f"SUCCESS: PDF report has been generated: {output_path}")


#===================================================================#
#Step 3b: Generate multi-year PDF report with year-over-year analysis
#===================================================================#
def pdf_generation_from_zip_multi_year(pdf_data, zip_path, trend_text, output_path):
    """Generate PDF report specifically for multi-year analysis"""
    
    # Create PDF file
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Enhanced title style for multi-year reports
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=22, spaceAfter=30,
        textColor=colors.darkblue
    )
    
    # Multi-year subtitle style
    subtitle_style = ParagraphStyle(
        'SubTitle', parent=styles['Heading2'],
        fontSize=14, spaceAfter=20,
        textColor=colors.darkgreen
    )

    # Title
    story.append(Paragraph(pdf_data.get('report_title', 'Multi-Year Work Integrated Learning Report'), title_style))
    
    # Add multi-year context
    multi_year_insights = pdf_data.get('multi_year_insights', {})
    years_analyzed = multi_year_insights.get('years_analyzed', [])
    if years_analyzed:
        years_text = f"Comparative Analysis: {' vs '.join(map(str, years_analyzed))}"
        story.append(Paragraph(years_text, subtitle_style))
    
    story.append(Spacer(1, 0.3*inch))

    # Executive summary with multi-year context
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    exec_summary = pdf_data.get('executive_summary', {})
    
    # Debug: Print data to check structure
    print(f"DEBUG - Multi-year PDF exec_summary: {exec_summary}")
    print(f"DEBUG - Multi-year PDF multi_year_insights: {multi_year_insights}")
    
    # Enhanced summary data for multi-year analysis
    summary_data = [
        ['Metric', 'Value'],
        ['Total students:', exec_summary.get('total_students', 'N/A')],
        ['Number of Faculties:', exec_summary.get('total_faculties', 'N/A')],
        ['Analysis Period:', exec_summary.get('academic_year', 'N/A')],
        ['Years Compared:', ', '.join(map(str, years_analyzed)) if years_analyzed else 'N/A'],
        ['Files Processed:', str(multi_year_insights.get('total_files_processed', 'N/A'))],
        ['Total Records:', str(multi_year_insights.get('total_records', 'N/A'))],
        ['Report Date:', exec_summary.get('report_date', 'N/A')]
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))

    # Multi-year insights section
    story.append(Paragraph("WIL Program Analysis Insights", styles['Heading2']))
    story.append(Paragraph(trend_text, styles['Normal']))
    story.append(Spacer(1, 0.5*inch))

    # Add multi-year analysis tables if available - check multiple possible data paths
    analysis_tables = pdf_data.get('analysis_tables', {})
    
    # If not found at top level, check in full_statistics
    if not analysis_tables:
        full_stats = pdf_data.get('full_statistics', {})
        analysis_tables = full_stats.get('analysis_tables', {})
    
    # Debug: Print analysis_tables structure for multi-year
    print(f"DEBUG - PDF Multi-year analysis_tables structure: {list(analysis_tables.keys()) if analysis_tables else 'None'}")
    
    # Additional debug info
    print(f"DEBUG - PDF data keys: {list(pdf_data.keys())}")
    if 'full_statistics' in pdf_data:
        full_stats = pdf_data['full_statistics']
        print(f"DEBUG - full_statistics keys: {list(full_stats.keys()) if isinstance(full_stats, dict) else 'Not a dict'}")
        if isinstance(full_stats, dict) and 'analysis_tables' in full_stats:
            nested_tables = full_stats['analysis_tables']
            print(f"DEBUG - nested analysis_tables: {list(nested_tables.keys()) if nested_tables else 'None'}")
    else:
        print("DEBUG - full_statistics not found in pdf_data")
    
    if analysis_tables and len([k for k in analysis_tables.keys() if not k.startswith('_')]) > 0:  # Check for actual tables (excluding metadata)
        story.append(Paragraph("Multi-Year Statistical Analysis", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        # WIL Enrollments Year-over-Year Comparison Table
        if 'wil_enrollment_comparison' in analysis_tables:
            table_data = analysis_tables['wil_enrollment_comparison']
            story.append(Paragraph(table_data.get('title', 'WIL Enrollments Year-over-Year Comparison'), styles['Heading3']))
            
            # Convert table data to ReportLab format
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            if headers and rows:
                # Create table data with headers
                pdf_table_data = [headers]
                
                # Add data rows (limit to prevent page overflow)
                for row in rows[:15]:  # Limit rows for better page management
                    pdf_row = []
                    for header in headers:
                        value = row.get(header, 'N/A')
                        # Format values nicely and handle various data types
                        if value is None or value == '':
                            pdf_row.append('')
                        elif isinstance(value, (int, float)) and header != '% Change':
                            # Add comma formatting for large numbers
                            if isinstance(value, float) and value.is_integer():
                                pdf_row.append(f"{int(value):,}")
                            elif isinstance(value, int):
                                pdf_row.append(f"{value:,}")
                            else:
                                pdf_row.append(str(value))
                        else:
                            # Ensure all values are strings and handle any special characters
                            pdf_row.append(str(value).replace('\n', ' ').replace('\r', ''))
                    pdf_table_data.append(pdf_row)
                
                # Create and style the table with better formatting for multi-year - dynamic column widths
                num_cols = len(headers)
                if num_cols == 4 and 'Distinct Count of WIL Students' in headers and '% Change' in headers:  # Table 3 format: Distinct Count of WIL Students, Year1, Year2, % Change
                    col_widths = [5.2*inch, 0.6*inch, 0.6*inch, 0.6*inch]
                elif num_cols == 5:  # Other format: Count, Term, 2024, 2025, % Change
                    col_widths = [0.5*inch, 2.2*inch, 0.9*inch, 0.9*inch, 0.9*inch]
                elif num_cols == 4 and 'Faculty' in headers:  # Faculty table format
                    col_widths = [3.2*inch, 1.0*inch, 1.0*inch, 0.8*inch]
                elif num_cols == 4:  # Alternative format
                    col_widths = [0.5*inch, 2.8*inch, 1.1*inch, 1.1*inch]
                else:  # Fallback for other formats
                    col_widths = [6*inch/max(num_cols, 1)] * num_cols
                
                try:
                    enrollment_table = Table(pdf_table_data, colWidths=col_widths)
                except Exception as e:
                    print(f"Warning: Multi-year table creation failed, using default layout: {str(e)}")
                    enrollment_table = Table(pdf_table_data)
                enrollment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    # Highlight total row with stronger formatting
                    ('BACKGROUND', (0, -1), (-1, -1), colors.darkgreen),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                story.append(enrollment_table)
                story.append(Spacer(1, 0.3*inch))
                
                # Add summary insight
                summary = table_data.get('summary', {})
                if summary:
                    insight_text = (f"Overall enrollment changed by {summary.get('total_change', 'N/A')} students "
                                   f"({summary.get('total_change_pct', 'N/A')}) from {summary.get('year_1', '')} to {summary.get('year_2', '')}.")
                    story.append(Paragraph(f"<i>{insight_text}</i>", styles['Normal']))
                    story.append(Spacer(1, 0.3*inch))
        
        # Multi-year Student Demographics Analysis - Full Table
        if 'distinct_student_count' in analysis_tables:
            table_data = analysis_tables['distinct_student_count']
            story.append(Paragraph(table_data.get('title', 'Multi-Year Student Demographics Analysis'), styles['Heading3']))
            
            # Convert table data to ReportLab format - Full detailed table
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            if headers and rows:
                # Create table data with headers
                pdf_table_data = [headers]
                
                # Add data rows (limit to prevent page overflow)
                for row in rows[:30]:  # Show more rows for multi-year demographics table
                    pdf_row = []
                    for header in headers:
                        value = row.get(header, 'N/A')
                        # Format values nicely and handle various data types
                        if value is None or value == '':
                            pdf_row.append('')
                        elif isinstance(value, (int, float)) and header != '% Change':
                            # Add comma formatting for large numbers
                            if isinstance(value, float) and value.is_integer():
                                pdf_row.append(f"{int(value):,}")
                            elif isinstance(value, int):
                                pdf_row.append(f"{value:,}")
                            else:
                                pdf_row.append(str(value))
                        else:
                            # Ensure all values are strings and handle any special characters
                            pdf_row.append(str(value).replace('\n', ' ').replace('\r', ''))
                    pdf_table_data.append(pdf_row)
                
                # Create and style the table with better formatting for multi-year - dynamic column widths
                num_cols = len(headers)
                if num_cols == 4 and 'Distinct Count of WIL Students' in headers and '% Change' in headers:  # Table 3 format: Distinct Count of WIL Students, Year1, Year2, % Change
                    col_widths = [5.2*inch, 0.6*inch, 0.6*inch, 0.6*inch]
                elif num_cols == 5:  # Other format: Count, Term, 2024, 2025, % Change
                    col_widths = [0.5*inch, 2.2*inch, 0.9*inch, 0.9*inch, 0.9*inch]
                elif num_cols == 4 and 'Faculty' in headers:  # Faculty table format
                    col_widths = [3.2*inch, 1.0*inch, 1.0*inch, 0.8*inch]
                elif num_cols == 4:  # Alternative format
                    col_widths = [0.5*inch, 2.8*inch, 1.1*inch, 1.1*inch]
                else:  # Fallback for other formats
                    col_widths = [6*inch/max(num_cols, 1)] * num_cols
                
                try:
                    demographics_table = Table(pdf_table_data, colWidths=col_widths)
                except Exception as e:
                    print(f"Warning: Multi-year demographics table creation failed, using default layout: {str(e)}")
                    demographics_table = Table(pdf_table_data)
                
                # Build table style with dynamic formatting for Faculty rows
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    # Highlight total row with stronger formatting
                    ('BACKGROUND', (0, -1), (-1, -1), colors.darkgreen),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]
                
                # Add special formatting for Faculty rows (rows that don't start with spaces and aren't "Grand Total")
                for i, row_data in enumerate(pdf_table_data[1:], 1):  # Skip header row
                    first_col_value = str(row_data[0]).strip()
                    # Faculty rows: don't start with spaces, aren't "Total" or "Grand Total"
                    if (not first_col_value.startswith('  ') and 
                        first_col_value not in ['Total', 'Grand Total'] and
                        first_col_value != ''):
                        table_style.extend([
                            ('BACKGROUND', (0, i), (-1, i), colors.steelblue),
                            ('TEXTCOLOR', (0, i), (-1, i), colors.white),
                            ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
                        ])
                
                demographics_table.setStyle(TableStyle(table_style))
                story.append(demographics_table)
                story.append(Spacer(1, 0.3*inch))
        
        # Term-based Analysis Summary for Multi-year
        if 'term_breakdown' in analysis_tables:
            table_data = analysis_tables['term_breakdown']
            story.append(Paragraph("Multi-Year Term Analysis Summary", styles['Heading3']))
            
            summary = table_data.get('summary', {})
            years_covered = summary.get('years_covered', [])
            term_analysis_text = (f"Term-by-term analysis covering {', '.join(years_covered)} shows enrollment patterns "
                                 f"across {summary.get('total_faculties', 'N/A')} faculties with {summary.get('total_students', 'N/A')} total student records. "
                                 f"This analysis reveals seasonal trends and faculty-specific participation patterns that inform strategic planning.")
            story.append(Paragraph(term_analysis_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("Note: Comprehensive detailed tables with complete breakdowns are available in the accompanying JSON analysis files.", 
                             styles['Italic']))
        story.append(Spacer(1, 0.5*inch))

    # Key insights section for multi-year analysis
    key_insights = pdf_data.get('key_insights', {})
    if key_insights:
        story.append(Paragraph("Key Multi-Year Insights", styles['Heading2']))
        for insight_key, insight_value in key_insights.items():
            if insight_value:
                # Handle both string and list values properly
                insight_title = insight_key.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{insight_title}:</b>", styles['Normal']))
                
                if isinstance(insight_value, list):
                    # If it's a list, display each item as a separate bullet point
                    for item in insight_value:
                        if item and isinstance(item, str):
                            story.append(Paragraph(f"  • {item}", styles['Normal']))
                else:
                    # If it's a string, display it directly
                    story.append(Paragraph(f"  {insight_value}", styles['Normal']))
                
                story.append(Spacer(1, 0.2*inch))
        story.append(Spacer(1, 0.5*inch))

    # Charts section - Enhanced for multi-year analysis with table visualizations
    story.append(Paragraph("Multi-Year Data Visualizations", styles['Heading2']))
    
    # Define chart priority order and display names for multi-year
    chart_priority = {
        'year_comparison': 'Year-over-Year Faculty Enrollment Comparison',
        'faculty_residency': 'Faculty and Residency Status Analysis',
        'table1_faculty_comparison_chart': 'Table 1: Faculty Enrollment Comparison Chart',
        'table3_academic_levels_chart': 'Table 3: Academic Level Distribution Chart',
        'gender_distribution_pie': 'Overall Gender Distribution',
        'gender_distribution_faculty': 'Gender Distribution by Faculty',
        'first_generation_participation': 'First Generation Student Participation',
        'ses_distribution': 'Socioeconomic Status Distribution',
        'indigenous_participation': 'Indigenous Student Participation',
        'regional_distribution': 'Regional Distribution of Students',
        'cdev_residency': 'CDEV Course Enrollment by Residency',
        'cdev_gender': 'CDEV Course Gender Distribution'
    }
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get all available chart files
        available_charts = []
        chart_files = pdf_data.get('charts', {})
        
        # Add charts from the charts mapping
        for chart_key, chart_file in chart_files.items():
            image_zip_path = f"charts/{chart_file}"
            if image_zip_path in zip_ref.namelist():
                available_charts.append((chart_key, chart_file, image_zip_path))
        
        # Also look for table visualization charts directly in charts folder
        for file_info in zip_ref.namelist():
            if file_info.startswith('charts/') and file_info.endswith('.png'):
                filename = file_info.split('/')[-1]
                # Check for table visualization charts
                if 'table1_faculty_comparison_chart' in filename or 'table3_academic_levels_chart' in filename:
                    chart_key = filename.replace('.png', '').split('_')[:-1]  # Remove date suffix
                    chart_key = '_'.join(chart_key)
                    if chart_key not in [c[0] for c in available_charts]:
                        available_charts.append((chart_key, filename, file_info))
        
        # Sort charts by priority
        def get_priority(chart_tuple):
            chart_key = chart_tuple[0]
            for i, priority_key in enumerate(chart_priority.keys()):
                if priority_key in chart_key:
                    return i
            return len(chart_priority)  # Put unrecognized charts at the end
        
        available_charts.sort(key=get_priority)
        
        # Add charts to PDF
        charts_added = 0
        for chart_key, chart_file, image_zip_path in available_charts:
            try:
                with zip_ref.open(image_zip_path) as image_file:
                    image_data = BytesIO(image_file.read())
                    
                    # Get display name
                    display_name = None
                    for priority_key, display_name_candidate in chart_priority.items():
                        if priority_key in chart_key:
                            display_name = display_name_candidate
                            break
                    
                    if not display_name:
                        display_name = chart_key.replace("_", " ").title()
                    
                    # Add year comparison context for specific charts
                    if ("enrollment" in chart_key.lower() and "comparison" in display_name.lower()) or \
                       ("faculty" in chart_key.lower() and "residency" in chart_key.lower()) or \
                       ("table" in display_name.lower()):
                        if years_analyzed:
                            display_name += f" ({' vs '.join(map(str, years_analyzed))})"
                    
                    story.append(Paragraph(display_name, styles['Heading3']))
                    story.append(Image(image_data, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 0.5*inch))
                    charts_added += 1
                    
            except Exception as e:
                print(f"Warning: Could not add chart {chart_key}: {str(e)}")
        
        print(f"DEBUG - Added {charts_added} charts to multi-year PDF")

    doc.build(story)
    print(f"SUCCESS: Multi-year PDF report has been generated: {output_path}")






