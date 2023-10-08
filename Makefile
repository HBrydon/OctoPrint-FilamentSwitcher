#!/usr/bin/make -f

SHELL := /bin/bash

VERSION_FILE = octoprint_filamentswitcher/include/pluginversion.py

all: check-env $(VERSION_FILE)



# Create an auto-incrementing build number.
BUILD_YMD         = $(shell date +"%Y%m%d")
BUILD_DATE        =$$(date +'%Y-%m-%d')
BUILD_INFO_FILE   =$(VERSION_FILE)
BUILD_NUMBER_FILE =buildnum$(BUILD_YMD).tmp
BUILD_NUMBER      =$$(cat $(BUILD_NUMBER_FILE))

VER_MAJOR      = 0
VER_MINOR      = 1
VER_PATCH      = $(BUILD_YMD)
VER_REVISION   = $(BUILD_YMD)b$(BUILD_NUMBER)
VER_MMP        =$(VER_MAJOR).$(VER_MINOR).$(VER_PATCH)
VERSION        =$(VER_MAJOR).$(VER_MINOR).$(VER_REVISION)
FULLNAME       =H Brydon
EMAIL          ="2030784+HBrydon@users.noreply.github.com"

# Build Info file.  Define values based on today's date, increment build number
# for each package build.

$(BUILD_INFO_FILE): octoprint_filamentswitcher/__init__.py
	@echo ... Creating Build Version file $@
	@if ! test -f $(BUILD_NUMBER_FILE); then echo 0 > $(BUILD_NUMBER_FILE); fi
	@echo $$(($$(cat $(BUILD_NUMBER_FILE)) + 1)) > $(BUILD_NUMBER_FILE)
	@echo "# version.py"                              > $@
	@echo "#"                                        >> $@
	@echo "# Generated file - do not edit"           >> $@
	@echo -e "#\n"                                   >> $@
	@echo "BUILD_DATE         =\"$(BUILD_DATE)\""    >> $@
	@echo "BUILD_YMD          =\"$(BUILD_YMD)\""     >> $@
	@echo "VER_MAJOR          =$(VER_MAJOR)"         >> $@
	@echo "VER_MINOR          =$(VER_MINOR)"         >> $@
	@echo "VER_PATCH          =\"$(VER_PATCH)\""     >> $@
	@echo "VER_REVISION       =\"$(VER_REVISION)\""  >> $@
	@echo "VER_MMP            =\"$(VER_MMP)\""       >> $@
	@echo "VERSION            =\"$(VERSION)\""       >> $@
	@echo "FULLNAME           =\"$(FULLNAME)\""      >> $@
	@echo "EMAIL              =\"$(EMAIL)\""         >> $@
	@#cat $(BUILD_INFO_FILE)
	@ls -la $@
	pip install -e .


#octoprint_filamentswitcher/include/version.py: version.py
#	@echo ... Creating Build Version file $@
#	@cp -v $< $@

#deploy: check-env
#	...

#other-thing-that-needs-env: check-env
#	...

#define-env:
#	echo "PWD 2 is ${PWD}" && virtualenv venv && source venv/bin/activate && pip install -e '.[develop,plugins]'


# The following check for VIRTUAL_ENV based on info found at
#  https://stackoverflow.com/questions/4728810/how-to-ensure-makefile-variable-is-set-as-a-prerequisite
check-env:
ifndef VIRTUAL_ENV
	@echo "**** Virtual environment does not seem to be created. You need to go to"
	@echo "**** to ~/workarea/OctoPrint and run create_env"
endif

#~/workarea/OctoPrint/create_venv: create_venv
#	@echo ... Populating $@ from $<
#	- @chmod +x $<
#	- @cp -v $< $@


TARGETS = $(VERSION_FILE)

clean:
	- @rm -v $(TARGETS)

.PHONY: all clean #  deploy check-env

