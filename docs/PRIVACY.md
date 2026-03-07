# Privacy & Security Guide

## Privacy Philosophy

WhisperLeaf is built on the fundamental principle that **your emotional data belongs to you**. Unlike cloud-based AI services that collect and monetize personal data, WhisperLeaf operates entirely under your control with complete data sovereignty.

### Core Privacy Principles

1. **Local Processing**: All emotional analysis happens on your device
2. **Zero Data Collection**: No telemetry, analytics, or external data transmission
3. **User Control**: You define what data is stored and how it's protected
4. **Transparency**: Open source code allows complete verification
5. **Encryption by Default**: Sensitive data is encrypted using industry standards

## Data Sovereignty

### What Stays Local

**Everything.** WhisperLeaf processes all data locally:

- **Emotional memories** and journal entries
- **Mood analysis** and emotional patterns
- **Crisis detection** assessments
- **Content curation** and filtering
- **Backup data** and system configurations
- **AI model inference** and decision-making

### No External Dependencies

WhisperLeaf operates completely offline after initial setup:

- **No cloud APIs** for emotional analysis
- **No external databases** for data storage
- **No telemetry** or usage tracking
- **No automatic updates** that could compromise privacy
- **No third-party integrations** without explicit user consent

## Encryption and Security

### Multi-Level Data Protection

WhisperLeaf implements multiple layers of security:

#### Level 1: Public Data
- Non-sensitive system information
- Public configuration settings
- Anonymous usage statistics (if enabled)

#### Level 2: Private Data
- Personal memories and journal entries
- Emotional analysis results
- Content curation preferences

#### Level 3: Encrypted Data
- Crisis detection assessments
- Sensitive emotional content
- Personal crisis intervention data
- Constitutional AI decision logs

### Encryption Implementation

**Algorithm**: Fernet (AES 128 in CBC mode with HMAC-SHA256)
**Key Management**: User-controlled encryption keys
**Storage**: Encrypted data stored in local SQLite database

```python
# Example of encryption in action
from cryptography.fernet import Fernet

# User-controlled encryption key
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt sensitive emotional content
encrypted_memory = cipher.encrypt(emotional_content.encode())

# Only you have the key to decrypt
decrypted_memory = cipher.decrypt(encrypted_memory).decode()
```

### Database Security

**Local SQLite Database**:
- Stored on your local filesystem
- Protected by operating system permissions
- Encrypted sensitive tables
- No network access or remote connections

**Access Control**:
- File-level permissions restrict access
- Application-level authentication (optional)
- Constitutional AI governs data access
- Audit logging for all data operations

## Constitutional AI Framework

### Privacy-Preserving Governance

WhisperLeaf includes a Constitutional AI system that enforces privacy rules:

#### Default Constitutional Rules

1. **Privacy Protection Rule**
   - Never share personal data externally
   - Require explicit consent for any data export
   - Block unauthorized access attempts

2. **Data Minimization Rule**
   - Only collect necessary information
   - Automatically purge old data (if configured)
   - Minimize data retention periods

3. **User Autonomy Rule**
   - User has final authority over all data decisions
   - AI cannot override user privacy preferences
   - Transparent decision-making process

4. **Crisis Exception Rule**
   - Emergency protocols may override privacy in life-threatening situations
   - User-configurable crisis response settings
   - Audit trail for all emergency actions

### Customizable Privacy Rules

You can define your own constitutional rules:

```yaml
# config/constitutional_rules.yaml
rules:
  - name: "Strict Privacy"
    description: "Never allow any external data sharing"
    priority: 1
    conditions:
      - action_type: "data_export"
      - external_recipient: true
    decision: "deny"
    
  - name: "Research Participation"
    description: "Allow anonymized research participation with consent"
    priority: 2
    conditions:
      - action_type: "research_data"
      - anonymized: true
      - user_consent: true
    decision: "allow"
```

## Privacy Controls

### Granular Privacy Levels

Control privacy for different types of content:

```python
# Creating memories with different privacy levels
memory_public = {
    "content": "Learned about AI today",
    "privacy_level": "public"  # Shareable, non-sensitive
}

memory_private = {
    "content": "Had a difficult conversation with family",
    "privacy_level": "private"  # Personal, not encrypted
}

memory_encrypted = {
    "content": "Struggling with anxiety about health",
    "privacy_level": "encrypted"  # Highly sensitive, encrypted
}
```

### Data Export Controls

When exporting data, WhisperLeaf respects privacy levels:

- **Public data**: Exported in plain text
- **Private data**: Requires user confirmation
- **Encrypted data**: Requires explicit consent and password

### Automatic Data Protection

**Crisis Detection Privacy**:
- Crisis assessments are automatically encrypted
- Access requires constitutional AI approval
- Emergency contacts can be configured with privacy controls

**Backup Privacy**:
- Backups maintain original privacy levels
- Encrypted backups require user password
- Backup metadata excludes sensitive information

## Network Security

### Local-Only Operation

WhisperLeaf operates without network access:

