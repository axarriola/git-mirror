import os
import hmac
import hashlib
import logging
import uvicorn
import secrets
import subprocess

from constants import *
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse


app = FastAPI()
security = HTTPBasic()


def run_cmd(cmd: list):
    out: subprocess.CompletedProcess = subprocess.run(cmd,
                                                      stdout=subprocess.PIPE,
                                                      stderr=subprocess.STDOUT,
                                                      shell=False, text=True)

    if out.returncode != 0:
        logging.error(f"Non-zero return code: {out.returncode}")

    logging.info(out.stdout)


def pull(repo_name: str):
    source_url: str = os.environ.get("SOURCE_URL")
    local_path: str = f"{TEMP_DIR}/{repo_name}.git"

    logging.info(f"Mirroring repository {repo_name}")

    if os.path.exists(local_path):
        log_msg = f"{local_path} already cloned, updating..."
        cmd: list[str] = [
            "git", "--git-dir", local_path,
            "remote", "update", "origin"
        ]
    else:
        log_msg = f"Cloning {local_path} for the first time..."
        cmd: list[str] = [
            "git", "clone", "--mirror",
            f"{source_url}/{repo_name}",
            local_path
        ]

    logging.info(log_msg)
    run_cmd(cmd)


def push(repo_name: str):
    dest_url: str = os.environ.get("DESTINATION_URL")

    cmd: list[str] = [
        "git",  "--git-dir",
        f"{TEMP_DIR}/{repo_name}.git",
        "push", "--mirror",
        f"{dest_url}/{repo_name}"
    ]

    logging.info(f"Pushing {repo_name}...")
    run_cmd(cmd)


@app.on_event("startup")
async def init():
    logging.config.dictConfig(LOGGING_CONFIG)

    with open('.env', 'r') as fenv:
        dotenv = dict(
                    tuple(line.rstrip().split('='))
                    for line in fenv.readlines()
                    if not line.startswith('#')
                 )

    os.environ.update(dotenv)

    if os.environ.get("DEBUG") == "1":
        logging.getLogger("").setLevel(logging.DEBUG)

    logging.debug(os.environ)

    if not os.path.isdir(TEMP_DIR):
        logging.info(f"Creating directory {TEMP_DIR}")
        os.mkdir(TEMP_DIR)

    repositories: list[str] = os.environ.get("REPOSITORIES").split(" ")

    for repo in repositories:
        pull(repo)
        push(repo)


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username,
                                              os.environ.get("USER"))
    correct_password = secrets.compare_digest(credentials.password,
                                              os.environ.get("PASSWORD"))

    if not (correct_username and correct_password):
        logging.critical("Unauthorized request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True


@app.get("/ping")
def ping(req: Request, auth: str = Depends(authenticate)):
    logging.info(f"{req.method} {req.client.host}:{req.client.port} {req.url}")
    return JSONResponse(status_code=200, content={"message": "Alive"})


@app.post("/forceupdate/{repo_name}")
def force_update(repo_name: str, req: Request, auth: str = Depends(authenticate)):
    logging.info(f"{req.method} {req.client.host}:{req.client.port} {req.url}")

    repositories: list[str] = os.environ.get("REPOSITORIES").split(" ")

    if repo_name == "all":
        updated: list[str] = repositories
        for repo in repositories:
            pull(repo)
            push(repo)
    else:
        if repo_name in repositories:
            updated: list[str] = [repo_name]
            pull(repo_name)
            push(repo_name)
        else:
            logging.error(f"{repo_name} not in configured list")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{repo_name} not in configured list"
            )
    
    return JSONResponse(status_code=201, content={"Updated": updated})


@app.post("/githubevent")
async def recv_event(req: Request, X_GitHub_Event: str = Header(None), X_Hub_Signature: str = Header(None)):
    logging.info(f"{req.method} {{ X-GitHub-Event: {X_GitHub_Event} }} {req.client.host}:{req.client.port} {req.url}")

    github_secret: str = os.environ.get("GITHUB_SECRET")

    # body_json: to access any required fields directly
    body_json = await req.json()
    # body_bytes: to calculate the digest (converting the json to string and then to bytes is not the same result)
    body_bytes = await req.body()
    
    logging.debug(body_json)

    # Make sure the signature is as expected and matches own result
    if github_secret:
        if not X_Hub_Signature:
            logging.critical(f"Received webhook without X_Hub_Signature")
            raise HTTPException(
                status_code=403,
                detail="Forbidden",
            )

        sig_alg, sig = X_Hub_Signature.split('=')

        if sig_alg != 'sha1':
            logging.critical(f"Non-implemented signature algorithm {sig_alg}")
            raise HTTPException(
                status_code=501,
                detail="Not implemented",
            )
        
        mac = hmac.new(github_secret.encode(), msg=body_bytes, digestmod='sha1')

        if not hmac.compare_digest(str(mac.hexdigest()), str(sig)):
            logging.critical(f"Unmatched signature comparison. Calculated {str(mac.hexdigest())} received {str(sig)}")
            raise HTTPException(
                status_code=403,
                detail="Forbidden",
            )

    if X_GitHub_Event == "ping":
        return JSONResponse(status_code=200, content={"message": "Ping received"})

    if X_GitHub_Event != "push":
        logging.warning(f"Not handling {{ X-GitHub-Event: {X_GitHub_Event} }}")
        return JSONResponse(status_code=405,
                            content={"message": f"X-GitHub-Event: {X_GitHub_Event} not useful"})

    repo_name = body_json['repository']['name']
    ref = body_json['ref']

    repositories: list[str] = os.environ.get("REPOSITORIES").split(" ")

    if repo_name in repositories:
        logging.info(f"Repository {repo_name} received push in {ref}")
        pull(repo_name)
        push(repo_name)
    else:
        logging.error(f"{repo_name} not in configured list")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{repo_name} not in configured list"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2555)
