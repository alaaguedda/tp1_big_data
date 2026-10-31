# Base image: Python 3.12 (slim = small size)
FROM python:3.12-slim

# Show Python prints immediately in docker logs
ENV PYTHONUNBUFFERED=1
# SERVE=0: run the analysis and exit. SERVE=1: also serve the dashboard on port 8000
ENV SERVE=0

# Working folder inside the container
WORKDIR /app

# Install the libraries first (this layer is cached if requirements.txt does not change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ src/
COPY run_pipeline.sh .

# Port used when SERVE=1
EXPOSE 8000

# Command executed when the container starts
CMD ["bash", "run_pipeline.sh"]
