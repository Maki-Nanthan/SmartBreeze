<<<<<<< HEAD
# Smart Classroom Edge AI System

This project is a clean starter scaffold for a Smart Classroom Edge AI System.

## Project Structure

- frontend/ - React + TypeScript + Vite client application
  - src/pages/ - page-level views
  - src/components/ - reusable UI components
  - src/services/ - API and client services
  - src/types/ - shared TypeScript types
  - src/hooks/ - custom React hooks
  - src/utils/ - utility helpers
- backend/ - FastAPI application
  - app/routers/ - API endpoints
  - app/services/ - business logic
  - app/schemas/ - request/response schemas
  - app/models/ - database models
  - app/database/ - database setup and helpers
  - app/core/ - shared configuration and utilities

## Backend

The FastAPI backend foundation is now in place.

### What is included

- FastAPI application entry point
- CORS support for local frontend development
- Environment-based configuration
- Health endpoint at /api/health
- Shared classroom state schema with occupancy and control mode enums
- Service layer for classroom state management
- Basic validation and HTTP error handling
- OpenAPI/Swagger documentation

### Run the backend

From the backend directory, run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API docs will be available at:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Current Status

The backend foundation has been implemented. Feature logic will be added later.
=======
# SmartBreeze
>>>>>>> 3b98996496d6acc3af5d255e1efc884a2c6d4a56
