BUNDLED_PYTHON := /Users/cam/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
PYTHON ?= $(shell if [ -x "$(BUNDLED_PYTHON)" ]; then echo "$(BUNDLED_PYTHON)"; else command -v python3; fi)
SCAN_INPUT ?= input/raw scans/main book
FAMILY_SITE_OUTPUT ?= build/family-site
AUDIOBOOK_SCRIPT_OUTPUT ?= audiobook/script
DOC_WEB_RUN_ID ?= alain-lessard-book-r1
DOC_WEB_SNAPSHOT_ID ?= $(DOC_WEB_RUN_ID)

.PHONY: skills-sync skills-check methodology-compile methodology-check scan-intake-report process-scans build-image-pdf ocr-pdf archival-image-pdf archival-pdf scan-pdf-all doc-web-contract doc-web-run doc-web-import-run doc-web-validate-active build-audiobook-script build-family-site deploy-static render-pdf-checks validate-pdf

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

doc-web-contract:
	$(PYTHON) scripts/doc_web_import.py contract

doc-web-run:
	$(PYTHON) scripts/doc_web_import.py run --run-id "$(DOC_WEB_RUN_ID)" --force

doc-web-import-run:
	$(PYTHON) scripts/doc_web_import.py import-run --run-id "$(DOC_WEB_RUN_ID)" --snapshot-id "$(DOC_WEB_SNAPSHOT_ID)" --force

doc-web-validate-active:
	$(PYTHON) scripts/doc_web_import.py validate-bundle --bundle-path "input/doc-web-html/$(DOC_WEB_SNAPSHOT_ID)"

build-audiobook-script:
	$(PYTHON) scripts/build_audiobook_script.py --output "$(AUDIOBOOK_SCRIPT_OUTPUT)"

build-family-site: build-audiobook-script
	$(PYTHON) scripts/build_family_site.py --output "$(FAMILY_SITE_OUTPUT)"

deploy-static:
	$(PYTHON) scripts/deploy_static_site.py --source "$(FAMILY_SITE_OUTPUT)"

render-pdf-checks:
	$(PYTHON) scripts/process_book_scans.py render-checks

validate-pdf:
	$(PYTHON) scripts/process_book_scans.py validate-pdf
