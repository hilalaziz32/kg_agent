# Knowledge Graph Reasoning Benchmarks

Generated: 2025-06-13 16:32:18

## subclassing

Total Tests: 5
Passed: 0
Failed: 5

### Detailed Results

#### Test SUB-001
- Status: ❌ FAIL
- Error: column reference "source_node_id" is ambiguous
LINE 9:                         WHERE e.source_node_id = source_node...
                                                         ^
DETAIL:  It could refer to either a PL/pgSQL variable or a table column.
QUERY:  INSERT INTO edges (source_node_id, target_node_id, edge_type)
                    SELECT 
                        source_node_id,
                        target_node_id,
                        'rdf:type'
                    WHERE NOT EXISTS (
                        -- Avoid duplicates
                        SELECT 1 FROM edges e
                        WHERE e.source_node_id = source_node_id
                        AND e.target_node_id = target_node_id
                        AND e.edge_type = 'rdf:type'
                    )
                    RETURNING edge_id
CONTEXT:  PL/pgSQL function core_rule_fire() line 51 at SQL statement

- Expected: N/A
- Actual: N/A

#### Test SUB-002
- Status: ❌ FAIL
- Error: current transaction is aborted, commands ignored until end of transaction block

- Expected: N/A
- Actual: N/A

#### Test SUB-003
- Status: ❌ FAIL
- Error: current transaction is aborted, commands ignored until end of transaction block

- Expected: N/A
- Actual: N/A

#### Test SUB-004
- Status: ❌ FAIL
- Error: current transaction is aborted, commands ignored until end of transaction block

- Expected: N/A
- Actual: N/A

#### Test SUB-005
- Status: ❌ FAIL
- Error: current transaction is aborted, commands ignored until end of transaction block

- Expected: N/A
- Actual: N/A

