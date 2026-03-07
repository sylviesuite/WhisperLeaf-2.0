# WhisperLeaf API Documentation

## Overview

WhisperLeaf provides a comprehensive RESTful API that enables programmatic access to all system capabilities including emotional processing, memory management, content curation, and system administration.

**Base URL**: `http://localhost:8000`  
**API Version**: v1  
**Authentication**: API Key (optional for local use)

## Authentication

For local installations, authentication is optional. For production deployments, include your API key in the header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/v1/endpoint
```

## Core Endpoints

### Health Check

**GET** `/health`

Returns system health status and component information.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "2 days, 14:32:15",
  "components": {
    "database": "connected",
    "emotional_engine": "operational",
    "content_curator": "active",
    "backup_system": "enabled",
    "constitutional_ai": "enforcing 7 rules"
  }
}
```

## Memory Management API

### Create Memory

**POST** `/api/v1/memories`

Creates a new memory entry with optional emotional context.

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Had a wonderful conversation with a friend today",
    "memory_type": "journal",
    "mood": "happy",
    "privacy_level": "private",
    "tags": ["friendship", "conversation"]
  }'
```

**Request Body:**
```json
{
  "content": "string (required)",
  "memory_type": "journal|emotional|general",
  "mood": "string (optional)",
  "privacy_level": "public|private|encrypted",
  "tags": ["array of strings"],
  "location": "string (optional)",
  "metadata": "object (optional)"
}
```

**Response:**
```json
{
  "id": "mem_123456789",
  "content": "Had a wonderful conversation with a friend today",
  "memory_type": "journal",
  "mood": "happy",
  "privacy_level": "private",
  "created_at": "2025-07-20T14:30:00Z",
  "tags": ["friendship", "conversation"],
  "emotional_analysis": {
    "primary_emotion": "joy",
    "confidence": 0.92,
    "mood_color": "yellow"
  }
}
```

### Retrieve Memories

**GET** `/api/v1/memories`

Retrieves memories with optional filtering and pagination.

```bash
curl "http://localhost:8000/api/v1/memories?mood=happy&limit=10&offset=0"
```

**Query Parameters:**
- `mood`: Filter by mood (string)
- `memory_type`: Filter by type (journal|emotional|general)
- `tags`: Filter by tags (comma-separated)
- `date_from`: Start date (ISO 8601)
- `date_to`: End date (ISO 8601)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

### Search Memories

**GET** `/api/v1/memories/search`

Advanced search across memory content and metadata.

```bash
curl "http://localhost:8000/api/v1/memories/search?q=friendship&emotional_context=positive"
```

**Query Parameters:**
- `q`: Search query (string)
- `emotional_context`: positive|negative|neutral
- `time_range`: today|week|month|year
- `similarity_threshold`: 0.0-1.0 (for semantic search)

## Emotional Processing API

### Analyze Emotion

**POST** `/api/v1/emotional/analyze`

Analyzes emotional content and returns detailed emotional insights.

```bash
curl -X POST http://localhost:8000/api/v1/emotional/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I feel overwhelmed with work and stressed about deadlines",
    "context": "work_related"
  }'
```

**Response:**
```json
{
  "primary_emotion": "stress",
  "secondary_emotions": ["anxiety", "overwhelm"],
  "mood_color": "red",
  "intensity": 0.78,
  "confidence": 0.91,
  "crisis_risk": "low",
  "recommendations": [
    "Consider taking short breaks",
    "Practice deep breathing exercises"
  ],
  "emotional_patterns": {
    "trend": "increasing_stress",
    "frequency": "recurring_weekly"
  }
}
```

### Mood Timeline

**GET** `/api/v1/emotional/timeline`

Retrieves emotional patterns and mood trends over time.

```bash
curl "http://localhost:8000/api/v1/emotional/timeline?period=week&granularity=day"
```

**Query Parameters:**
- `period`: day|week|month|year
- `granularity`: hour|day|week
- `mood_colors`: Filter by specific mood colors

### Crisis Detection

**POST** `/api/v1/emotional/crisis-check`

Performs crisis risk assessment on provided content.

```bash
curl -X POST http://localhost:8000/api/v1/emotional/crisis-check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I feel hopeless and nothing seems to matter anymore",
    "user_context": "recent_loss"
  }'
```

**Response:**
```json
{
  "risk_level": "high",
  "confidence": 0.89,
  "risk_factors": [
    "hopelessness_indicators",
    "meaning_loss_patterns"
  ],
  "immediate_actions": [
    "Contact mental health professional",
    "Reach out to trusted friend or family"
  ],
  "resources": [
    {
      "name": "National Suicide Prevention Lifeline",
      "phone": "988",
      "available": "24/7"
    }
  ],
  "follow_up_recommended": true
}
```

## Content Curation API

### Add Content Source

**POST** `/api/v1/curation/sources`

Adds a new content source for monitoring and curation.

```bash
curl -X POST http://localhost:8000/api/v1/curation/sources \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/rss",
    "source_type": "rss",
    "name": "Tech News",
    "categories": ["technology", "innovation"],
    "quality_threshold": 0.7
  }'
