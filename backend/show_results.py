#!/usr/bin/env python3
"""
Display WIL Data Analysis Results

Read the generated analysis summary and display key information
"""

import json
import os
from datetime import datetime


def show_results():
    print("📊 WIL Data Analysis Results")
    print("=" * 60)
    
    # Find the latest analysis result file
    reports_dir = "../reports"
    summary_files = [f for f in os.listdir(reports_dir) if f.startswith('analysis_summary_') and f.endswith('.json')]
    
    if not summary_files:
        print("❌ No analysis result files found")
        return
    
    # Use the latest file
    latest_file = sorted(summary_files)[-1]
    summary_path = os.path.join(reports_dir, latest_file)
    
    print(f"📄 Analysis file: {latest_file}")
    print(f"📁 Reports directory: {os.path.abspath(reports_dir)}")
    
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Display basic statistics
        if 'key_statistics' in data:
            stats = data['key_statistics']
            print(f"\n📈 Key Statistics")
            print("-" * 30)
            print(f"👥 Total Students: {stats.get('total_students', 0):,}")
            print(f"🏛️ Total Faculties: {stats.get('total_faculties', 0)}")
            print(f"📚 Total Courses: {stats.get('total_courses', 0):,}")
        
        # Display faculty distribution
        if 'faculty_breakdown' in data:
            faculty = data['faculty_breakdown']
            print(f"\n🏛️ Faculty Distribution (Top 5)")
            print("-" * 30)
            # Handle different data types
            faculty_items = []
            for name, count in faculty.items():
                if isinstance(count, (int, float)):
                    faculty_items.append((name, count))
            
            sorted_faculty = sorted(faculty_items, key=lambda x: x[1], reverse=True)
            for i, (name, count) in enumerate(sorted_faculty[:5], 1):
                print(f"{i}. {name}: {count:,} students")
        
        # Display gender distribution
        if 'gender_breakdown' in data:
            gender = data['gender_breakdown']
            print(f"\n👥 Gender Distribution")
            print("-" * 30)
            for key, value in gender.items():
                if isinstance(value, (int, float)):
                    print(f"• {key}: {value:.1f}%")
        
        # Display residency status distribution
        if 'residency_breakdown' in data:
            residency = data['residency_breakdown']
            print(f"\n🌏 Residency Status Distribution")
            print("-" * 30)
            for key, value in residency.items():
                if isinstance(value, (int, float)):
                    print(f"• {key}: {value:.1f}%")
        
        # Display key insights
        if 'key_insights' in data:
            insights = data['key_insights']
            if 'program_overview' in insights:
                print(f"\n💡 Program Overview")
                print("-" * 30)
                for insight in insights['program_overview'][:3]:
                    print(f"• {insight}")
        
        # List generated chart files
        print(f"\n📊 Generated Chart Files")
        print("-" * 30)
        chart_files = [f for f in os.listdir(reports_dir) if f.endswith('.png')]
        chart_files.sort()
        
        chart_descriptions = {
            'year_comparison': '📈 Faculty Enrollment Overview',
            'faculty_residency': '🏛️ Faculty Residency Distribution', 
            'gender_distribution_pie': '👥 Gender Distribution Pie Chart',
            'gender_distribution_faculty': '👥 Faculty Gender Distribution',
            'first_generation_participation': '🎓 First Generation Participation',
            'ses_distribution': '💰 Socioeconomic Status Distribution',
            'indigenous_participation': '🌏 Indigenous Participation',
            'regional_distribution': '📍 Regional Distribution',
            'cdev_residency': '💼 CDEV Course Residency Status',
            'cdev_gender': '💼 CDEV Course Gender Distribution'
        }
        
        for chart_file in chart_files:
            file_size = os.path.getsize(os.path.join(reports_dir, chart_file)) // 1024
            chart_type = chart_file.split('_20250701.png')[0]
            description = chart_descriptions.get(chart_type, '📊 Data Chart')
            print(f"• {description}: {chart_file} ({file_size} KB)")
        
        print(f"\n🎯 Usage Guide")
        print("-" * 30)
        print(f"1. View Charts: Open {os.path.abspath(reports_dir)} directory")
        print(f"2. All charts are high-resolution PNG format, suitable for presentations")
        print(f"3. The analysis summary JSON file contains complete statistical data")
        print(f"4. These charts can be directly used in presentations and reports")
        
        print(f"\n✅ Analysis completed! Generated {len(chart_files)} chart files")
        
    except Exception as e:
        print(f"❌ Failed to read analysis results: {e}")


if __name__ == "__main__":
    show_results()