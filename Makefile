APP := tx_clients

develop: ## Enable setup.py develop mode. Useful for local development. Disable develop mode before installing.
	python setup.py develop

undevelop: ## Disable setup.py develop mode
	python setup.py develop --uninstall

install: ## Install the latest local build of our app to the default environment. Requires building the app.
	conda install $(APP) --use-local

uninstall: ## Uninstall the latest build of our app from the default environment
	conda uninstall $(APP)

build: ## Build from the conda recipe.
	conda build recipe

test: ## Run trial unittest runner against app. Must be installed or in develop mode. Requires Twisted
	trial $(APP)

lint: ## Run pylint against the app. Must be installed or in develop mode. Requires pylint
	pylint $(APP)

help: ## print list of tasks and descriptions
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY := develop undevelop install uninstall build test lint help
