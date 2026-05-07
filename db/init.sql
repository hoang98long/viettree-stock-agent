CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY,
    symbol VARCHAR(16) NOT NULL,
    decision JSONB NOT NULL,
    alerts JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_symbol_created_at
    ON analysis_runs (symbol, created_at DESC);
