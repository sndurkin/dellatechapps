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

#### Fixing Collation Version Mismatch

If you see collation version mismatch warnings in the logs, the production setup automatically refreshes the collation version on startup. For manual fixes:

```bash
# Run the refresh command directly
docker exec -it dellatechapps-db-1 psql -U postgres -d postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
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

## Bus Route Image Assets

The bus route visualization feature requires specific image files and coordinate data to function properly. These files must be created manually as they are not included in the repository (the `assets` folder is in `.gitignore`).

### Required Files

Create the following directory structure and files:

```
server/apps/tablet/assets/
├── 0.png
├── 1.png
├── 2.png
├── ...
├── N-1.png
└── image_coords.json
```

### File Descriptions

- **0.png, 1.png, ..., N-1.png**: Map image files used for rendering bus locations. Each image corresponds to a specific geographic region defined in `image_coords.json`.
- **image_coords.json**: JSON file containing coordinate boundaries for each map image. The format is:
  ```json
  [
    {
      "start": [latitude, longitude],
      "end": [latitude, longitude]
    },
    ... N total records ...
  ]
  ```
  Where `start` is the Southwest (SW) point and `end` is the Northeast (NE) point of the map region.

### Setup Instructions

1. Create the assets directory:
   ```bash
   mkdir -p server/apps/tablet/assets
   ```

2. Add your map image files to the `assets` folder.

3. Create `image_coords.json` with the coordinate boundaries for each image. Example:
   ```json
   [
     {
       "start": [34.022974766551066, -84.19690756865513],
       "end": [34.06900147393319, -84.10432701570126]
     },
     {
       "start": [34.034673461770176, -84.15348728998701],
       "end": [34.05768676335601, -84.10632907082613]
     },
     {
       "start": [34.042099363059144, -84.13108151302484],
       "end": [34.053605786899915, -84.10750240344439]
     },
     {
       "start": [34.04607393227104, -84.1177612646545],
       "end": [34.05182706969481, -84.10618869553527]
     }
   ]
   ```

**Note:** The `assets` folder is excluded from version control (via `.gitignore`) to prevent committing large image files. Each developer/deployment must provide these files separately.

### Uploading Assets to Production

The asset files in `server/apps/tablet/assets/` are gitignored but required in production.

Upload using scp:

```bash
scp -r server/apps/tablet/assets/* user@your-droplet:/var/www/dellatechapps/assets/
```

**Note:** Assets only need to be uploaded once (or when they change). The docker-compose volume mount ensures they persist across container rebuilds.

## BusData Cleanup - Daily Scheduled Task

The application includes a management command to automatically clean up old BusData records.

### Management Command

A Django management command has been created at:
`server/apps/tablet/management/commands/cleanup_old_bus_data.py`

**Usage:**

Test with dry-run (no actual deletion):
```bash
python manage.py cleanup_old_bus_data --dry-run
```

Run cleanup (default: deletes records older than 10 days):
```bash
python manage.py cleanup_old_bus_data
```

Customize the retention period:
```bash
python manage.py cleanup_old_bus_data --days 7
```

### Scheduling Options

#### Option 1: Docker Compose Cron Service (Recommended for Production)

A cron service has been added to `docker-compose.prod.yml` that runs the cleanup daily at 2:00 AM.

**To use:**
1. The cron service is already configured in `docker-compose.prod.yml`
2. Start it with: `docker-compose -f docker-compose.prod.yml up -d cron`
3. Check logs: `docker-compose -f docker-compose.prod.yml logs cron`

**To modify the schedule:**
Edit the `crontab` file. Cron format: `minute hour day month weekday`
- `0 2 * * *` = Daily at 2:00 AM
- `0 0 * * *` = Daily at midnight
- `0 */6 * * *` = Every 6 hours

#### Option 2: System Cron (Linux/Mac)

Add to your system crontab (`crontab -e`):

```bash
# Run BusData cleanup daily at 2:00 AM
0 2 * * * cd /path/to/dellatechapps && python manage.py cleanup_old_bus_data >> /var/log/bus_data_cleanup.log 2>&1
```

#### Option 3: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Set action: Start a program
5. Program: `python`
6. Arguments: `manage.py cleanup_old_bus_data`
7. Start in: `C:\projects\dellatechapps`

#### Option 4: Manual Execution

You can also run the command manually whenever needed:
```bash
python manage.py cleanup_old_bus_data
```

### Monitoring

- The command outputs the number of records deleted
- If using Docker cron service, check logs: `docker-compose logs cron`
- Logs are also written to `/var/log/bus_data_cleanup.log` in the cron container

## Networks

The application uses two Docker networks:
- `nginx-web`: Communication between Nginx and Django
- `web-db`: Communication between Django and PostgreSQL
