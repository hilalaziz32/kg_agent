# Knowledge Graph Reasoning Benchmarks

Generated: 2025-06-13 17:34:47

## subclassing

Total Tests: 5
Passed: 5
Failed: 0

### Detailed Results

#### Test SUB-001
- Status: ✅ PASS
- Expected: (Rex, rdf:type, Mammal)
- Actual: [{'source': 'Rex', 'edge_type': 'rdf:type', 'target': 'Mammal'}]

#### Test SUB-002
- Status: ✅ PASS
- Expected: (Ferrari1, rdf:type, Vehicle)
- Actual: [{'source': 'Ferrari1', 'edge_type': 'rdf:type', 'target': 'Vehicle'}]

#### Test SUB-003
- Status: ✅ PASS
- Expected: (Fluffy, rdf:type, Dog), (Fluffy, rdf:type, Mammal)
- Actual: [{'source': 'Fluffy', 'edge_type': 'rdf:type', 'target': 'Dog'}, {'source': 'Fluffy', 'edge_type': 'rdf:type', 'target': 'Mammal'}]

#### Test SUB-004
- Status: ✅ PASS
- Expected: (Smith, rdf:type, Faculty)
- Actual: [{'source': 'Smith', 'edge_type': 'rdf:type', 'target': 'Faculty'}]

#### Test SUB-005
- Status: ✅ PASS
- Expected: (MacBook, rdf:type, Computer), (MacBook, rdf:type, Electronics)
- Actual: [{'source': 'MacBook', 'edge_type': 'rdf:type', 'target': 'Computer'}, {'source': 'MacBook', 'edge_type': 'rdf:type', 'target': 'Electronics'}]

