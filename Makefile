APP := "tx_clients"
VERSION := "0.1.4" # Managed by bumpversion. Do not modify.

bumpmicro: ## Bump the micro (patch) version of the package. Auto generates a tag and a commit.
	bumpversion patch

bumppatch: bumpmicro ## Alias for bumpmicro

bumpminor: ## Bump the minor version of the package. Auto generates a tag and a commit.
	bumpversion minor

bumpmajor: ## Bump the major version of the package. Auto generates a tag and a commit.
	bumpversion major

develop: ## Enable setup.py develop mode. Useful for local development. Disable develop mode before installing.
	python setup.py develop

undevelop: ## Disable setup.py develop mode
	python setup.py develop --uninstall

install: ## Install the latest local build of our app to the default environment. Requires building the app.
	conda install -y $(APP) --use-local

uninstall: ## Uninstall the latest build of our app from the default environment
	conda uninstall -y $(APP)

build: ## Build from the conda recipe.
	conda build recipe

test: ## Run trial unittest runner against app. Must be installed or in develop mode. Requires Twisted
	coverage run --source $(APP) `which trial` $(APP)

coverage: ## Display the coverage report. Requires that make test has been run.
	coverage report

lint: ## Run pylint against the app. Must be installed or in develop mode. Requires pylint
	pylint $(APP)

help: ## Print list of tasks and descriptions
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY := develop undevelop install uninstall build test coverage lint help bumppatch bumpminor bumpmajor bumpmicro
