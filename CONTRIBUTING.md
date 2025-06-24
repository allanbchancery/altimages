# Contributing to Matalan Website Accessibility & Widget Analysis Toolkit

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🎯 Project Goals

This toolkit aims to:
- Make web accessibility analysis accessible to developers and organizations
- Provide comprehensive e-commerce website analysis capabilities
- Generate actionable insights for improving website accessibility
- Maintain high code quality and documentation standards

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- Chrome/Chromium browser
- Basic understanding of web accessibility principles
- Familiarity with HTML, CSS, and web scraping concepts

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/altimages.git
   cd altimages
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

4. **Verify Installation**
   ```bash
   python matalan_analyzer_final.py
   ```

## 🔧 Development Workflow

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### Commit Message Format

Use clear, descriptive commit messages:

```
type(scope): brief description

Detailed explanation if needed

- List specific changes
- Reference issues: Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Example Commit Messages

```bash
feat(analyzer): add support for ARIA landmark detection

- Implement ARIA landmark scanning in accessibility analysis
- Add landmark coverage metrics to reports
- Update dashboard to display landmark information
- Fixes #45

fix(dashboard): resolve responsive layout issues on mobile

- Fix table overflow on small screens
- Improve button spacing in mobile view
- Update CSS media queries for better compatibility

docs(readme): update installation instructions

- Add troubleshooting section for common Chrome driver issues
- Include virtual environment setup steps
- Update dependency versions
```

## 📝 Code Standards

### Python Code Style

We follow PEP 8 with some project-specific guidelines:

1. **Line Length**: Maximum 88 characters (Black formatter default)
2. **Imports**: Group imports in this order:
   ```python
   # Standard library imports
   import time
   import json
   
   # Third-party imports
   import requests
   from selenium import webdriver
   
   # Local imports
   from .utils import helper_function
   ```

3. **Docstrings**: Use Google-style docstrings
   ```python
   def analyze_page_accessibility(url: str, page_type: str) -> dict:
       """Analyze a single page for accessibility and widgets.
       
       Args:
           url: The URL to analyze
           page_type: Type of page (homepage, category, product, static)
           
       Returns:
           Dictionary containing analysis results with keys:
           - images: Image accessibility data
           - widgets: Widget detection results
           - accessibility: ARIA and other accessibility features
           
       Raises:
           requests.RequestException: If the page cannot be accessed
           selenium.common.exceptions.TimeoutException: If page load times out
       """
   ```

4. **Type Hints**: Use type hints for function parameters and return values
   ```python
   from typing import Dict, List, Optional, Union
   
   def process_results(data: List[Dict[str, Union[str, int]]]) -> Optional[Dict[str, float]]:
       """Process analysis results and return summary statistics."""
   ```

### Code Formatting

We use automated formatting tools:

```bash
# Format code with Black
black .

# Check code style with flake8
flake8 .

# Sort imports with isort
isort .
```

### Error Handling

Always include proper error handling:

```python
try:
    response = self.session.get(url, timeout=15)
    response.raise_for_status()
except requests.exceptions.Timeout:
    logger.error(f"Timeout accessing {url}")
    return {'error': 'timeout', 'url': url}
except requests.exceptions.RequestException as e:
    logger.error(f"Request failed for {url}: {e}")
    return {'error': str(e), 'url': url}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test file
python -m pytest tests/test_analyzer.py

# Run with verbose output
python -m pytest -v
```

### Writing Tests

Create tests for new functionality:

```python
import pytest
from unittest.mock import Mock, patch
from matalan_analyzer_final import analyze_matalan_product_page

class TestMatalanAnalyzer:
    def test_analyze_product_page_success(self):
        """Test successful product page analysis."""
        # Mock the webdriver and page content
        with patch('matalan_analyzer_final.webdriver.Chrome') as mock_driver:
            mock_driver.return_value.find_elements.return_value = []
            mock_driver.return_value.title = "Test Product"
            
            images, widgets = analyze_matalan_product_page("https://example.com")
            
            assert isinstance(images, list)
            assert isinstance(widgets, dict)
    
    def test_analyze_page_with_invalid_url(self):
        """Test handling of invalid URLs."""
        with pytest.raises(Exception):
            analyze_matalan_product_page("invalid-url")
