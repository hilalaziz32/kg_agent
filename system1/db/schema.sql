-- Knowledge Graph Schema
-- Core tables for nodes, edges, rules, and tokens

-- Nodes table
CREATE TABLE nodes (
    node_id SERIAL PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Edges table
CREATE TABLE edges (
    edge_id SERIAL PRIMARY KEY,
    source_node_id INTEGER REFERENCES nodes(node_id),
    target_node_id INTEGER REFERENCES nodes(node_id),
    edge_type VARCHAR(50) NOT NULL,
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rules table
CREATE TABLE rules (
    rule_id SERIAL PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL,
    rule_body TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tokens table for rule matching
CREATE TABLE tokens (
    token_id SERIAL PRIMARY KEY,
    token_type VARCHAR(50) NOT NULL,
    token_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_edges_type ON edges(edge_type);
CREATE INDEX idx_edges_source ON edges(source_node_id);
CREATE INDEX idx_edges_target ON edges(target_node_id);
CREATE INDEX idx_rules_type ON rules(rule_type);
CREATE INDEX idx_tokens_type ON tokens(token_type); 