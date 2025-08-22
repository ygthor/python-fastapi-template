# Project Setup Guide

This project uses Python 3.11, FastAPI, NGINX, and Supervisor to run a web application. Follow the steps below to set up and run the project locally or on a server.

## Prerequisites
- Python 3.11 installed
- pip package manager
- NGINX installed
- Supervisor installed
- apt install tesseract-ocr
- apt install -y libgl1

## Setup Instructions

1. **Create a Virtual Environment**
   Create a Python virtual environment to manage dependencies:
   ```bash
   python3.11 -m venv venv
   ```

2. **Activate the Virtual Environment**
   Activate the virtual environment to isolate the project's dependencies:
   ```bash
   source venv/bin/activate
   ```

3. **Install Dependencies**
   Install the required dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Python Version**
   Confirm that the correct Python version is being used:
   ```bash
   python --version
   ```

5. **Configure NGINX**
   Add the following configuration to your NGINX site configuration file (e.g., `/etc/nginx/sites-available/your-app`) to proxy requests to the FastAPI application:
   ```nginx
   location /api {
       proxy_pass http://127.0.0.1:8787/;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
   ```
   - After updating the NGINX configuration, test and reload NGINX:
     ```bash
     sudo nginx -t
     sudo systemctl reload nginx
     ```
   - The application will be accessible at `http://your_domain_name/api`.

6. **Configure Supervisor**
   Create a Supervisor configuration file (e.g., `/etc/supervisor/conf.d/fastapi.conf`) to manage the FastAPI application:
   ```ini
   [program:fastapi]
   command=/home/runcloud/webapps/your-app/start.sh
   directory=/home/runcloud/webapps/your-app
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/fastapi.err.log
   stdout_logfile=/var/log/fastapi.out.log
   user=runcloud
   ```
   - Update Supervisor to apply the configuration:
     ```bash
     sudo supervisorctl reread
     sudo supervisorctl update
     ```

7. **Create Start Script**
   Create a start script (e.g., `/home/runcloud/webapps/your-app/start.sh`) to run the FastAPI application:
   ```bash
   #!/bin/bash
   # Navigate to your project directory
   cd /home/runcloud/webapps/your-app

   # Activate virtual environment
   source venv/bin/activate

   # Start Uvicorn server
   exec uvicorn main:app --reload --host 0.0.0.0 --port 8787
   ```
   - Make the script executable:
     ```bash
     chmod +x /home/runcloud/webapps/your-app/start.sh
     ```

8. **Validate Application is Running**
   Check the status of the FastAPI application managed by Supervisor:
   ```bash
   sudo supervisorctl status
   ```

9. **Run the Application (Manual)**
   If not using Supervisor, you can manually start the FastAPI application:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8787
   ```

## Notes
- Ensure you activate the virtual environment every time you work on the project manually.
- The application will be accessible at `http://your_domain_name/api` when using NGINX.
- Replace `your-app` and `your_domain_name` with your actual application name and domain.
- Logs for the FastAPI application are stored in `/var/log/fastapi.err.log` and `/var/log/fastapi.out.log`.
