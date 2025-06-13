-- Core rule engine functions

-- Function to fire rules and return new edges
CREATE OR REPLACE FUNCTION core_rule_fire()
RETURNS TABLE (new_edge_id INTEGER) AS $$
DECLARE
    rule_record RECORD;
    created_edge_id INTEGER;
    rule_parts TEXT[];
    idx INTEGER;
    src_class TEXT;
    tgt_class TEXT;
    src_node INTEGER;
    tgt_node INTEGER;
BEGIN
    -- Loop through all active rules
    FOR rule_record IN 
        SELECT rule_id, rule_body 
        FROM rules 
        WHERE is_active = true
    LOOP
        RAISE NOTICE 'Processing rule: %', rule_record.rule_body;
        
        -- Parse rule body (format: "?x rdf:type Dog → ?x rdf:type Mammal")
        -- For now, we'll handle simple subclass rules
        IF rule_record.rule_body LIKE '%rdf:type%→%rdf:type%' THEN
            -- Split rule into parts by →
            rule_parts := string_to_array(rule_record.rule_body, '→');
            RAISE NOTICE 'Rule parts: %', rule_parts;
            
            -- For each adjacent pair in the chain
            FOR idx IN 1..array_length(rule_parts, 1) - 1 LOOP
                -- Extract source and target classes
                src_class := TRIM(SPLIT_PART(rule_parts[idx], 'rdf:type', 2));
                tgt_class := TRIM(SPLIT_PART(rule_parts[idx + 1], 'rdf:type', 2));
                
                RAISE NOTICE 'Processing chain: % → %', src_class, tgt_class;
                
                -- Find all entities that are of the source class
                FOR src_node IN 
                    SELECT DISTINCT n1.node_id
                    FROM nodes n1
                    JOIN edges e1 ON e1.source_node_id = n1.node_id
                    JOIN nodes n2 ON e1.target_node_id = n2.node_id
                    WHERE n2.properties->>'label' = src_class
                    AND e1.edge_type = 'rdf:type'
                LOOP
                    -- Get the target class node
                    SELECT node_id INTO tgt_node
                    FROM nodes
                    WHERE node_type = 'Class'
                    AND properties->>'label' = tgt_class;
                    
                    -- Create new edge if it doesn't exist
                    INSERT INTO edges (source_node_id, target_node_id, edge_type)
                    SELECT 
                        src_node,
                        tgt_node,
                        'rdf:type'
                    WHERE NOT EXISTS (
                        -- Avoid duplicates
                        SELECT 1 FROM edges e2
                        WHERE e2.source_node_id = src_node
                        AND e2.target_node_id = tgt_node
                        AND e2.edge_type = 'rdf:type'
                    )
                    RETURNING edge_id INTO created_edge_id;
                    
                    -- Return the new edge ID
                    IF created_edge_id IS NOT NULL THEN
                        RAISE NOTICE 'Created new edge: %', created_edge_id;
                        new_edge_id := created_edge_id;
                        RETURN NEXT;
                    END IF;
                END LOOP;
            END LOOP;
        END IF;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql; 