#!make
all: manual backend frontend static-copy

manual:
	cd docs; hugo;

backend:
	pip install -r test-requirements.txt; cd harvester_e2e_tests/; pdoc --html -o . .;

frontend:
	cd cypress; npm install; ./node_modules/.bin/typedoc --options ./typedoc.json;

static-copy:
	mv cypress/docs/ docs/public/integration;
	mv harvester_e2e_tests/harvester_e2e_tests docs/public/backend;

live-copy:
	mkdir -p /tmp/hugo/
	mv cypress/docs/ /tmp/hugo/integration;
	mv harvester_e2e_tests/harvester_e2e_tests /tmp/hugo/backend;

preview-hugo:
	cd docs; hugo server --buildDrafts --buildFuture --destination /tmp/hugo

run: clean backend frontend live-copy preview-hugo

clean:
	rm -rf docs/public;
	rm -rf cypress/docs;
	rm -rf harvester_e2e_tests/harvester_e2e_tests;
	rm -rf /tmp/hugo;
