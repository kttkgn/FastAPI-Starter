# FastAPI Application Template

A production-ready FastAPI application template with clean architecture, comprehensive documentation, and best practices implementation.

## 🚀 Features

- **Clean Architecture**: Properly structured with domain-driven design principles
- **Type Safety**: Full type hints throughout the codebase
- **API Documentation**: Automatic OpenAPI/Swagger documentation
- **Authentication**: JWT token-based authentication
- **Database**: SQLAlchemy ORM with PostgreSQL support
- **Caching**: Redis integration for performance optimization
- **Background Tasks**: Celery for asynchronous processing
- **Monitoring**: Structured logging and Prometheus metrics
- **Testing**: Comprehensive test suite with pytest
- **CI/CD Ready**: Docker and Kubernetes configuration
- **Development Tools**: Makefile with common commands
- **Linting & Formatting**: Black, isort, flake8, and mypy configuration

## 📁 Project Structure

```
app/
├── adapters/         # External system adapters
│   ├── external/     # External API clients
│   └── persistence/  # Database adapters
├── api/              # API endpoints and routes
├── core/             # Core business logic
│   ├── config.py     # Application configuration
│   └── exceptions.py # Custom exceptions
├── domain/           # Domain models and entities
├── middleware/       # FastAPI middleware
├── schemas/          # Pydantic models for request/response
├── services/         # Business services
└── utils/            # Utility functions
conf/                 # Configuration files
k8s/                  # Kubernetes configuration
scripts/              # Utility scripts
logs/                 # Log files
```

## 🛠️ Installation

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 15 or higher
- Redis 7.0 or higher (for caching and Celery)
- Poetry for dependency management

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies using Poetry:

```bash
# Using Makefile
make setup

# Manual installation
python -m pip install --upgrade pip
python -m pip install poetry
poetry install
```

3. Create environment configuration:

```bash
cp conf/dev.env.example conf/dev.env
# Edit conf/dev.env with your settings
```

4. Initialize the database:

```bash
make init-db
```

## 🚦 Usage

### Development Server

Run the application in development mode with hot reloading:

```bash
make run
```

The application will be available at http://localhost:8000

API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Production Mode

```bash
make run-prod
```

### Testing

Run the test suite:

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make typecheck
```

## 🐳 Docker

Build and run the application using Docker:

```bash
# Build Docker image
make build-docker

# Run Docker container
make run-docker
```

## 🎯 API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/refresh` - Refresh JWT token

### Example Resources

- `GET /api/resources` - Get all resources
- `GET /api/resources/{id}` - Get a specific resource
- `POST /api/resources` - Create a new resource
- `PUT /api/resources/{id}` - Update a resource
- `DELETE /api/resources/{id}` - Delete a resource

## 🔧 Configuration

The application is configured using environment variables in the `.env` files:

- `conf/dev.env` - Development environment
- `conf/prod.env` - Production environment

### Key Configuration Variables

- `APP_NAME`: Name of the application
- `APP_VERSION`: Application version
- `DEBUG`: Enable/disable debug mode
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `JWT_ALGORITHM`: Algorithm for JWT tokens
- `JWT_EXPIRATION`: JWT token expiration time in minutes
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 📝 Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive API documentation
- [Architecture Documentation](docs/architecture.md) - System architecture overview
- [Development Guide](docs/development.md) - Guidelines for developers

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

- Project Maintainer: [Your Name/Team]
- Email: [contact@example.com]
- Issue Tracker: [https://github.com/yourusername/your-repo/issues]
