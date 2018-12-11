IMAGE=pi-k8s-fitches-chore-redis
VERSION=0.3
ACCOUNT=gaf3
NAMESPACE=fitches
VOLUMES=-v ${PWD}/lib/:/opt/pi-k8s/lib/ -v ${PWD}/test/:/opt/pi-k8s/test/ -v ${PWD}/setup.py:/opt/pi-k8s/setup.py

.PHONY: build shell test tag push

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	docker run --privileged -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh

test:
	docker run --privileged -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m"

tag:
	git tag -a "v$(VERSION)" -m "Version $(VERSION)"

push:
	git push origin "v$(VERSION)"