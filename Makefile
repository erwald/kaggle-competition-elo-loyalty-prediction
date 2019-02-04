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
	mkdir -p $@

data/raw: | data
	mkdir -p $@

zipfiles = $(notdir $(wildcard data/raw/*.csv.zip))
unzippedfiles = $(notdir $(wildcard data/unzipped/*.csv))
alreadyunzipped = $(unzippedfiles:%.csv=%.csv.zip)
missingunzipped = $(filter-out $(alreadyunzipped),$(zipfiles))
data/unzipped: kaggle
ifeq (, $(wildcard data/unzipped))
	mkdir -p $@
endif
ifneq (,$(missingunzipped))
	cd $@; for f in $(addprefix ../raw/,$(missingunzipped)); do unzip $$f; done
	chmod 0644 $@/*.csv
endif

# Targets for further data processing, epecially commands that take along time
# call 'make processdata' to update all targets.
# For specific files call make only on their target, e.g. 'make data/processed/merchants.csv'.
#
# For each file 'xxx' to be created in folder 'data/processed':
# 1. add it to 'processedfiles'
# 2. add a target 'data/processed/xxx: <dependencies> | data/processed' with the rules to generate the file.
#    <dependencies> should be the list of files that should trigger recreation of the file if they change.
#    We add 'data/processed' as an order-only prerequisite to make sure this rule isn't triggered
#    by changes to unrelated files.
# IMPORTANT: Indentation must be by TABS, not spaces.

.PHONY: processdata
processedfiles = merchants.csv new_merchant_transactions_with_merchants.csv historical_transactions_with_merchants.csv
processdata: $(addprefix data/processed/,$(processedfiles))

data/processed/new_merchant_transactions_with_merchants.csv: data/processed/new_merchant_transactions.csv data/processed/merchants.csv | data/processed
	source activate && python join_transactions_and_merchants.py data/processed/new_merchant_transactions.csv $@

data/processed/historical_transactions_with_merchants.csv: data/processed/historical_transactions.csv data/processed/merchants.csv | data/processed
	source activate && python join_transactions_and_merchants.py data/processed/historical_transactions.csv $@

data/processed/new_merchant_transactions.csv: data/unzipped/new_merchant_transactions.csv | data/processed
	source activate && python clean_transactions.py data/unzipped/new_merchant_transactions.csv $@

data/processed/historical_transactions.csv: data/unzipped/historical_transactions.csv | data/processed
	source activate && python clean_transactions.py --calculate_time_since_purchase_with_merchant data/unzipped/historical_transactions.csv $@

data/processed/merchants.csv: data/unzipped/merchants.csv | data/processed
	source activate && python clean_merchants.py $@

data/processed: data/unzipped
	mkdir -p $@

# call 'make print-{VARIABLE}' to print make variable value
# e.g.: make print-missingunzipped
print-%: ; @echo $* = $($*)

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
