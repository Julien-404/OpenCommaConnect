# Contributing to Comma Connect Self-Hosted Server

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourorg/comma-connect-server
cd comma-connect-server

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f
```

### Backend Development

The backend is built with FastAPI (Python).

```bash
cd backend/api

# Install dependencies
pip install -r requirements.txt

# Run locally (without Docker)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

The frontend is built with React and TypeScript.

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start

# Build for production
npm run build
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Format with Black (line length 100)
- Sort imports with isort

### TypeScript/React

- Use TypeScript strict mode
- Follow ESLint rules
- Use functional components with hooks
- Write prop types for all components

## Testing

### Backend Tests

```bash
cd backend/api
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Pull Request Process

1. **Update Documentation**: If you change functionality, update the relevant documentation
2. **Add Tests**: Add tests for new features
3. **Follow Code Style**: Ensure code follows project style guidelines
4. **One Feature Per PR**: Keep pull requests focused on a single feature or fix
5. **Descriptive Commit Messages**: Write clear commit messages explaining what and why

### Commit Message Format

```
type(scope): brief description

Detailed explanation of what changed and why.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Areas for Contribution

### High Priority

- [ ] Advanced log parsing (capnproto)
- [ ] Video transcoding optimization
- [ ] Event detection algorithms
- [ ] Mobile app development
- [ ] Performance optimizations

### Medium Priority

- [ ] Additional map tile sources
- [ ] Route sharing enhancements
- [ ] Analytics dashboard
- [ ] Multi-language support
- [ ] Plugin system

### Documentation

- [ ] API documentation improvements
- [ ] Setup guides for different platforms
- [ ] Video tutorials
- [ ] Troubleshooting guides

## Questions or Issues?

- Open an issue on GitHub
- Join our Discord server
- Check existing documentation

## Code of Conduct

Be respectful and constructive in all interactions. We're building this together!

---

Thank you for contributing to making openpilot data management better for everyone!
