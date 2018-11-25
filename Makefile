IMAGE=pi-k8s-fitches-chore-redis
VERSION=0.1
ACCOUNT=gaf3
NAMESPACE=fitches
VOLUMES=-v ${PWD}/lib/:/opt/pi-k8s/lib/ -v ${PWD}/test/:/opt/pi-k8s/test/ -v ${PWD}/setup.py:/opt/pi-k8s/setup.py

.PHONY: pull build shell test run push create update delete

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	docker run --privileged -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh

test:
	docker run --privileged -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include lib/*.py"
