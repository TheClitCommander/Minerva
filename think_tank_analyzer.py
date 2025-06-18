#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Think Tank Analyzer

This script performs analysis on the Think Tank mode's performance and
provides insights for further optimization.
"""

import json
import logging
import argparse
import os
import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_results(results_file: str) -> Dict:
    """Load test results from the JSON file."""
    try:
        with open(results_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load test results: {e}")
        return {}

def analyze_model_selection(results: Dict) -> Dict[str, Any]:
    """Analyze model selection patterns from test results."""
    if not results or 'queries' not in results:
        return {}
    
    model_counts = Counter()
    query_types = defaultdict(list)
    model_by_query_type = defaultdict(Counter)
    
    for query_data in results['queries']:
        query = query_data.get('query', '')
        selected_model = query_data.get('selected_model', '')
        query_type = 'general'
        
        # Simple query type classification
        query_lower = query.lower()
        if any(term in query_lower for term in ['code', 'function', 'program', 'algorithm', 'debug']):
            query_type = 'technical'
        elif any(term in query_lower for term in ['creative', 'write', 'story', 'poem', 'imagine']):
            query_type = 'creative'
        elif any(term in query_lower for term in ['explain', 'why', 'how', 'reason', 'analyze']):
            query_type = 'reasoning'
        
        if selected_model:
            model_counts[selected_model] += 1
            query_types[query_type].append(query)
            model_by_query_type[query_type][selected_model] += 1
    
    return {
        'model_selection_counts': dict(model_counts),
        'query_types': {k: len(v) for k, v in query_types.items()},
        'model_by_query_type': {k: dict(v) for k, v in model_by_query_type.items()},
    }

def analyze_model_performance(results: Dict) -> Dict[str, Any]:
    """Analyze model performance metrics from test results."""
    if not results or 'queries' not in results:
        return {}
    
    model_scores = defaultdict(list)
    model_response_times = defaultdict(list)
    
    for query_data in results['queries']:
        selected_model = query_data.get('selected_model', '')
        score = query_data.get('score', 0)
        response_time = query_data.get('response_time', 0)
        
        if selected_model:
            model_scores[selected_model].append(score)
            model_response_times[selected_model].append(response_time)
    
    # Calculate average scores and response times
    avg_scores = {
        model: sum(scores) / len(scores) if scores else 0 
        for model, scores in model_scores.items()
    }
    
    avg_response_times = {
        model: sum(times) / len(times) if times else 0 
        for model, times in model_response_times.items()
    }
    
    return {
        'average_scores': avg_scores,
        'average_response_times': avg_response_times,
    }

def generate_text_charts(analysis: Dict, output_dir: str) -> Dict[str, str]:
    """Generate text-based charts for the analysis results."""
    chart_files = {}
    
    # Model selection frequency chart
    model_counts = analysis.get('model_selection_counts', {})
    if model_counts:
        chart_path = os.path.join(output_dir, 'model_selection_chart.txt')
        with open(chart_path, 'w') as f:
            f.write("Model Selection Frequency:\n\n")
            max_count = max(model_counts.values())
            for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
                bar_length = int(40 * count / max_count) if max_count > 0 else 0
                bar = '#' * bar_length
                f.write(f"{model.ljust(10)} | {bar} {count}\n")
        chart_files['model_selection'] = chart_path
    
    # Model by query type chart
    model_by_query_type = analysis.get('model_by_query_type', {})
    if model_by_query_type:
        chart_path = os.path.join(output_dir, 'model_by_query_type_chart.txt')
        with open(chart_path, 'w') as f:
            f.write("Model Usage by Query Type:\n\n")
            for query_type, counts in model_by_query_type.items():
                f.write(f"\n{query_type.upper()} QUERIES:\n")
                max_count = max(counts.values()) if counts else 0
                for model, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                    bar_length = int(30 * count / max_count) if max_count > 0 else 0
                    bar = '#' * bar_length
                    f.write(f"{model.ljust(10)} | {bar} {count}\n")
        chart_files['model_by_query_type'] = chart_path
    
    # Model scores chart
    avg_scores = analysis.get('average_scores', {})
    if avg_scores:
        chart_path = os.path.join(output_dir, 'model_scores_chart.txt')
        with open(chart_path, 'w') as f:
            f.write("Average Model Quality Scores:\n\n")
            for model, score in sorted(avg_scores.items(), key=lambda x: x[1], reverse=True):
                bar_length = int(40 * score)
                bar = '#' * bar_length
                f.write(f"{model.ljust(10)} | {bar} {score:.2f}\n")
        chart_files['model_scores'] = chart_path
    
    return chart_files

def generate_report(results: Dict, analysis: Dict, output_dir: str):
    """Generate a markdown report with the analysis results."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_path = os.path.join(output_dir, "think_tank_analysis_report.md")
    
    with open(report_path, "w") as f:
        f.write(f"# Think Tank Mode Analysis Report\n\n")
        f.write(f"Generated: {timestamp}\n\n")
        
        # Overall statistics
        f.write("## Overall Statistics\n\n")
        f.write(f"- Total queries tested: {results.get('total_queries', 0)}\n")
        f.write(f"- Successful responses: {results.get('successful_responses', 0)}\n")
        f.write(f"- Failed responses: {results.get('failed_responses', 0)}\n")
        f.write(f"- Success rate: {results.get('success_percentage', 0):.1f}%\n")
        f.write(f"- Average response time: {results.get('average_response_time', 0):.3f}s\n\n")
        
        # Model selection
        model_counts = analysis.get('model_selection_counts', {})
        f.write("## Model Selection\n\n")
        f.write("| Model | Selection Count | Selection Percentage |\n")
        f.write("|-------|----------------|----------------------|\n")
        total_selections = sum(model_counts.values())
        for model, count in model_counts.items():
            percentage = (count / total_selections * 100) if total_selections > 0 else 0
            f.write(f"| {model} | {count} | {percentage:.1f}% |\n")
        f.write("\n")
        
        # Query type breakdown
        query_types = analysis.get('query_types', {})
        f.write("## Query Type Distribution\n\n")
        f.write("| Query Type | Count | Percentage |\n")
        f.write("|------------|-------|------------|\n")
        total_queries = sum(query_types.values())
        for query_type, count in query_types.items():
            percentage = (count / total_queries * 100) if total_queries > 0 else 0
            f.write(f"| {query_type} | {count} | {percentage:.1f}% |\n")
        f.write("\n")
        
        # Model performance
        avg_scores = analysis.get('average_scores', {})
        avg_response_times = analysis.get('average_response_times', {})
        f.write("## Model Performance\n\n")
        f.write("| Model | Average Quality Score | Average Response Time (s) |\n")
        f.write("|-------|----------------------|---------------------------|\n")
        for model in avg_scores.keys():
            score = avg_scores.get(model, 0)
            response_time = avg_response_times.get(model, 0)
            f.write(f"| {model} | {score:.2f} | {response_time:.3f} |\n")
        f.write("\n")
        
        # Model usage by query type
        model_by_query_type = analysis.get('model_by_query_type', {})
        f.write("## Model Usage by Query Type\n\n")
        
        for query_type, model_counts in model_by_query_type.items():
            f.write(f"### {query_type.capitalize()} Queries\n\n")
            f.write("| Model | Count | Percentage |\n")
            f.write("|-------|-------|------------|\n")
            
            total = sum(model_counts.values())
            for model, count in model_counts.items():
                percentage = (count / total * 100) if total > 0 else 0
                f.write(f"| {model} | {count} | {percentage:.1f}% |\n")
            f.write("\n")
        
        f.write("## Text Charts\n\n")
        f.write("Text-based charts have been saved to the output directory:\n\n")
        f.write("- Model Selection Frequency (model_selection_chart.txt)\n")
        f.write("- Model Usage by Query Type (model_by_query_type_chart.txt)\n")
        f.write("- Average Model Quality Scores (model_scores_chart.txt)\n\n")
        
        f.write("## Recommendations\n\n")
        
        # Generate some basic recommendations based on analysis
        if avg_scores:
            best_model = max(avg_scores.items(), key=lambda x: x[1])[0]
            worst_model = min(avg_scores.items(), key=lambda x: x[1])[0]
            
            f.write(f"- {best_model} achieved the highest average quality score and may be prioritized for general queries.\n")
            f.write(f"- {worst_model} achieved the lowest average quality score and may benefit from tuning or de-prioritization.\n")
        
        # Model recommendations by query type
        for query_type, model_counts in model_by_query_type.items():
            if model_counts:
                top_model = max(model_counts.items(), key=lambda x: x[1])[0]
                f.write(f"- For {query_type} queries, {top_model} was selected most frequently and could be prioritized for this type.\n")
        
    logger.info(f"Analysis report generated at {report_path}")
    return report_path

def main():
    parser = argparse.ArgumentParser(description="Analyze Think Tank mode test results")
    parser.add_argument(
        "--results", 
        default="think_tank_test_results.json", 
        help="Path to the test results JSON file"
    )
    parser.add_argument(
        "--output", 
        default="think_tank_analysis", 
        help="Output directory for analysis results"
    )
    args = parser.parse_args()

    logger.info(f"Loading test results from {args.results}")
    results = load_test_results(args.results)
    
    if not results:
        logger.error("No valid test results found. Exiting.")
        return
    
    logger.info("Analyzing model selection patterns")
    model_selection_analysis = analyze_model_selection(results)
    
    logger.info("Analyzing model performance")
    model_performance_analysis = analyze_model_performance(results)
    
    # Combine analyses
    analysis = {**model_selection_analysis, **model_performance_analysis}
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # Generate text charts
    logger.info("Generating text charts")
    chart_files = generate_text_charts(analysis, args.output)
    
    # Generate report
    logger.info("Generating analysis report")
    report_path = generate_report(results, analysis, args.output)
    
    logger.info(f"Analysis complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()
