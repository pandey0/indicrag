.PHONY: test ingest ingest-myscheme discover-myscheme chunk db-up db-load
test:
	python3 -m pytest -q
ingest:            ## fetch+parse the candidate sources (set TESSERACT_BIN/TESSDATA_PREFIX for OCR)
	python3 -m src.ingest run
discover-myscheme: ## enumerate myScheme scheme pages (headless Chrome; CHROME_BIN overrides /usr/bin/google-chrome)
	python3 -m src.ingest.discover_myscheme --pages 30 --out data/sources_myscheme.csv
ingest-myscheme:
	python3 -m src.ingest run --sources data/sources_myscheme.csv

chunk:
	python3 -m src.chunk build --strategy fixed --budget 512 --overlap 64

# local pgvector for development (reuses an already-pulled Postgres image; throwaway password, localhost only)
db-up:
	docker run -d --name indicrag_pg -e POSTGRES_PASSWORD=dev -p 127.0.0.1:54329:5432 ghcr.io/supabase/postgres:17.11.0.004
db-load:
	DATABASE_URL=postgresql://postgres:dev@localhost:54329/postgres python3 scripts/db_load.py data/chunks/fixed_512_64.jsonl
