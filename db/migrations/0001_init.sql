-- IndicRAG schema v1 (docs/02). Plain SQL migrations; applied in filename order by scripts/db_load.py.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz DEFAULT now());

CREATE TABLE documents (
    id            text PRIMARY KEY,            -- source_id
    url           text NOT NULL,
    title         text,
    lang          text NOT NULL CHECK (lang IN ('en','hi','kn')),
    role          text NOT NULL DEFAULT 'candidate',   -- labelled | distractor | candidate
    licence_note  text,
    redistribute  boolean NOT NULL DEFAULT false,
    fetched_at    timestamptz,
    sha256        text NOT NULL,               -- raw bytes
    parsed_sha256 text NOT NULL,
    parser_version text NOT NULL
);

CREATE TABLE chunks (
    id            text PRIMARY KEY,            -- deterministic chunk_id
    doc_id        text NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parsed_sha256 text NOT NULL,
    lang          text NOT NULL,
    section_path  text NOT NULL DEFAULT '',
    char_start    integer NOT NULL,
    char_end      integer NOT NULL CHECK (char_end > char_start),
    strategy      text NOT NULL,
    budget        integer NOT NULL,
    counter       text NOT NULL,
    text          text NOT NULL CHECK (char_length(text) = char_end - char_start),
    -- Postgres ships no Hindi/Kannada text-search config: 'simple' (no stemming). Lexical quality is measured, not assumed.
    tsv           tsvector GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED
);
CREATE INDEX chunks_doc_idx  ON chunks (doc_id);
CREATE INDEX chunks_lang_idx ON chunks (lang);
CREATE INDEX chunks_tsv_idx  ON chunks USING gin (tsv);

-- One row per (chunk, embedding model); dimension is a property of the model, so no fixed-dim column on chunks.
-- An HNSW index is created per model/dimension at embed time (see docs/14), e.g.
--   CREATE INDEX ON chunk_embeddings USING hnsw ((embedding::vector(384)) vector_cosine_ops) WHERE model = '<name>';
CREATE TABLE chunk_embeddings (
    chunk_id  text NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    model     text NOT NULL,
    dim       integer NOT NULL,
    embedding vector NOT NULL,
    PRIMARY KEY (chunk_id, model)
);

INSERT INTO schema_migrations VALUES ('0001_init') ON CONFLICT DO NOTHING;
