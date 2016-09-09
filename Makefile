APP := tx_clients
VERSION := 0.3.1# Managed by bumpversion. Do not modify.

TEST_RUNNER := `which trial`# This is intentionally a string

ACTIVE_ENVIRONMENT := $(shell basename $${CONDA_DEFAULT_ENV:-'null'})

check_active: ## Check the active conda environment before allowing certain targets.
ifeq ("$(ACTIVE_ENVIRONMENT)", "_test")
else ifneq ($(ACTIVE_ENVIRONMENT), $(APP))
	printf "\nThe active conda environment is \"$(CONDA_DEFAULT_ENV)\". This target expects the active environment to be \"$(APP)\".\n\n"
	printf "If you have not yet created the environment, run:\n\n    conda env create\n\n"
	printf "To activate the environment, run:\n\n    source activate $(APP)\n\n"
	exit 1
endif

bumpmicro: ## Bump the micro (patch) version of the package. Auto generates a tag and a commit.
	bumpversion patch

bumppatch: bumpmicro ## Alias for bumpmicro

bumpminor: ## Bump the minor version of the package. Auto generates a tag and a commit.
	bumpversion minor

bumpmajor: ## Bump the major version of the package. Auto generates a tag and a commit.
	bumpversion major

develop: check_active ## Enable setup.py develop mode. Useful for local development. Disable develop mode before installing.
	python setup.py develop

undevelop: check_active ## Disable setup.py develop mode
	python setup.py develop --uninstall

install: check_active ## Install the latest local build of our app to the default environment. Requires building the app.
	conda install -y $(APP) --use-local

uninstall: check_active ## Uninstall the latest build of our app from the default environment
	conda uninstall -y $(APP)

build: check_active ## Build from the conda recipe.
	conda build recipe

test: ## Run trial unittest runner against app. Must be installed or in develop mode. Requires Twisted
	coverage run --branch --source $(APP) $(TEST_RUNNER) $(APP)

coverage: ## Display the coverage report. Requires that make test has been run.
	coverage report

lint: ## Run pylint against the app. Must be installed or in develop mode. Requires pylint
	pylint $(APP)

flake8: ## Run flake8 against the apps source. CANNOT be run on build. Requires flake8
	 flake8 --show-source --statistics --benchmark $(APP)

circle_deploy_pypi: ## Build and Upload pypi package from circle
	python setup.py sdist
	anaconda --token $(ANACONDA_CLOUD_DEPLOY_TOKEN) upload -u $(ANACONDA_CLOUD_ORGANIZATION) --label main --no-register --force dist/$(APP)-$(VERSION).tar.gz

circle_deploy_conda: ## Build and Upload conda package from circle
	conda build -q --user $(ANACONDA_CLOUD_ORGANIZATION) --token $(ANACONDA_CLOUD_DEPLOY_TOKEN) recipe

clean: ## Removes all untracked files and directories including those ignored by git
	git clean -Xfd

help: ## Print list of tasks and descriptions
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.SILENT: check_active
