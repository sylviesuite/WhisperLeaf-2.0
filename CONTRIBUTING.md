# Contributing to WhisperLeaf

Thank you for your interest in contributing to WhisperLeaf! This document provides guidelines for contributing to the project while maintaining our core principles of privacy, security, and user sovereignty.

## Code of Conduct

### Our Principles

WhisperLeaf is built on these fundamental principles:

1. **Privacy First**: User privacy and data sovereignty are non-negotiable
2. **Emotional Safety**: User emotional well-being is our highest priority
3. **Transparency**: All code and decisions should be open and explainable
4. **User Control**: Users must maintain complete control over their AI companion
5. **Ethical AI**: AI should benefit users without exploitation or manipulation

### Expected Behavior

- Be respectful and inclusive in all interactions
- Focus on constructive feedback and collaboration
- Respect privacy and security considerations in all contributions
- Prioritize user benefit over technical convenience
- Maintain professional and empathetic communication

## Getting Started

### Development Environment Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/WhisperLeaf.git
   cd WhisperLeaf
   ```

2. **Set up development environment**
   ```bash
   ./scripts/install.sh
   source venv/bin/activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run tests to verify setup**
   ```bash
   python -m pytest tests/ -v
   ```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   python -m pytest tests/ -v
   
   # Run specific test categories
   python -m pytest tests/test_emotional_engine.py
   python -m pytest tests/test_privacy.py
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new emotional analysis feature"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Contribution Guidelines

### Types of Contributions

We welcome various types of contributions:

#### 🐛 Bug Reports
- Use the bug report template
- Include steps to reproduce
- Provide system information
- Respect privacy when sharing logs

#### ✨ Feature Requests
- Use the feature request template
- Explain the use case and benefit
- Consider privacy and security implications
- Align with WhisperLeaf's core principles

#### 🔧 Code Contributions
- Bug fixes
- New features
- Performance improvements
- Documentation updates
- Test coverage improvements

#### 📚 Documentation
- User guides and tutorials
- API documentation
- Code comments and docstrings
- Privacy and security documentation

#### 🧪 Testing
- Unit tests
- Integration tests
- Privacy validation tests
- Performance benchmarks

### Coding Standards

#### Python Code Style

We follow PEP 8 with some specific guidelines:

```python
# Use type hints
def analyze_emotion(text: str, context: Optional[str] = None) -> EmotionAnalysis:
    """Analyze emotional content with optional context.
    
    Args:
        text: The text content to analyze
        context: Optional context for analysis
        
    Returns:
        EmotionAnalysis object with results
        
    Raises:
        ValueError: If text is empty or invalid
    """
    pass

# Use descriptive variable names
emotional_state = analyze_emotion(user_input)
crisis_risk_level = assess_crisis_risk(emotional_state)

# Document privacy-sensitive operations
@privacy_sensitive
def store_emotional_memory(memory: EmotionalMemory) -> str:
    """Store emotional memory with appropriate privacy protection."""
    pass
```

#### Code Organization

```
src/
├── core/           # Core system functionality
├── emotional/      # Emotional processing components
├── curation/       # Content curation features
├── backup/         # Backup and recovery systems
└── utils/          # Shared utilities
```

#### Privacy and Security Guidelines

1. **Data Handling**
   ```python
   # Always use privacy levels
   memory = EmotionalMemory(
       content=user_input,
       privacy_level=PrivacyLevel.ENCRYPTED
   )
   
   # Validate privacy before operations
   if not privacy_validator.can_process(memory):
       raise PrivacyViolationError("Operation not permitted")
   ```

2. **Encryption**
   ```python
   # Use provided encryption utilities
   from src.utils.encryption import encrypt_sensitive_data
   
   encrypted_content = encrypt_sensitive_data(
       data=emotional_content,
       privacy_level=PrivacyLevel.ENCRYPTED
   )
   ```

3. **Constitutional AI Integration**
   ```python
   # Check constitutional rules before actions
   @constitutional_check
   def share_emotional_data(data: EmotionalData, recipient: str):
       """Share emotional data with constitutional validation."""
       pass
   ```

### Testing Requirements

#### Test Categories

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **Privacy Tests**: Validate privacy protection
4. **Security Tests**: Test security measures
5. **Performance Tests**: Validate performance requirements

#### Test Examples

```python
# Unit test example
def test_emotion_detection():
    analyzer = EmotionAnalyzer()
    result = analyzer.analyze("I feel happy today")
    
    assert result.primary_emotion == "joy"
    assert result.confidence > 0.8
    assert result.mood_color == "yellow"

# Privacy test example
def test_privacy_protection():
    memory = create_encrypted_memory("sensitive content")
    
    # Verify encryption
    assert memory.is_encrypted
    assert memory.raw_content != "sensitive content"
    
    # Verify access control
    with pytest.raises(PrivacyViolationError):
        unauthorized_access(memory)

# Integration test example
def test_crisis_detection_workflow():
    crisis_text = "I feel hopeless and want to end it all"
    
    # Process through full pipeline
    analysis = emotional_processor.analyze(crisis_text)
    crisis_assessment = crisis_detector.assess(analysis)
    response = crisis_responder.respond(crisis_assessment)
    
    # Verify appropriate crisis response
    assert crisis_assessment.risk_level == "high"
    assert "crisis resources" in response.content
    assert response.immediate_action_required
```

