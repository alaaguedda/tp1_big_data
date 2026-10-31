# TP04 Report

## Task 4 questions

**What problem does Docker Compose solve?**
It describes a whole application (services, build instructions, volumes, networks, settings) in one
YAML file. Instead of typing long `docker run` commands for each container, one command starts everything,
the same way on every machine.

**docker run vs docker compose up**
- `docker run` starts one container, and every option (ports, volumes, network, name) is typed by hand each time.
- `docker compose up` reads `compose.yaml`, builds the image if needed, creates the network and volumes,
  and starts all services. The file can be versioned on GitHub and reused. `docker compose down` removes it all.

**How to add a database service?** Add a second service and let the app reach it by its service name:

```yaml
services:
 data-analysis:
  build: .
  depends_on:
   - db
  environment:
   DB_HOST: db
 db:
  image: postgres:16
  environment:
   POSTGRES_PASSWORD: example
  volumes:
   - db-data:/var/lib/postgresql/data
volumes:
 db-data:
```
Compose puts both services on one network, so the app connects to host `db`. The named volume keeps the data
after the container is removed.

## Task 5 questions

**What is Docker and why is it useful in data-science projects?**
Docker packages an application with its libraries and settings into a container that runs the same way on any
machine. In data science this gives reproducible results, no "works on my computer" problems or version conflicts,
easy sharing through Docker Hub and simple deployment.

**Image vs container**
An image is a read-only template made of layers (the recipe). A container is a running instance of an image,
with its own writable layer. One image can create many containers, like one class creates many objects.

**Dockerfile instructions**
- `FROM`: the base image to start from (for example `python:3.12-slim`).
- `WORKDIR`: sets the working folder inside the image (created if missing) for the next instructions.
- `COPY`: copies files from your computer into the image.
- `RUN`: runs a command at build time (for example `pip install`) and saves the result as a layer.
- `CMD`: the default command executed when a container starts (it can be overridden at `docker run`).
