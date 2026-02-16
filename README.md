# GMU DAEN Capstone Project - GitHub Repository Structure

## Overview

This repository provides a standardized directory structure for **George Mason University (GMU) College of Engineering and Computing (CEC) Data Analytics Engineering (DAEN) Program Capstone Projects**. This structure has been designed to accommodate the typical requirements of DAEN capstone projects, which are generally Python-based, include graphical user interfaces (GUIs), utilize Docker containerization.

---

## Directory Structure

```
.
├── docker/                   # Store all the dockerfile for each implementation.
│   ├── api/                  # Dockerfile to run the fastapi.
│   ├── db-init-scripts/      # Initial for setting up postgis and db.
│   ├── flows_package/        # Dockerfile for prefect.
│   └── nginx/                # Nginx configuration file.
├── prefect/                  # Prefect main folder.
│   └── flows/                # Store all the pipeline flows.
├── backend/                  # Backend main code.
│   └── api/                  # FastAPI implementation.
├── shared/                   # Shared function for all the code.
├── secrets/                  # Store all the credentials and secrets.
├── .gitignore                # Git ignore file.
├── docker-compose.yaml       # Docker compose file for prefect and fastapi.
├── LICENSE                   # MIT License
└── README.md                 # This file - project documentation.
```

---

## Detailed Directory Descriptions

### `docker/`
**Purpose:** Contains all Docker-related configurations for containerizing the application.

- **`api/`**: Dockerfile and configuration for the FastAPI application container.
- **`db-init-scripts/`**: Initialization scripts for setting up PostGIS database, creating users, databases, and schemas.
- **`flows_package/`**: Dockerfile for the Prefect worker container that runs data pipeline flows.
- **`nginx/`**: Configuration files for NGINX reverse proxy.

**Common Files:**
- `Dockerfile`: Instructions for building Docker images
- `.dockerignore`: Files to exclude from Docker context
- Initialization scripts and startup commands

**Key Services:**
- **postgis**: PostgreSQL database with PostGIS extension (user: `prefect`/`developer`, database: `prefect`/`app`)
- **redis**: Message broker for Prefect
- **prefect-server**: Prefect orchestration server
- **prefect-services**: Prefect background services
- **prefect-worker**: Executes Prefect flows (NOAA-pool, flight-pool)
- **fastapi**: REST API server
- **nginx**: Reverse proxy on port 4200

---

### `prefect/`
**Purpose:** Contains Prefect workflow orchestration code.

- **`flows/`**: Prefect flow definitions for data pipelines (e.g., NOAA weather data, flight data ingestion).

**Environment Variables:**
- `PREFECT_API_URL`: Connection to Prefect server
- `DATABASE_URL`: PostgreSQL connection for application data (uses `developer` user and `app` database)

**Work Pools:**
- `NOAA-pool`: Process pool for weather data workflows
- `flight-pool`: Process pool for flight data workflows

---

### `backend/`
**Purpose:** Backend application code.

- **`api/`**: FastAPI application with REST endpoints, route definitions, and request handlers.

**Database Connection:**
- Host: `postgis` container
- Database: `${DEVELOPER_DB}`
- User: `${DEVELOPER_USER}`
- Password: `${DEVELOPER_PASSWORD}` (from environment)
- Port: 8000 (exposed)

---

### `shared/`
**Purpose:** Reusable utility functions and helper modules shared across services (Prefect flows, FastAPI, etc.).

**Common Use Cases:**
- Data validation functions
- Format converters
- Database utilities
- Common constants and configurations

---

### `secrets/`
**Purpose:** Stores credentials and sensitive configuration files.

**Security Note:** 
- **NEVER** commit this folder to version control
- Add `secrets/` to `.gitignore`
- Use environment variables for sensitive data
- Consider using secret management tools (Docker secrets, AWS Secrets Manager, etc.)

**Common Files:**
- API keys
- Database credentials
- OAuth tokens
- SSL certificates
- PyOpenSky settings: `${PYOPENSKY_SETTINGS}` mounted to `/root/.config/pyopensky/settings.conf`

---

## Root-Level Files

### `.gitignore`
Specifies files and directories that Git should ignore (e.g., `__pycache__/`, `*.pyc`, `data/`, `logs/`, `.env`, `secrets/`, virtual environments).

### `LICENSE`
MIT License - This project is open source software licensed under the MIT License.

### `README.md`
This file. Provides an overview of the project, setup instructions, and directory structure documentation.

### `docker-compose.yaml`
Defines multi-container Docker applications with the following services:
- PostGIS database with two databases (`prefect` for Prefect metadata, `app` for application data)
- Redis for message brokering
- Prefect server, services, and workers
- FastAPI application
- NGINX reverse proxy

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- Environment variables configured in `.env` file

### Required Environment Variables

Create a `.env` file in the project root with:

```bash
DEVELOPER_PASSWORD=your_developer_password
READONLY_PASSWORD=your_readonly_password
PYOPENSKY_SETTINGS=/path/to/pyopensky/settings.conf
```

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd capstone
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the services:**
   - Prefect UI: http://localhost:4200
   - FastAPI: http://localhost:8000
   - FastAPI Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432

---

## Database Configuration

### PostgreSQL Databases

**Prefect Metadata Database:**
- Database: `prefect`
- User: `prefect`
- Password: `prefect`
- Connection String: `postgresql+asyncpg://prefect:prefect@postgis:5432/prefect`

**Application Database:**
- Database: `${DEVELOPER_DB}`
- User: `${DEVELOPER_USER}`
- Password: `${DEVELOPER_PASSWORD}`
- Connection String: `postgresql://${DEVELOPER_USER}:${DEVELOPER_PASSWORD}@postgis:5432/${DEVELOPER_DB}`

---

## Development Workflow

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test locally:**
   - Add Prefect flows in `prefect/flows/`
   - Add API endpoints in `backend/api/`
   - Add shared utilities in `shared/`

3. **Rebuild and restart containers:**
   ```bash
   docker-compose down
   docker-compose up --build
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f [service_name]
   ```

5. **Commit and push:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/your-feature-name
   ```

---

## Contributing

Please follow these guidelines:
- Follow PEP 8 style guidelines for Python code
- Write meaningful commit messages
- Add documentation for new features
- Test changes before submitting pull requests
- Never commit secrets or credentials

---

## Support and Resources

- **GMU DAEN Program:** https://analyticsengineering.gmu.edu/
- **Prefect Documentation:** https://docs.prefect.io/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Docker Documentation:** https://docs.docker.com/
- **PostGIS Documentation:** https://postgis.net/documentation/

---

# Apache License
Version 2.0, January 2004  
http://www.apache.org/licenses/

Copyright 2026 GMU DAEN Capstone Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Contact

For questions about this project or the DAEN Capstone program, contact:
- Project Team: [Team Email/Contact]
- Faculty Advisor: [Advisor Name and Email]
- Program Coordinator: [Coordinator Contact]

---

**Last Updated:** February 2026

