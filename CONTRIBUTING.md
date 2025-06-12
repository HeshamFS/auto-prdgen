# Contributing to PRD Creator CLI

Thank you for your interest in contributing to PRD Creator CLI! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Test your changes thoroughly
6. Submit a pull request

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HeshamFS/auto-prdgen.git
   cd auto-prdgen
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google API key
   ```

## Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

## Testing

- Test your changes with various PRD scenarios
- Ensure all existing functionality still works
- Add tests for new features when applicable

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the version number in setup.py following semantic versioning
3. Ensure your code follows the established patterns
4. Write clear commit messages
5. Submit your pull request with a clear description

## Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant error messages or logs

## Feature Requests

We welcome feature requests! Please:
- Check if the feature already exists or is planned
- Provide a clear use case
- Explain how it would benefit users
- Consider implementation complexity

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming environment for all contributors.

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.