### Documentation Standards

#### Code Documentation

```python
class EmotionalProcessor:
    """Process and analyze emotional content.
    
    This class provides comprehensive emotional analysis while maintaining
    strict privacy protection and constitutional AI compliance.
    
    Attributes:
        privacy_level: Default privacy level for processing
        constitutional_ai: Constitutional AI validator instance
        
    Example:
        >>> processor = EmotionalProcessor()
        >>> result = processor.analyze("I feel anxious")
        >>> print(result.primary_emotion)
        'anxiety'
    """
    
    def analyze(self, text: str, context: Optional[str] = None) -> EmotionAnalysis:
        """Analyze emotional content with privacy protection.
        
        Args:
            text: The emotional content to analyze
            context: Optional context for more accurate analysis
            
        Returns:
            EmotionAnalysis containing detected emotions, confidence scores,
            and mood classification
            
        Raises:
            ValueError: If text is empty or contains invalid characters
            PrivacyViolationError: If analysis violates privacy rules
            
        Privacy:
            This method processes data locally and never transmits content
            to external services. All analysis results respect the user's
            configured privacy level.
        """
        pass
```

#### API Documentation

Use OpenAPI/Swagger standards for API documentation:

```python
@app.post("/api/v1/emotional/analyze")
async def analyze_emotion(
    request: EmotionAnalysisRequest
) -> EmotionAnalysisResponse:
    """
    Analyze emotional content and return detailed insights.
    
    This endpoint processes emotional text and returns comprehensive
    analysis including primary emotions, mood classification, and
    crisis risk assessment.
    
    - **Privacy**: All processing is local, no external data transmission
    - **Security**: Input is validated and sanitized
    - **Constitutional**: Analysis respects user-defined AI rules
    """
    pass
```

### Pull Request Process

#### Before Submitting

1. **Run all tests**
   ```bash
   python -m pytest tests/ -v --cov=src
   ```

2. **Check code style**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

3. **Update documentation**
   - Update relevant docstrings
   - Update API documentation if needed
   - Update user guides if applicable

4. **Privacy impact assessment**
   - Consider privacy implications
   - Update privacy documentation if needed
   - Ensure constitutional AI compliance

#### Pull Request Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Privacy Impact
- [ ] No privacy impact
- [ ] Minimal privacy impact (explain below)
- [ ] Significant privacy impact (detailed assessment required)

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Privacy tests pass
- [ ] Manual testing completed

## Constitutional AI Compliance
- [ ] Changes comply with constitutional rules
- [ ] No new constitutional violations introduced
- [ ] Constitutional rules updated if necessary

## Documentation
- [ ] Code comments updated
- [ ] API documentation updated
- [ ] User documentation updated
- [ ] Privacy documentation updated

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
```

### Review Process

#### Review Criteria

1. **Functionality**: Does the code work as intended?
2. **Privacy**: Does it maintain privacy protection?
3. **Security**: Are there any security vulnerabilities?
4. **Performance**: Does it meet performance requirements?
5. **Maintainability**: Is the code clean and maintainable?
6. **Documentation**: Is it properly documented?
7. **Testing**: Is it adequately tested?

#### Review Timeline

- **Initial review**: Within 48 hours
- **Follow-up reviews**: Within 24 hours
- **Final approval**: Within 72 hours of submission

### Community Guidelines

#### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community discussion
- **Pull Requests**: Code review and collaboration
- **Documentation**: Guides and tutorials

#### Getting Help

1. **Check existing documentation**
2. **Search existing issues and discussions**
3. **Ask questions in GitHub Discussions**
4. **Join community chat (if available)**

#### Recognition

Contributors are recognized through:

- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in release announcements
- **Community highlights**: Featured in project updates

## Special Considerations

### Privacy-Sensitive Contributions

When working with privacy-sensitive features:

1. **Minimize data exposure** in tests and examples
2. **Use synthetic data** for testing when possible
3. **Document privacy implications** clearly
4. **Follow data minimization principles**
5. **Respect user consent** in all scenarios

### Emotional AI Ethics

When contributing to emotional AI features:

1. **Prioritize user well-being** over technical metrics
2. **Avoid manipulation** or exploitative patterns
3. **Respect emotional vulnerability** in design
4. **Provide appropriate crisis support** resources
5. **Maintain empathetic tone** in all interactions

### Constitutional AI Development

When working with constitutional AI:

1. **Understand existing rules** before making changes
2. **Consider rule interactions** and conflicts
3. **Test constitutional compliance** thoroughly
4. **Document rule changes** clearly
5. **Respect user autonomy** in rule customization

## License

By contributing to WhisperLeaf, you agree that your contributions will be licensed under the same license as the project (GPL-3.0).

## Questions?

If you have questions about contributing, please:

1. Check this document first
2. Search existing GitHub issues and discussions
3. Create a new discussion in GitHub Discussions
4. Contact the maintainers if needed

Thank you for helping make WhisperLeaf better while maintaining our commitment to privacy, security, and user sovereignty! 🌿

