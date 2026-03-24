# DataShift (Python)

A simple tool to move data between databases, converted from the original Java/Spring Boot implementation to Python/FastAPI.

## Features

- **Connection Management**: Create, test, and manage database connections (PostgreSQL, MySQL, SQLite)
- **Pipeline Management**: Define data pipelines between source and target databases
- **Async Execution**: Pipeline runs execute asynchronously with progress tracking
- **Alerting**: Configure alert rules based on pipeline execution metrics
- **Observability**: Built-in metrics, health checks, and execution trends
- **Prometheus Metrics**: Export metrics for monitoring

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with Python type hints
- **Alembic** - Database migrations
- **Pydantic** - Data validation and settings management
- **prometheus-client** - Metrics export

## Getting Started

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Installation

1. Create a virtual environment:
```bash
cd python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Create data directory:
```bash
mkdir -p data
```

5. Run database migrations:
```bash
alembic upgrade head
```

### Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8080

# Or run directly
python -m app.main
```

The API will be available at `http://localhost:8080`

## API Documentation

- **Swagger UI**: http://localhost:8080/swagger-ui.html
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/v3/api-docs

## API Endpoints

### Connections
- `POST /api/v1/connections` - Create a new connection
- `GET /api/v1/connections` - List all connections
- `GET /api/v1/connections/{id}` - Get connection by ID
- `DELETE /api/v1/connections/{id}` - Delete connection
- `POST /api/v1/connections/{id}/test` - Test connection
- `GET /api/v1/connections/{id}/schemas` - Get database schemas

### Pipelines
- `POST /api/v1/pipelines` - Create a new pipeline
- `GET /api/v1/pipelines` - List all pipelines
- `GET /api/v1/pipelines/{id}` - Get pipeline by ID
- `DELETE /api/v1/pipelines/{id}` - Delete pipeline
- `POST /api/v1/pipelines/{id}/run` - Start pipeline execution
- `GET /api/v1/pipelines/{id}/runs` - Get pipeline runs
- `GET /api/v1/pipelines/{id}/runs/{runId}/logs` - Get run logs

### Alerts
- `POST /api/v1/alerts/rules` - Create alert rule
- `GET /api/v1/alerts/rules` - List alert rules
- `DELETE /api/v1/alerts/rules/{id}` - Delete alert rule
- `GET /api/v1/alerts` - List alerts
- `GET /api/v1/alerts/{id}` - Get alert by ID
- `PUT /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

### Observability
- `GET /api/v1/observability/pipelines/metrics` - Global metrics
- `GET /api/v1/observability/pipelines/{id}/stats` - Pipeline stats
- `GET /api/v1/observability/system/health` - System health
- `GET /api/v1/observability/trends` - Execution trends

### Health & Metrics
- `GET /actuator/health` - Health check with component status
- `GET /actuator/health/liveness` - Kubernetes liveness probe
- `GET /actuator/health/readiness` - Kubernetes readiness probe
- `GET /actuator/metrics` - Prometheus metrics

## Configuration

Configuration is done via environment variables (prefix: `DATASHIFT_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASHIFT_DEBUG` | `true` | Enable debug mode |
| `DATASHIFT_DATABASE_URL` | `sqlite+aiosqlite:///./data/datashift.db` | Database connection URL |
| `DATASHIFT_DATABASE_ECHO` | `true` | Log SQL queries |
| `DATASHIFT_ENCRYPTION_KEY` | `datashift-secret-key-16` | AES encryption key (16 bytes) |
| `DATASHIFT_SERVER_PORT` | `8080` | Server port |

### Database URL Examples

```bash
# SQLite (default)
DATASHIFT_DATABASE_URL=sqlite+aiosqlite:///./data/datashift.db

# PostgreSQL
DATASHIFT_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/datashift

# MySQL
DATASHIFT_DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/datashift
```

## Alert Condition Types

- `FAILED_COUNT` - Triggers when failed runs exceed threshold in time window
- `NO_SUCCESS` - Triggers when no successful runs in time window
- `AVG_DURATION` - Triggers when average duration exceeds threshold (in minutes)

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
ruff check app/
```

## Migration from Java

This Python version maintains API compatibility with the original Java/Spring Boot implementation:

- Same REST API endpoints and paths
- Same request/response JSON structure (with camelCase aliases)
- Same database schema
- Same encryption (AES/ECB - note: consider using GCM in production)
- Same alert rule conditions

### Key Differences

| Feature | Java | Python |
|---------|------|--------|
| Web Framework | Spring Boot | FastAPI |
| ORM | JPA/Hibernate | SQLAlchemy |
| Migrations | Liquibase | Alembic |
| Validation | Jakarta Validation | Pydantic |
| Async | @Async | asyncio |
| HTTP Server | Tomcat | Uvicorn |

## License

MIT
