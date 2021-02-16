.PHONY: docs api_docs docs-serve


api_docs:
	pdoc3 plugins --html --output-dir docs/api --force

docs: api_docs

docs-serve:
	python3 -m http.server --directory ./docs
