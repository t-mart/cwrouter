REQUIREMENTS="requirements-dev.txt"

all: test

uninstall-cwrouter:
	@echo $(TAG)Removing existing installation of cwrouter$(END)
	- pip uninstall --yes cwrouter >/dev/null
	! which cwrouter
	@echo

uninstall-all: uninstall-cwrouter
	- pip uninstall --yes -r $(REQUIREMENTS)

init: uninstall-cwrouter
	@echo $(TAG)Installing dev requirements$(END)
	pip install --upgrade -r $(REQUIREMENTS)
	@echo $(TAG)Installing HTTPie$(END)
	pip install --upgrade --editable .
	@echo

test: init
	@echo $(TAG)Running tests in on current Python with coverage $(END)
	py.test --cov-report term-missing --cov ./cwrouter --verbose ./tests
	@echo