#!make
all: manual backend frontend static-copy

pytest-install:
	pip install -r test-requirements.txt

manual:
	cd docs; hugo;

backend:
	pytest-install; cd harvester_e2e_tests/; pdoc --html -o . .;

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
	cd docs; hugo server --buildDrafts --buildFuture --destination /tmp/hugo --bind 0.0.0.0

run-docs: clean backend frontend live-copy preview-hugo

clean-docs:
	rm -rf docs/public;
	rm -rf cypress/docs;
	rm -rf harvester_e2e_tests/harvester_e2e_tests;
	rm -rf /tmp/hugo;

run-all-tests:
	tox -e testenv -- harvester_e2e_tests --html=test_result.html
	
run-api-tests:
	tox -e testenv -- harvester_e2e_tests/apis --html=test_result.html

run-scenario-tests:
	tox -r -e testenv -- harvester_e2e_tests/scenarios --html=test_result.html

run-integration-tests:
	tox -r -e testenv -- harvester_e2e_tests/integration --html=test_result.html
