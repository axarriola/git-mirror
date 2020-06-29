# git-mirror
Mirror a list of repositories from one location to another. Written in python3.8 with Fastapi, it listens to webhooks (push events) to trigger the mirroring and always have the latest changes.

It validates the received webhooks integrity with the Github Secret. The script also receives API calls from the user (authenticated with username/password).

# Quick how to

## Create the .env file
The .env file contains all the variables that the script uses. The file .env.example is added as 

The variables are the following:
* **REPOSITORIES:** space-separated list of repository names
* **SOURCE_URL:** source url including the oauth key and the organization, e.g.: https://oauth2:abcd1234@github.com/MY_ORGANIZATION
* **DESTINATION_URL:** destination url including the oauth key and the organization, e.g.: https://oauth2:vwxyz6789@local-git.example.com/MY_ORGANIZATION
* **USER:** user to authenticate with the script API
* **PASSWORD:** password to authenticate with the script API
* **GITHUB_SECRET:** secret used to validate the integrity of the received webhooks.
* **DEBUG:** set to 1 to set logging level to debug.
* **GIT_SSL_NO_VERIFY:** set to true or false

## Build and run containerized app

This will build the docker image and execute the container. It will listen in port 2555.
```
make all
```

You can check if it is running with GET to `/ping`
```
curl -X GET -u ${USER}:${PASSWORD} http://your-git-mirror-host:2555/ping
```

## Configure webhook in Github repository

Go to your organization in the source location. Open settings -> hooks -> Add webhook. Set the following config
```
payload url: http://your-git-mirror-host:2555/githubevent
content type: application/json
secret: ${GITHUB_SECRET}
```

# Force the app to update a repository
In case you want to trigger the update of a repository, you can do a POST request to /forceupdate/${REPO_NAME}

```
curl -X POST -u ${USER}:${PASSWORD} http://your-git-mirror-host:2555/forceupdate/${REPO_NAME}
```

# Files

* **main.py:** python source code for the application
* **constants.py:** variables used by the application
* **requirements.txt:** python libraries required
* **.gitlab-ci.yml:** gitlab-ci pipeline config to build app into container image and push to registry.
* **Dockerfile:** used to package app into container
* **Makefile:** commands to build, run, tag and push containerized app
* **.env.example:** example of how the secrets variables

# Recommendations

## Mount .env file as volume!!!
In this repository, the .env file is copied into the container image. The .env file should be mounted as a volume in the container instead. Because these are variables,
if they are built into the container it reduces flexibility (in case of a change you would have to re-build the image and then re-deploy the container). Also, since there are
secrets involved, it would be highly insecure.

## App port
Currently, the application runs on port 2555, to change that you would need to modify it in the Dockerfile CMD and in the `docker run` -p flag.
