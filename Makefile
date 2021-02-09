.PHONY: base agent agent_test

base:
	docker build -t plark_hunt/base:latest -f Dockerfile_base .

agent:
	docker build -t plark_hunt/team_$(label):latest -f Dockerfile_agent .

agent_test:
	docker run plark_hunt/team_$(label):latest tests/test_docker/test_agent.sh