- **API server** binds to localhost only
- **No outbound connections** for core functionality
- **Firewall friendly** - no open ports required
- **Air-gap compatible** for maximum security

### Optional Network Features

If you choose to enable network features:

**Content Curation**:
- RSS feeds fetched over HTTPS
- Web scraping uses secure connections
- Content filtered before local storage
- No personal data transmitted

**System Updates**:
- Manual update process only
- Cryptographic signature verification
- User approval required for all updates

## Compliance and Standards

### Privacy Regulations

WhisperLeaf is designed to comply with major privacy regulations:

**GDPR (General Data Protection Regulation)**:
- ✅ Data minimization by design
- ✅ User control and consent mechanisms
- ✅ Right to data portability
- ✅ Right to erasure (deletion)
- ✅ Privacy by design and default

**CCPA (California Consumer Privacy Act)**:
- ✅ No sale of personal information
- ✅ User control over data collection
- ✅ Transparent privacy practices
- ✅ Right to delete personal information

**HIPAA (Healthcare Privacy)**:
- ✅ Local data storage only
- ✅ Encryption of sensitive health information
- ✅ Access controls and audit logging
- ✅ No unauthorized disclosures

### Security Standards

**Encryption**: NIST-approved algorithms (AES, SHA-256)
**Key Management**: User-controlled key generation and storage
**Access Control**: Role-based permissions with audit trails
**Data Integrity**: Cryptographic checksums and validation

## Privacy Best Practices

### For Users

1. **Strong Passwords**: Use unique, strong passwords for encryption
2. **Regular Backups**: Maintain encrypted backups of important data
3. **System Updates**: Keep WhisperLeaf updated for security patches
4. **Access Control**: Limit physical access to your device
5. **Network Security**: Use secure networks for any optional online features

### For Developers

1. **Code Review**: All privacy-related code undergoes peer review
2. **Security Testing**: Regular penetration testing and vulnerability assessment
3. **Minimal Dependencies**: Reduce attack surface through minimal external dependencies
4. **Audit Logging**: Comprehensive logging of all data access and modifications
5. **Documentation**: Clear documentation of all privacy and security features

## Threat Model

### Threats We Protect Against

**External Attackers**:
- ✅ Network-based attacks (no network exposure)
- ✅ Data interception (local processing only)
- ✅ Cloud provider breaches (no cloud dependencies)
- ✅ Government surveillance (local data sovereignty)

**Malicious Software**:
- ✅ Data exfiltration (encrypted sensitive data)
- ✅ Unauthorized access (access controls and permissions)
- ✅ Data corruption (integrity checks and backups)

**Physical Access**:
- ✅ Device theft (encrypted data storage)
- ✅ Unauthorized local access (authentication and permissions)
- ✅ Data recovery attacks (secure deletion methods)

### Limitations

**What We Cannot Protect Against**:
- Compromised operating system with root access
- Physical memory attacks on running system
- User sharing of encryption keys or passwords
- Social engineering attacks targeting users directly

## Privacy Verification

### Open Source Transparency

Verify WhisperLeaf's privacy claims:

1. **Source Code Review**: All code is open source and auditable
2. **Network Monitoring**: Use tools like Wireshark to verify no external connections
3. **File System Monitoring**: Monitor file access to verify local-only storage
4. **Process Monitoring**: Verify no unauthorized processes or network connections

### Independent Audits

WhisperLeaf welcomes independent security and privacy audits:

- **Code audits** by security researchers
- **Privacy assessments** by privacy advocates
- **Penetration testing** by ethical hackers
- **Academic research** on privacy-preserving AI

## Incident Response

### Privacy Breach Protocol

In the unlikely event of a privacy incident:

1. **Immediate Assessment**: Determine scope and impact
2. **User Notification**: Immediate notification to affected users
3. **Mitigation**: Steps to prevent further exposure
4. **Investigation**: Root cause analysis and remediation
5. **Transparency**: Public disclosure of incident and response

### Reporting Security Issues

Report security vulnerabilities responsibly:

- **Email**: security@whisperleaf.org
- **PGP Key**: Available on our website
- **Bug Bounty**: Rewards for responsible disclosure
- **Response Time**: 24-48 hours for initial response

## Future Privacy Enhancements

### Planned Features

**Advanced Encryption**:
- Homomorphic encryption for analysis on encrypted data
- Zero-knowledge proofs for privacy-preserving verification
- Quantum-resistant encryption algorithms

**Enhanced Anonymization**:
- Differential privacy for statistical analysis
- K-anonymity for research data sharing
- Advanced anonymization techniques

**Decentralized Features**:
- Peer-to-peer backup networks
- Decentralized identity management
- Blockchain-based audit trails

### Research Initiatives

WhisperLeaf contributes to privacy research:

- **Privacy-preserving AI** techniques
- **Federated learning** for emotional AI
- **Secure multi-party computation** for collaborative analysis
- **Homomorphic encryption** applications in emotional computing

---

**Your privacy is not just a feature—it's the foundation of everything WhisperLeaf does.**

For questions about privacy and security, please see our [FAQ](FAQ.md) or contact us through our [secure channels](CONTACT.md).

