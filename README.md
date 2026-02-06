# DataShift

A simple tool to move data between databases using Java + Spring Boot.

## Features
- Database Connections management (stores DB details)
- Pipelines to link source to target tables
- PipelineRun tracking (foundation)
- REST APIs for CRUD on connections and pipelines
- H2 for testing, Liquibase for schema
- Swagger UI for API docs

## Tech Stack
- Spring Boot 3.2.5
- JPA / Hibernate
- H2 Database (in-memory)
- Liquibase
- Springdoc OpenAPI (Swagger)
- Lombok

## Quick Start

1. Run the application:
   ```
   mvn spring-boot:run
   ```

2. Access:
   - API: http://localhost:8080/api/connections , http://localhost:8080/api/pipelines
   - Swagger UI: http://localhost:8080/swagger-ui.html
   - H2 Console: http://localhost:8080/h2-console (JDBC URL: jdbc:h2:mem:datashift)

3. Example usage:
   - POST /api/connections to create connection
   - POST /api/pipelines to create pipeline (requires existing connections)

## Future Extensions
- Actual data migration logic
- Scheduling (e.g., Quartz)
- More databases support
- Security, auth, encryption for passwords
- etc.