```

### Test Coverage

Aim for at least 80% test coverage for new code:

- Unit tests for individual functions
- Integration tests for complete workflows
- Mock external dependencies (web requests, browser automation)

## 📊 Adding New Features

### New Analysis Capabilities

When adding new analysis features:

1. **Create a new analyzer function**:
   ```python
   def analyze_new_feature(soup: BeautifulSoup) -> Dict[str, Any]:
       """Analyze new accessibility feature.
       
       Args:
           soup: BeautifulSoup object of the page
           
       Returns:
           Dictionary with analysis results
       """
   ```

2. **Add to existing analysis pipeline**:
   ```python
   # In main analysis function
   new_feature_data = analyze_new_feature(soup)
   result['new_feature'] = new_feature_data
   ```

3. **Update dashboard templates**:
   ```html
   <!-- Add new section to HTML dashboard -->
   <div class="section">
       <h2 class="section-title">🆕 New Feature Analysis</h2>
       <!-- Display new feature data -->
   </div>
   ```

4. **Add tests**:
   ```python
   def test_analyze_new_feature():
       """Test new feature analysis."""
       # Test implementation
   ```

### New Widget Detection

To add detection for new widgets:

1. **Define CSS selectors**:
   ```python
   NEW_WIDGET_SELECTORS = [
       '[data-testid="new-widget"]',
       '.new-widget-class',
       '[aria-label*="new widget"]'
   ]
   ```

2. **Implement detection logic**:
   ```python
   def detect_new_widget(soup: BeautifulSoup) -> Dict[str, Any]:
       """Detect new widget on page."""
       elements = []
       for selector in NEW_WIDGET_SELECTORS:
           elements.extend(soup.select(selector))
       
       return {
           'found': len(elements) > 0,
           'count': len(elements),
           'selectors_used': NEW_WIDGET_SELECTORS
       }
   ```

3. **Add to widget analysis**:
   ```python
   widgets['new_widget'] = detect_new_widget(soup)
   ```

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include type hints for better IDE support
- Document complex algorithms and business logic
- Add inline comments for non-obvious code

### README Updates

When adding new features, update the README:

- Add to feature list
- Update usage examples
- Include new configuration options
- Update sample outputs

### API Documentation

For significant changes, update API documentation:

```python
def new_analysis_function(url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Perform new type of analysis.
    
    This function analyzes web pages for new accessibility features
    and returns structured data about findings.
    
    Args:
        url: The URL to analyze. Must be a valid HTTP/HTTPS URL.
        options: Optional configuration dictionary with keys:
            - timeout: Request timeout in seconds (default: 15)
            - user_agent: Custom user agent string
            - selectors: Custom CSS selectors for detection
    
    Returns:
        Dictionary containing analysis results:
        {
            'url': str,
            'analysis_type': str,
            'results': Dict[str, Any],
            'timestamp': str,
            'success': bool
        }
    
    Raises:
        ValueError: If URL is invalid
        requests.RequestException: If page cannot be accessed
        
    Example:
        >>> result = new_analysis_function('https://example.com')
        >>> print(result['success'])
        True
    """
```

## 🐛 Bug Reports

### Before Submitting

1. Check existing issues to avoid duplicates
2. Test with the latest version
3. Gather relevant information:
   - Python version
   - Operating system
   - Browser version
   - Error messages and stack traces

### Bug Report Template

```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version: 3.x.x
- OS: Windows/macOS/Linux
- Browser: Chrome/Firefox version
- Package versions: (from pip freeze)

## Error Messages
```
Paste error messages and stack traces here
```

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Implementation
How should this feature work?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Screenshots, mockups, or examples
```

## 🔍 Code Review Process

### Submitting Pull Requests

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow code standards
   - Add tests
   - Update documentation

3. **Test your changes**:
   ```bash
   python -m pytest
   black .
   flake8 .
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**:
   - Use the PR template
   - Link related issues
   - Add screenshots for UI changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)

## Related Issues
Fixes #123
Related to #456

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Review Criteria

Pull requests will be reviewed for:

- **Functionality**: Does it work as intended?
- **Code Quality**: Follows standards and best practices?
- **Testing**: Adequate test coverage?
- **Documentation**: Clear and complete?
- **Performance**: No significant performance regressions?
- **Security**: No security vulnerabilities introduced?

## 🏆 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes for significant contributions
- GitHub contributor graphs

## 📞 Getting Help

- **Questions**: Use GitHub Discussions
- **Issues**: Create GitHub Issues
- **Real-time chat**: [Discord/Slack link if available]

## 📋 Checklist for Contributors

Before submitting your contribution:

- [ ] Code follows project style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Pull request template is filled out
- [ ] No merge conflicts
- [ ] Feature is backward compatible (or breaking changes documented)

Thank you for contributing to making the web more accessible! 🌟
