.PHONY: login build push

REGISTRY = turingrldsg.azurecr.io

login:
	docker login $(REGISTRY) -u ${RL_ADMIN_TOKEN_NAME} -p ${RL_ADMIN_TOKEN} 

build:
	docker build -t $(REGISTRY)/battleground:latest -f Dockerfile .
push:
	docker push $(REGISTRY)/battleground:latest
