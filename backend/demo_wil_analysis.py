#!/usr/bin/env python3
"""
WIL DAta Analysis Demo Tool
Uses sample_data/sampledata.csv for analysis and outputs results to reports/ directory.

"""

import sys
import os
from datetime import datetime
from app.services.visualization import WILReportAnalyzer


def main():
    print("🎓 WIL Data Analysis Demo")
    print("=" * 50)
    
    # Data file paths
    data_file = "../sample_data/sampledata.csv"
    output_dir = "../reports"
    
    # Check if data file exists
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        return
    
    print(f"📊 Data file: {data_file}")
    print(f"📁 Output directory: {output_dir}")
    
    try:
        print("\n⏳ Starting analysis...")
        
        # Create analyzer
        analyzer = WILReportAnalyzer(data_file, output_dir)
        
        # Load data
        print("1. 📥 Loading data...")
        data = analyzer.load_data()
        print(f"   ✅ Successfully loaded {len(data):,} records")
        
        # Generate analysis summary
        print("2. 📊 Generating analysis summary...")
        summary = analyzer.generate_analysis_summary()
        
        if summary and 'key_statistics' in summary:
            stats = summary['key_statistics']
            print(f"   📈 Total students: {stats.get('total_students', 'N/A'):,}")
            print(f"   🏛️ Total faculties: {stats.get('total_faculties', 'N/A')}")
            print(f"   📚 Total courses: {stats.get('total_courses', 'N/A'):,}")
        
        # Generate all charts
        print("3. 📈 Generating charts...")
        charts = analyzer.generate_all_charts()
        
        # Count generated charts
        total_charts = 0
        for category, chart_list in charts.items():
            if isinstance(chart_list, list):
                total_charts += len(chart_list)
                if chart_list:
                    print(f"   📊 {category}: {len(chart_list)} charts")
        
        print(f"   ✅ Total charts generated: {total_charts}")
        
        print("\n🎉 Analysis completed!")
        print("=" * 50)
        print(f"📂 Results saved to: {os.path.abspath(output_dir)}")
        print("💡 You can view the chart files in the reports/ directory")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()