

# Static, not sure if needed??
PYTHON=python3
PIP=pip3

FILES=pull_organization_data.py trigger_account_actions.py get_billing_data.py report-accounts.py report-vpcs.py \
		inventory-instances-sg.py inventory-health-report.py inventory-eni.py inventory-vpc.py \
		inventory-route53.py inventory-buckets.py inventory-iam.py inventory-ecs.py new_account_handler.py \
		inventory-cloudtrail.py inventory-es.py inventory-secrets.py inventory-ecr.py inventory-lambdas.py inventory-kms.py \
		inventory-dx.py inventory-ami.py inventory-cft.py inventory-cloudfront.py

DEPENDENCIES=yaml semver.py lib mako markupsafe bin

package: test clean deps zipfile

#
# Lambda function management
#

clean:
	rm -rf __pycache__ *.zip *.dist-info $(DEPENDENCIES)

# # Create the package Zip. Assumes all tests were done
zipfile:  $(FILES) $(DEPENDENCIES)
	cp -a ../../lib .
	zip -r $(LAMBDA_PACKAGE) $^

test: $(FILES)
	for f in $^; do $(PYTHON) -m py_compile $$f; if [ $$? -ne 0 ] ; then echo "$$f FAILS" ; exit 1; fi done

deps:
	$(PIP) install -r requirements.txt -t . --upgrade
	cp -a ../../lib .
