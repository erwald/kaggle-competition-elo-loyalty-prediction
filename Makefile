SHELL := /bin/bash

.DELETE_ON_ERROR:
.PHONY: all

all: data/unzipped .git | env data data/raw

env:
	python3 -m venv $@
	ln -s $@/bin/activate activate

env/.requirements.lastrun: requirements.txt | env
	source activate && pip install -r requirements.txt
	touch $@

.git:
	git init
	git add .
	git commit -m "Initial commit"

data:
	mkdir $@

data/raw: | data
	mkdir $@

data/unzipped: kaggle
ifeq (, $(wildcard data/unzipped))
	mkdir $@
	cd $@; for f in ../raw/*.zip; do unzip $$f; done
	chmod 0644 $@/*.csv
endif

data/%.csv: data/raw/%.csv.zip
	unzip $<


# Clean commands

.PHONY: distclean envclean gitclean dataclean rawclean

distclean: envclean gitclean alldataclean

# clean everything that can be recreated from raw data
clean: processeddataclean

envclean:
	rm -f activate
	rm -rf env

gitclean:
	rm -rf .git

alldataclean: rawclean
ifneq (, $(wildcard data))
	rm -rf data
endif

rawclean:
ifneq (, $(wildcard data/raw))
	rm -rf data/raw
endif

allbutraw := $(filter-out data/raw,$(wildcard data/*))
processeddataclean:
ifneq (, $(allbutraw))
	rm -rf $(allbutraw)
endif

# Kaggle commands

.PHONY: kaggle

kaggle: | data/raw env/.requirements.lastrun
ifeq (, $(wildcard data/raw/*))
	source activate && kaggle competitions download -c elo-merchant-category-recommendation -p data/raw/
endif
