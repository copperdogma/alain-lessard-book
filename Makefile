BUNDLED_PYTHON := /Users/cam/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
PYTHON ?= $(shell if [ -x "$(BUNDLED_PYTHON)" ]; then echo "$(BUNDLED_PYTHON)"; else command -v python3; fi)
SCAN_INPUT ?= input/raw scans/main book

.PHONY: skills-sync skills-check methodology-compile methodology-check scan-intake-report process-scans build-image-pdf ocr-pdf archival-image-pdf archival-pdf scan-pdf-all render-pdf-checks validate-pdf

skills-sync:
	./scripts/sync-agent-skills.sh

skills-check:
	./scripts/sync-agent-skills.sh --check

methodology-compile:
	$(PYTHON) scripts/methodology_graph.py build

methodology-check:
	$(PYTHON) scripts/methodology_graph.py check

scan-intake-report:
	$(PYTHON) scripts/inspect_scan_set.py "$(SCAN_INPUT)"

process-scans:
	$(PYTHON) scripts/process_book_scans.py process

build-image-pdf: process-scans
	$(PYTHON) scripts/process_book_scans.py build-image-pdf --profile distribution

ocr-pdf: build-image-pdf
	$(PYTHON) scripts/process_book_scans.py ocr --profile distribution

archival-image-pdf: process-scans
	$(PYTHON) scripts/process_book_scans.py build-image-pdf --profile archival

archival-pdf: archival-image-pdf
	$(PYTHON) scripts/process_book_scans.py ocr --profile archival

scan-pdf-all: ocr-pdf archival-pdf

render-pdf-checks:
	$(PYTHON) scripts/process_book_scans.py render-checks

validate-pdf:
	$(PYTHON) scripts/process_book_scans.py validate-pdf