```

### Get Curated Content

**GET** `/api/v1/curation/content`

Retrieves curated content based on user interests and quality scores.

```bash
curl "http://localhost:8000/api/v1/curation/content?category=technology&quality_min=0.8"
```

**Response:**
```json
{
  "content": [
    {
      "id": "content_123",
      "title": "Breakthrough in AI Research",
      "url": "https://example.com/article",
      "summary": "Researchers achieve new milestone...",
      "quality_score": 0.92,
      "relevance_score": 0.87,
      "source": "Tech News",
      "published_at": "2025-07-20T10:00:00Z",
      "categories": ["technology", "ai"],
      "reading_time": "5 minutes"
    }
  ],
  "total": 1,
  "page": 1,
  "has_more": false
}
```

## Backup and Recovery API

### Create Backup

**POST** `/api/v1/backup/create`

Creates a system backup with specified options.

```bash
curl -X POST http://localhost:8000/api/v1/backup/create \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "full",
    "include_encrypted": true,
    "compression": true
  }'
```

**Response:**
```json
{
  "backup_id": "backup_20250720_143000",
  "backup_type": "full",
  "size": "245.7 MB",
  "created_at": "2025-07-20T14:30:00Z",
  "file_path": "/backups/backup_20250720_143000.tar.gz",
  "checksum": "sha256:abc123...",
  "status": "completed"
}
```

### List Backups

**GET** `/api/v1/backup/list`

Lists available backups with metadata.

```bash
curl http://localhost:8000/api/v1/backup/list
```

### Restore from Backup

**POST** `/api/v1/backup/restore`

Restores system from a specified backup.

```bash
curl -X POST http://localhost:8000/api/v1/backup/restore \
  -H "Content-Type: application/json" \
  -d '{
    "backup_id": "backup_20250720_143000",
    "restore_type": "selective",
    "components": ["memories", "configuration"]
  }'
```

## Constitutional AI API

### Get Active Rules

**GET** `/api/v1/constitutional/rules`

Retrieves currently active constitutional rules.

```bash
curl http://localhost:8000/api/v1/constitutional/rules
```

### Evaluate Decision

**POST** `/api/v1/constitutional/evaluate`

Evaluates a proposed action against constitutional rules.

```bash
curl -X POST http://localhost:8000/api/v1/constitutional/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "share_emotional_data",
    "context": "research_request",
    "user_consent": false
  }'
```

**Response:**
```json
{
  "allowed": false,
  "violated_rules": [
    {
      "rule_name": "Privacy Protection",
      "severity": "high",
      "reason": "User consent required for data sharing"
    }
  ],
  "recommendations": [
    "Request explicit user consent",
    "Anonymize data before sharing"
  ]
}
```

## WebSocket API

### Real-time Emotional Monitoring

Connect to WebSocket for real-time emotional state updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/emotional');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Emotional update:', data);
};

// Send emotional content for real-time analysis
ws.send(JSON.stringify({
  type: 'analyze',
  content: 'Feeling anxious about the presentation tomorrow'
}));
```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "mood",
      "issue": "Must be one of: happy, sad, angry, anxious, calm"
    }
  },
  "request_id": "req_123456789"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input parameters
- `NOT_FOUND`: Requested resource not found
- `UNAUTHORIZED`: Authentication required
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `CONSTITUTIONAL_VIOLATION`: Action blocked by constitutional rules

## Rate Limiting

API endpoints are rate-limited to ensure system stability:

- **General endpoints**: 100 requests per minute
- **Emotional analysis**: 50 requests per minute
- **Backup operations**: 5 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

## SDK and Libraries

### Python SDK

```python
from whisperleaf import WhisperLeafClient

client = WhisperLeafClient(base_url="http://localhost:8000")

# Create a memory
memory = client.memories.create(
    content="Had a great day at the park",
    mood="happy",
    tags=["outdoor", "relaxation"]
)

# Analyze emotion
analysis = client.emotional.analyze(
    text="Feeling stressed about work deadlines"
)

print(f"Primary emotion: {analysis.primary_emotion}")
print(f"Mood color: {analysis.mood_color}")
```

### JavaScript SDK

```javascript
import { WhisperLeafClient } from 'whisperleaf-js';

const client = new WhisperLeafClient({
  baseUrl: 'http://localhost:8000'
});

// Create memory
const memory = await client.memories.create({
  content: 'Learned something new today',
  mood: 'curious',
  tags: ['learning', 'growth']
});

// Get emotional timeline
const timeline = await client.emotional.getTimeline({
  period: 'week',
  granularity: 'day'
});
```

## Integration Examples

### Webhook Integration

Configure webhooks to receive notifications:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["crisis_detected", "backup_completed"],
    "secret": "your_webhook_secret"
  }'
```

### Batch Processing

Process multiple items efficiently:

```bash
curl -X POST http://localhost:8000/api/v1/batch/emotional/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"text": "First emotional content"},
      {"text": "Second emotional content"},
      {"text": "Third emotional content"}
    ]
  }'
```

This API documentation provides comprehensive coverage of WhisperLeaf's capabilities. For additional examples and advanced usage patterns, see the [User Guide](USER_GUIDE.md) and [Integration Examples](INTEGRATION.md).

