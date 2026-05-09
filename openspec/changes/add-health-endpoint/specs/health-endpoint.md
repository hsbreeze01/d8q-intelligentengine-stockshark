# Delta Spec: Add /api/health endpoint

## ADDED Requirements

### Requirement: Health check endpoint at /api/health

The system SHALL provide a health check endpoint at `GET /api/health` that returns the service status and a server-generated timestamp.

#### Scenario: Successful health check

- **Given** the StockShark service is running
- **When** a client sends `GET /api/health`
- **Then** the system SHALL respond with HTTP 200
- **And** the response body SHALL be JSON containing `"status": "ok"` and a `"timestamp"` field with the current UTC time in ISO 8601 format (e.g. `"2025-01-15T10:30:00Z"`)

#### Scenario: Health response structure

- **Given** the StockShark service is running
- **When** a client sends `GET /api/health`
- **Then** the response JSON SHALL contain exactly the keys `status` and `timestamp`
- **And** the `status` value SHALL be the string `"ok"`
- **And** the `timestamp` value SHALL be a valid ISO 8601 UTC datetime string

### Requirement: Health endpoint registered via Flask blueprint

The health check endpoint SHALL be registered as a Flask blueprint under the existing API prefix, following the same routing pattern used by other API route modules (analysis, search, etc.).

#### Scenario: Blueprint registration

- **Given** the Flask application is created via `create_app()`
- **When** the app registers all blueprints
- **Then** the health blueprint SHALL be registered at `{API_PREFIX}/health`
- **And** it SHALL be accessible without authentication
