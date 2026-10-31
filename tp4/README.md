# TP04: Containerization of the HIGGS (1% sample) analysis with Docker

The application reads `data/HIGGS_sample_1pct.csv` (mounted read-only), profiles and cleans it,
and builds an interactive dashboard. Results are written to `output/`.

## Files

```
higgs-project/
├── Dockerfile          image definition (FROM, WORKDIR, COPY, RUN, CMD)
├── compose.yaml        Task 4: one service, data mounted read-only
├── requirements.txt    pandas, numpy, plotly
├── run_pipeline.sh     runs clean.py then dashboard.py (SERVE=1 also serves the dashboard on port 8000)
├── .dockerignore
├── README.md
├── REPORT.md           answers to the TP questions
├── data/               put HIGGS_sample_1pct.csv here
├── output/             created results: profile.txt, higgs_clean.csv, dashboard.html, index.html
└── src/
    ├── clean.py        profile + cleaning
    └── dashboard.py    charts
```

Docker Hub username used below: `alaaguedda`. Commands are for PowerShell
(Docker Desktop on Windows). On Linux/macOS replace `${PWD}` with `$(pwd)`.

## Before anything: start the Docker engine

Open **Docker Desktop** from the Start menu and wait until it says **Engine running** (bottom left).
Then check that `docker info` shows a `Server:` section without an error.
If it does not start: run `wsl --update` in PowerShell, restart the computer, and make sure
virtualization is enabled (Task Manager > Performance > CPU > Virtualization: Enabled).

## Task 1: Installation

```
docker --version
docker run hello-world
docker login
```
Your Docker Hub account is `alaaguedda` (already saved on this computer). If `docker login` asks, finish the login
in the browser, or use `docker login -u alaaguedda` with your password or an access token.
Take a screenshot of the three outputs.

## Task 2: Image, push, pull

```
docker build -t alaaguedda/tp04-higgs:1.0 .
docker images
docker push alaaguedda/tp04-higgs:1.0
docker rmi alaaguedda/tp04-higgs:1.0
docker pull alaaguedda/tp04-higgs:1.0
```
`docker rmi` deletes the local copy so the `pull` really downloads it from Docker Hub.

## Task 3: Three containers on one network

```
docker network create tp04-net

docker run -d --name tp04-c1 --network tp04-net -p 8001:8000 -e SERVE=1 -v "${PWD}/data:/app/data:ro" alaaguedda/tp04-higgs:1.0
docker run -d --name tp04-c2 --network tp04-net -p 8002:8000 -e SERVE=1 -v "${PWD}/data:/app/data:ro" alaaguedda/tp04-higgs:1.0
docker run -d --name tp04-c3 --network tp04-net -p 8003:8000 -e SERVE=1 -v "${PWD}/data:/app/data:ro" alaaguedda/tp04-higgs:1.0
```

Verify (screenshot each):
```
docker ps
docker network inspect tp04-net
docker logs tp04-c1
```
Open http://localhost:8001, http://localhost:8002 and http://localhost:8003: each shows the dashboard.

Clean up when done:
```
docker stop tp04-c1 tp04-c2 tp04-c3
docker rm tp04-c1 tp04-c2 tp04-c3
docker network rm tp04-net
```

## Task 4: Docker Compose

```
docker compose up --build
docker compose ps -a
docker compose down
```
The container runs the analysis and exits (`restart: "no"`), so `ps -a` shows it as `Exited (0)`.
Results appear in `output/`: open `output/dashboard.html` and import `output/higgs_clean.csv` in Power BI.

## Deliverables for GitHub
Source files (this folder), screenshots of each task, and this README.md.
