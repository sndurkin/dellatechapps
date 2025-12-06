# DellaTech Apps

This repository contains a containerized application built with Django, PostgreSQL, and Nginx.

## Project Structure

The application consists of three main services:
- `web`: Django application
- `db`: PostgreSQL database
- `nginx`: Nginx reverse proxy

## Prerequisites

- Docker
- Docker Compose

## Host Configuration

### Setting up Local Domains

1. Edit your hosts file:
   - **Windows**: Open Notepad as Administrator and edit `C:\Windows\System32\drivers\etc\hosts`
   - **Mac/Linux**: Edit `/etc/hosts` with sudo privileges (`sudo nano /etc/hosts`)

2. Add the following line:
   ```
   127.0.0.1 dellatech.local
   ```

3. Save the file and close it.

### Important: Before Running Commands

1. Ensure Docker Desktop is running:
   - Look for the Docker Desktop icon in your system tray
   - If not running, launch Docker Desktop from your Start menu
   - Wait for Docker Desktop to fully initialize (you should see a green light in the bottom left)
   - If you see connection errors, try restarting Docker Desktop

2. Common Docker Desktop Issues:
   - If Docker Desktop won't start, try restarting the Docker service:
     ```bash
     net stop com.docker.service
     net start com.docker.service
     ```
   - If issues persist, you may need to restart Docker Desktop or your computer

## Getting Started

### Basic Commands

#### Starting the Application

Start all services:
```bash
docker-compose up
```

Run in detached mode (background):
```bash
docker-compose up -d
```

#### Stopping the Application

Stop all services:
```bash
docker-compose down
```

Remove all volumes (warning: this will delete database data):
```bash
docker-compose down -v
```

### Monitoring and Logs

View running containers and their status:
```bash
docker-compose ps
```

View logs:
```bash
# All services
docker-compose logs

# Specific service (web, db, or nginx)
docker-compose logs web

# Follow logs in real-time
docker-compose logs -f web
```

### Development Commands

Rebuild services (needed after Dockerfile changes):
```bash
docker-compose build
# or
docker-compose up --build
```

Rebuild services using development Dockerfile:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

Execute commands in containers:
```bash
# Open a shell in the web container
docker-compose exec web bash

# Run Django management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Database Operations

Access PostgreSQL CLI:
```bash
# Using docker exec
docker exec -it dellatechapps-db-1 bash
# Then once inside the container:
psql -U postgres
```

### Shell Access

Access the web service shell:
```bash
# Using docker exec
docker exec -it dellatechapps-web-1 bash
```

## Access Points

- Main application (via Nginx): `http://localhost:80`
- StoryMagic: `http://dellatech.local/storymagic`
- KitchenBuddy: `http://dellatech.local/kitchenbuddy`
- Django development server: `http://localhost:8000`
- PostgreSQL: Port `5432` (internal to Docker network)

## File Locations

- Static files: Served through Nginx from `./server/static`
- Database data: Persisted in Docker volume `postgres_data`

## Environment Variables

The application uses the following environment variables (configured in docker-compose.yml):
- `DEBUG`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

Additional environment variables can be configured in the `.env` file.

## Networks

The application uses two Docker networks:
- `nginx-web`: Communication between Nginx and Django
- `web-db`: Communication between Django and PostgreSQL
