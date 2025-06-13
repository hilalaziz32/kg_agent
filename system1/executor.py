import psycopg2
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleExecutor:
    def __init__(self, db_connection_string: str):
        self.conn = psycopg2.connect(db_connection_string)
        self.cur = self.conn.cursor()
        
    def ensure_class_node(self, class_label: str) -> int:
        """Ensure a class node exists and return its ID."""
        self.cur.execute("""
            INSERT INTO nodes (node_type, properties)
            SELECT 'Class', %s
            WHERE NOT EXISTS (
                SELECT 1 FROM nodes
                WHERE node_type = 'Class'
                AND properties->>'label' = %s
            )
            RETURNING node_id
        """, (json.dumps({'label': class_label}), class_label))
        
        result = self.cur.fetchone()
        if result:
            node_id = result[0]
        else:
            # If no insert happened, get the existing node's ID
            self.cur.execute("""
                SELECT node_id FROM nodes
                WHERE node_type = 'Class'
                AND properties->>'label' = %s
            """, (class_label,))
            node_id = self.cur.fetchone()[0]
            
        self.conn.commit()
        return node_id
        
    def load_benchmark_data(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load benchmark data from CSV file."""
        import csv
        test_cases = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                test_cases.append(row)
        return test_cases

    def ingest_facts(self, test_case: Dict[str, Any]) -> None:
        """Convert input facts into nodes and edges."""
        # Parse input facts (format: "(subject, predicate, object)")
        facts_str = test_case['Input Facts'].strip()
        logger.info(f"Raw input facts: '{facts_str}'")
        
        facts = facts_str.strip('()').split(',')
        subject, predicate, obj = [f.strip() for f in facts]
        
        logger.info(f"Parsed facts - Subject: '{subject}', Predicate: '{predicate}', Object: '{obj}'")
        
        # Insert subject node
        self.cur.execute("""
            INSERT INTO nodes (node_type, properties) 
            VALUES ('Entity', %s) RETURNING node_id
        """, (json.dumps({'label': subject}),))
        subject_id = self.cur.fetchone()[0]
        
        # Ensure object class exists
        object_id = self.ensure_class_node(obj)
        
        # Insert edge
        self.cur.execute("""
            INSERT INTO edges (source_node_id, target_node_id, edge_type)
            VALUES (%s, %s, %s)
        """, (subject_id, object_id, predicate))
        
        logger.info(f"Created edge: {subject_id} --{predicate}--> {object_id}")
        self.conn.commit()

    def register_rule(self, rule_example: str) -> None:
        """Register rules from the benchmark, handling multiple rules separated by semicolons."""
        # Split multiple rules at semicolons
        for part in rule_example.split(';'):
            body = part.strip()
            if body:
                # Extract all classes mentioned in the rule
                parts = body.split('→')
                for part in parts:
                    if 'rdf:type' in part:
                        class_label = part.split('rdf:type')[1].strip()
                        self.ensure_class_node(class_label)
                
                # Register the rule
                self.cur.execute("""
                    INSERT INTO rules (rule_type, rule_body)
                    VALUES ('OWL_SUBCLASS', %s)
                """, (body,))
                logger.info(f"Registered rule: {body}")
        
        self.conn.commit()

    def fire_rules(self) -> List[Dict[str, Any]]:
        """Fire rules and return new inferences."""
        # Add debug info before firing
        self.cur.execute("SELECT COUNT(*) FROM rules WHERE is_active = true")
        rule_count = self.cur.fetchone()[0]
        logger.info(f"About to fire {rule_count} active rules")
        
        self.cur.execute("SELECT rule_body FROM rules WHERE is_active = true")
        rules = self.cur.fetchall()
        for rule in rules:
            logger.info(f"Active rule: {rule[0]}")
        
        # Call core_rule_fire() stored procedure with proper syntax
        logger.info("Calling core_rule_fire()...")
        self.cur.execute("SELECT * FROM core_rule_fire()")
        new_edges = self.cur.fetchall()
        
        logger.info(f"Rule firing returned {len(new_edges) if new_edges else 0} new edges: {new_edges}")
        
        # Convert to list of dicts for easier handling
        results = []
        if new_edges:  # Only process if we got edges back
            for edge_id in new_edges:
                logger.info(f"Processing edge_id: {edge_id}")
                self.cur.execute("""
                    SELECT 
                        n1.properties->>'label' as source, 
                        n2.properties->>'label' as target,
                        e.edge_type
                    FROM edges e
                    JOIN nodes n1 ON e.source_node_id = n1.node_id
                    JOIN nodes n2 ON e.target_node_id = n2.node_id
                    WHERE e.edge_id = %s
                """, (edge_id[0],))  # edge_id is a tuple, get first element
                result = self.cur.fetchone()
                if result:
                    # Create dictionary with proper column names
                    edge_dict = {
                        'source': result[0],
                        'edge_type': result[2],
                        'target': result[1]
                    }
                    results.append(edge_dict)
                    logger.info(f"New inference: {edge_dict}")
                else:
                    logger.warning(f"Could not find edge with ID {edge_id[0]}")
            
        return results

    def parse_expected(self, expected_str: str) -> Set[Tuple[str,str,str]]:
        import re
        triples = set()
        for match in re.findall(r'\(\s*([^)]*?)\s*\)', expected_str):
            parts = [x.strip() for x in match.split(',')]
            if len(parts) != 3:
                raise ValueError(f"Can't parse expected triple: {match}")
            triples.add(tuple(parts))
        return triples

    def verify_output(self, test_case: Dict[str, Any], actual_output: List[Dict[str, Any]]) -> bool:
        """Verify if actual output matches all expected outputs."""
        expected_triples = self.parse_expected(test_case['Expected Output'])
        actual_triples = {(r['source'], r['edge_type'], r['target']) for r in actual_output}
        
        logger.info(f"Expected triples: {expected_triples}")
        logger.info(f"Actual triples: {actual_triples}")
        
        # Check if all expected triples are in actual triples
        missing = expected_triples - actual_triples
        if missing:
            logger.info(f"Missing triples: {missing}")
        return not missing  # Return True if no missing triples

    def run_benchmark(self, csv_path: str) -> Dict[str, Any]:
        """Run full benchmark pipeline."""
        test_cases = self.load_benchmark_data(csv_path)
        results = []
        
        # Clear all data before starting
        try:
            self.cur.execute("TRUNCATE nodes, edges, rules CASCADE")
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to clear database: {str(e)}")
            raise
        
        for test_case in test_cases:
            try:
                logger.info(f"\nProcessing test case {test_case['Test ID']}")
                logger.info(f"Input facts: {test_case['Input Facts']}")
                logger.info(f"Rule: {test_case['R²L Rule Example']}")
                logger.info(f"Expected output: {test_case['Expected Output']}")
                
                # Run pipeline
                self.ingest_facts(test_case)
                self.register_rule(test_case['R²L Rule Example'])
                actual_output = self.fire_rules()
                passed = self.verify_output(test_case, actual_output)
                
                # Commit successful test
                self.conn.commit()
                
                results.append({
                    'test_id': test_case['Test ID'],
                    'passed': passed,
                    'actual_output': actual_output,
                    'expected_output': test_case['Expected Output']
                })
                
            except Exception as e:
                # Rollback failed test
                self.conn.rollback()
                logger.error(f"Error in test {test_case['Test ID']}: {str(e)}")
                results.append({
                    'test_id': test_case['Test ID'],
                    'passed': False,
                    'error': str(e)
                })
        
        return results

    def close(self):
        """Close database connection."""
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    # Example usage
    executor = RuleExecutor("dbname=kg_benchmark user=postgres password=postgres")
    results = executor.run_benchmark("benchmarks/owl/subclassing.csv")
    
    # Save results
    with open("logs/system1_pass_fail.json", "w") as f:
        json.dump(results, f, indent=2)
    
    executor.close() 