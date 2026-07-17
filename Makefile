BUNDLED_PYTHON := /Users/cam/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
PYTHON ?= $(shell if [ -x "$(BUNDLED_PYTHON)" ]; then echo "$(BUNDLED_PYTHON)"; else command -v python3; fi)
SCAN_INPUT ?= input/raw scans/main book
SCAN_INTAKE_OUTPUT ?= output/intake
FAMILY_SITE_OUTPUT ?= build/family-site
AUDIOBOOK_SCRIPT_OUTPUT ?= audiobook/script
AUDIOBOOK_MANIFEST ?= audiobook/manifest.json
PORTABLE_MANIFEST ?= portable/manifest.json
EPUBCHECK_JAR ?=
DOC_WEB_RUN_ID ?= alain-lessard-book-r1
DOC_WEB_SNAPSHOT_ID ?= $(DOC_WEB_RUN_ID)
PUBLIC_BASE ?=

.PHONY: skills-sync skills-check methodology-compile methodology-check scan-intake-report process-scans build-image-pdf ocr-pdf archival-image-pdf archival-pdf scan-pdf-all supplemental-docs validate-supplemental-docs render-supplemental-pdf-checks doc-web-contract doc-web-run doc-web-import-run doc-web-validate-active companion-doc-web validate-companion-doc-web test-audiobook test-portable-editions build-audiobook-script inspect-audiobook validate-audiobook build-full-audiobook build-epub validate-epub build-m4b validate-m4b build-portable-editions validate-portable-editions build-family-site validate-family-site validate-family-site-release deploy-deps deploy-static render-pdf-checks validate-pdf

skills-sync:
	./scripts/sync-agent-skills.sh

skills-check:
	./scripts/sync-agent-skills.sh --check

methodology-compile:
	$(PYTHON) scripts/methodology_graph.py build

methodology-check:
	$(PYTHON) scripts/methodology_graph.py check

scan-intake-report:
	$(PYTHON) scripts/inspect_scan_set.py "$(SCAN_INPUT)" --output-dir "$(SCAN_INTAKE_OUTPUT)"

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

supplemental-docs:
	$(PYTHON) scripts/process_supplemental_scans.py all

validate-supplemental-docs:
	$(PYTHON) scripts/process_supplemental_scans.py validate

render-supplemental-pdf-checks:
	$(PYTHON) scripts/process_supplemental_scans.py render-checks

doc-web-contract:
	$(PYTHON) scripts/doc_web_import.py contract

doc-web-run:
	$(PYTHON) scripts/doc_web_import.py run --run-id "$(DOC_WEB_RUN_ID)" --force

doc-web-import-run:
	$(PYTHON) scripts/doc_web_import.py import-run --run-id "$(DOC_WEB_RUN_ID)" --snapshot-id "$(DOC_WEB_SNAPSHOT_ID)" --force

doc-web-validate-active:
	$(PYTHON) scripts/doc_web_import.py validate-bundle --bundle-path "input/doc-web-html/$(DOC_WEB_SNAPSHOT_ID)"

companion-doc-web: supplemental-docs
	$(PYTHON) scripts/build_supplemental_doc_web.py run --force

validate-companion-doc-web:
	$(PYTHON) scripts/build_supplemental_doc_web.py validate

test-audiobook:
	$(PYTHON) -m unittest discover -s tests -p 'test_audiobook*.py'
	$(PYTHON) -m unittest discover -s tests -p 'test_build_full_audiobook.py'

test-portable-editions:
	$(PYTHON) -m unittest discover -s tests -p 'test_portable_editions.py'
	$(PYTHON) -m unittest discover -s tests -p 'test_build_m4b.py'

build-audiobook-script:
	$(PYTHON) scripts/build_audiobook_script.py --output "$(AUDIOBOOK_SCRIPT_OUTPUT)"

inspect-audiobook:
	$(PYTHON) scripts/audiobook.py inspect --manifest "$(AUDIOBOOK_MANIFEST)"

validate-audiobook:
	$(PYTHON) scripts/audiobook.py validate --manifest "$(AUDIOBOOK_MANIFEST)" --release --decode

build-full-audiobook: build-audiobook-script
	$(PYTHON) scripts/build_full_audiobook.py \
		--manifest "$(AUDIOBOOK_MANIFEST)" \
		$(if $(OUTPUT),--output "$(OUTPUT)",) \
		$(if $(FORCE),--force,)

build-epub:
	$(PYTHON) scripts/portable_editions.py build-epub \
		--manifest "$(PORTABLE_MANIFEST)" \
		$(if $(OUTPUT),--output "$(OUTPUT)",) \
		$(if $(FORCE),--force,)

validate-epub:
	$(PYTHON) scripts/portable_editions.py validate-epub \
		--manifest "$(PORTABLE_MANIFEST)" \
		$(if $(EPUBCHECK),--epubcheck,) \
		$(if $(EPUBCHECK_JAR),--epubcheck-jar "$(EPUBCHECK_JAR)",)

build-m4b:
	$(PYTHON) scripts/build_m4b.py build \
		--audiobook-manifest "$(AUDIOBOOK_MANIFEST)" \
		--portable-manifest "$(PORTABLE_MANIFEST)" \
		$(if $(OUTPUT),--output "$(OUTPUT)",) \
		$(if $(FORCE),--force,)

validate-m4b:
	$(PYTHON) scripts/build_m4b.py validate \
		--audiobook-manifest "$(AUDIOBOOK_MANIFEST)" \
		--portable-manifest "$(PORTABLE_MANIFEST)"

build-portable-editions:
	$(MAKE) build-epub FORCE="$(FORCE)"
	$(MAKE) build-m4b FORCE="$(FORCE)"
	$(MAKE) build-family-site RELEASE="$(RELEASE)"

validate-portable-editions: validate-epub validate-m4b

build-family-site: build-audiobook-script supplemental-docs
	$(PYTHON) scripts/build_family_site.py --output "$(FAMILY_SITE_OUTPUT)" $(if $(RELEASE),--require-complete-audio,)

validate-family-site:
	$(PYTHON) scripts/validate_family_site.py --build-dir "$(FAMILY_SITE_OUTPUT)" $(if $(PUBLIC_BASE),--public-base "$(PUBLIC_BASE)",) $(if $(RELEASE),--require-complete-audio,)

validate-family-site-release:
	$(PYTHON) scripts/validate_family_site.py --build-dir "$(FAMILY_SITE_OUTPUT)" --require-complete-audio $(if $(PUBLIC_BASE),--public-base "$(PUBLIC_BASE)",)

deploy-deps:
	$(PYTHON) -m pip install -r requirements-deploy.txt

deploy-static: validate-family-site-release
	$(PYTHON) scripts/deploy_static_site.py --source "$(FAMILY_SITE_OUTPUT)"

render-pdf-checks:
	$(PYTHON) scripts/process_book_scans.py render-checks

validate-pdf:
	$(PYTHON) scripts/process_book_scans.py validate-pdf
