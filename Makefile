IMAGE_NAME = "github-listen-mirror"
REGISTRY=myregistry:5000/folder/

all: build run

build:
		docker build -t ${IMAGE_NAME} .

run:
		docker run -d -p 2555:2555 --name ${IMAGE_NAME} ${IMAGE_NAME}

push:
		docker tag ${IMAGE_NAME} ${REGISTRY}${IMAGE_NAME}:${CI_COMMIT_TAG}
		docker push ${REGISTRY}${IMAGE_NAME}

stop:
		docker stop ${IMAGE_NAME}
		docker rm ${IMAGE_NAME}

cleanimages:
		docker rmi --force ${REGISTRY}${IMAGE_NAME}:${CI_COMMIT_TAG}
		docker rmi --force ${IMAGE_NAME}
