define USAGE
Haiqu build system ⚙️

Commands:
	html        Build Sphinx documentation.
	setup-docs  Install Sphinx requirements.
endef

export USAGE
help:
	@echo "$$USAGE"

html:
	python3 -m sphinx -b html ./docs/source public

setup-docs:
	pip3 install -r ./docs/requirements.txt
