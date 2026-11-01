.PHONY: test ingest ingest-myscheme discover-myscheme chunk
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
