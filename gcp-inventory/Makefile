
ifndef env
# $(error env is not set)
	env ?= stage
endif

ifdef CONFIG
	include ../$(CONFIG)
	export
else
	include ../config.$(env)
	export
endif

# STACK_PREFIX is custom to your deployment and should be the same for all Antiope Stacks
ifndef STACK_PREFIX
	$(error STACK_PREFIX is not set)
endif

ifndef BUCKET
	$(error BUCKET is not set)
endif


ifndef version
	export version := $(shell date +%Y%b%d-%H%M)
endif

# Specific to this stack
export STACK_NAME=gcp-inventory
# Filename for the CFT to deploy
export STACK_TEMPLATE=cloudformation/Inventory-Template.yaml

# Name of the Zip file with all the function code and dependencies
export LAMBDA_PACKAGE=$(STACK_NAME)-lambda-$(version).zip

# The full name of the stack in Cloudformation. This must match the manifest file
export FULL_STACK_NAME=$(STACK_PREFIX)-$(env)-$(STACK_NAME)

# Name of the manifest file.
export manifest=cloudformation/$(FULL_STACK_NAME)-Manifest.yaml

# location in the Antiope bucket where we drop lambda-packages
export OBJECT_KEY=deploy-packages/$(LAMBDA_PACKAGE)

# For uploading CFT to S3
export TEMPLATE_KEY ?= deploy-packages/$(STACK_NAME)-Template-$(version).yaml
export TEMPLATE_URL ?= https://s3.amazonaws.com/$(BUCKET)/$(TEMPLATE_KEY)

# List of all the functions deployed by this stack. Required for "make update" to work.
FUNCTIONS = $(FULL_STACK_NAME)-pull-organization-data \
			$(FULL_STACK_NAME)-create-project-report \
			$(FULL_STACK_NAME)-new_project_handler


.PHONY: $(FUNCTIONS)

# Run all tests
test: cfn-validate
	cd lambda && $(MAKE) test

# Do everything
deploy: package upload cfn-deploy templates

clean:
	cd lambda && $(MAKE) clean

#
# Cloudformation Targets
#

# Upload template to S3
cfn-upload: $(STACK_TEMPLATE)
	aws s3 cp $(STACK_TEMPLATE) s3://$(BUCKET)/$(TEMPLATE_KEY)

# Validate the template
cfn-validate: cfn-upload $(STACK_TEMPLATE)
	aws cloudformation validate-template --template-url $(TEMPLATE_URL)

# Deploy the stack
cfn-deploy: cfn-validate $(manifest)
	deploy_stack.rb -m $(manifest) --template-url $(TEMPLATE_URL) pLambdaZipFile=$(OBJECT_KEY) pBucketName=$(BUCKET) pEnvironment=$(env)  --force

#
# Lambda Targets
#
package:
	cd lambda && $(MAKE) package

upload: package
	aws s3 cp lambda/$(LAMBDA_PACKAGE) s3://$(BUCKET)/$(OBJECT_KEY)

# # Update the Lambda Code without modifying the CF Stack
update: package $(FUNCTIONS)
	for f in $(FUNCTIONS) ; do \
	  aws lambda update-function-code --function-name $$f --zip-file fileb://lambda/$(LAMBDA_PACKAGE) ; \
	done

# Update one specific function. Called as "make fupdate function=<fillinstackprefix>-aws-inventory-ecs-inventory"
fupdate: package
	aws lambda update-function-code --function-name $(function) --zip-file fileb://lambda/$(LAMBDA_PACKAGE) ; \

# This will prompt for confirmation
# purge-tables:
# 	purge_ddb_table.py --table $(FULL_STACK_NAME)-accounts --key_attribute account_id --force
# 	purge_ddb_table.py --table $(FULL_STACK_NAME)-billing-data --key_attribute account_id --force
# 	purge_ddb_table.py --table $(FULL_STACK_NAME)-vpc-inventory --key_attribute vpc_id --force

trigger:
	../bin/trigger_state_machine.sh $(FULL_STACK_NAME)


templates:
	aws s3 cp html_templates/* s3://$(BUCKET)/Templates/

purge-logs:
	for f in $(FUNCTIONS) ; do \
	  aws logs delete-log-group --log-group-name /aws/lambda/$$f ; \
	done

expire-logs:
	for f in $(FUNCTIONS) ; do \
	  aws logs put-retention-policy --log-group-name /aws/lambda/$$f --retention-in-days 5 ; \
	done
