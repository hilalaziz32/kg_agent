import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
import sys

# Add the project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from system1.executor import RuleExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BenchmarkRunner:
    def __init__(self, db_connection_string: str):
        self.executor = RuleExecutor(db_connection_string)
        self.results_dir = os.path.join(PROJECT_ROOT, "logs")
        os.makedirs(self.results_dir, exist_ok=True)
        
    def run_owl_benchmarks(self):
        """Run all OWL-related benchmarks."""
        benchmarks = {
            'subclassing': os.path.join(PROJECT_ROOT, 'benchmarks', 'owl', 'subclass - Sheet1.csv'),
            # Add more OWL benchmarks here as they're created
        }
        
        results = {}
        for benchmark_name, csv_path in benchmarks.items():
            logger.info(f"Running benchmark: {benchmark_name}")
            try:
                if not os.path.exists(csv_path):
                    raise FileNotFoundError(f"Benchmark file not found: {csv_path}")
                benchmark_results = self.executor.run_benchmark(csv_path)
                results[benchmark_name] = benchmark_results
            except Exception as e:
                logger.error(f"Error running {benchmark_name}: {str(e)}")
                results[benchmark_name] = {'error': str(e)}
        
        return results
    
    def generate_report(self, results: Dict[str, Any]):
        """Generate a markdown report of benchmark results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.results_dir, f"benchmark_report_{timestamp}.md")
        
        with open(report_path, 'w') as f:
            f.write("# Knowledge Graph Reasoning Benchmarks\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for benchmark_name, benchmark_results in results.items():
                f.write(f"## {benchmark_name}\n\n")
                
                if isinstance(benchmark_results, dict) and 'error' in benchmark_results:
                    f.write(f"Error: {benchmark_results['error']}\n\n")
                    continue
                
                total_tests = len(benchmark_results)
                passed_tests = sum(1 for r in benchmark_results if r.get('passed', False))
                
                f.write(f"Total Tests: {total_tests}\n")
                f.write(f"Passed: {passed_tests}\n")
                f.write(f"Failed: {total_tests - passed_tests}\n\n")
                
                f.write("### Detailed Results\n\n")
                for result in benchmark_results:
                    f.write(f"#### Test {result['test_id']}\n")
                    f.write(f"- Status: {'✅ PASS' if result.get('passed', False) else '❌ FAIL'}\n")
                    if 'error' in result:
                        f.write(f"- Error: {result['error']}\n")
                    f.write(f"- Expected: {result.get('expected_output', 'N/A')}\n")
                    f.write(f"- Actual: {result.get('actual_output', 'N/A')}\n\n")
        
        logger.info(f"Report generated: {report_path}")
        return report_path

def main():
    # Initialize runner with database connection
    runner = BenchmarkRunner("dbname=kg_benchmark user=postgres password=postgres")
    
    try:
        # Run benchmarks
        results = runner.run_owl_benchmarks()
        
        # Generate report
        report_path = runner.generate_report(results)
        
        # Save raw results
        with open(os.path.join(runner.results_dir, "system1_pass_fail.json"), 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Benchmark execution completed. Report: {report_path}")
        
    finally:
        runner.executor.close()

if __name__ == "__main__":
    main() 