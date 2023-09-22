
SHELL := /bin/bash

all: check-env version.py octoprint_filamentswitcher/version.py



# Create an auto-incrementing build number.
BUILD_DATE        =$$(date +'%Y%m%d')
BUILD_INFO_FILE   =version.py
BUILD_NUMBER_FILE =buildnum$(BUILD_DATE).tmp
BUILD_NUMBER      =$$(cat $(BUILD_NUMBER_FILE))

YYYYMMDD       = $(shell date +"%Y-%m-%d")
VER_MAJOR      = 0
VER_MINOR      = 1
VER_REVISION   = $(BUILD_DATE)b$(BUILD_NUMBER)
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
	@echo "YYYYMMDD           =\"$(YYYYMMDD)\""      >> $@
	@echo "VER_MAJOR          =$(VER_MAJOR)"         >> $@
	@echo "VER_MINOR          =$(VER_MINOR)"         >> $@
	@echo "VER_REVISION       =\"$(VER_REVISION)\""  >> $@
	@echo "VERSION            =\"$(VERSION)\""       >> $@
	@echo "plugin_version     =\"$(VERSION)\""       >> $@
	@echo "__plugin_version__ =\"$(VERSION)\""       >> $@
	@#echo "BUILD_NUMBER       =$(BUILD_NUMBER)"      >> $@
	@echo "FULLNAME           =\"$(FULLNAME)\""      >> $@
	@echo "EMAIL              =\"$(EMAIL)\""         >> $@
	@#cat $(BUILD_INFO_FILE)



#version.py: octoprint_filamentswitcher/__init__.py
octoprint_filamentswitcher/version.py: version.py
	@echo ... Creating Build Version file $@
	@cp -v $< $@
		



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


.PHONY: all deploy check-env

