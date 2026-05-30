# Alignment MCP Server

A custom MCP (Model Context Protocol) server for the cross-team PM pipeline. It exposes a single tool, `score_alignment`, which takes a team's completed deliverables and goals, and returns semantic-similarity match scores per goal plus the deliverable IDs that support each goal.

## Features

- **Deterministic Scoring**: Pure mathematical calculations, no external data fetching
- **Two Backends**:
  - `embeddings` (default): sentence-transformers for semantic similarity
  - `tfidf`: scikit-learn TF-IDF for offline/lexical matching
- **Threshold-based Matching**: Configurable similarity threshold for determining supporting deliverables
- **Detailed Results**: Per-goal match scores and per-deliverable breakdown

## Installation

### 1. Clone or Download

```bash
cd traecy_mcp
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using the package:

```bash
pip install -e .
```

### 4. Pre-download Embedding Model (Recommended)

If using the default `embeddings` backend, pre-download the model to avoid delays:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Backend selection: "embeddings" (default) or "tfidf"
ALIGNMENT_BACKEND=embeddings
```

### Backend Options

**embeddings** (default):
- Uses sentence-transformers `all-MiniLM-L6-v2`
- Better semantic understanding (synonyms, paraphrase)
- Requires first-run model download from Hugging Face
- Default threshold: 0.40

**tfidf**:
- Uses scikit-learn TF-IDF cosine similarity
- No download required, fully offline
- Faster but lexical-only
- Recommended threshold: 0.10

## Usage

### Running the MCP Server

```bash
python alignment_server.py
```

The server uses stdio transport by default, suitable for MCP integration.

### TRAE Configuration

In TRAE settings, add this custom MCP:

```json
{
  "command": "python",
  "args": ["/absolute/path/to/alignment_server.py"],
  "env": {}
}
```

For TF-IDF backend:

```json
{
  "command": "python",
  "args": ["/absolute/path/to/alignment_server.py"],
  "env": {
    "ALIGNMENT_BACKEND": "tfidf"
  }
}
```

### Tool: score_alignment

#### Input Schema

```json
{
  "deliverables": [
    {
      "id": "string",
      "title": "string",
      "description": "string"
    }
  ],
  "goals": [
    {
      "goal_id": "string",
      "goal_text": "string"
    }
  ],
  "threshold": 0.40
}
```

#### Output Schema

```json
{
  "backend": "embeddings",
  "threshold": 0.40,
  "results": [
    {
      "goal_id": "string",
      "goal_text": "string",
      "match_score": 0.85,
      "supporting_deliverables": ["deliv-1", "deliv-3"],
      "per_deliverable": [
        {"id": "deliv-1", "score": 0.85},
        {"id": "deliv-2", "score": 0.32}
      ]
    }
  ]
}
```

#### Example Usage

```python
from alignment_server import score_alignment

deliverables = [
    {
        "id": "deliv-1",
        "title": "User authentication system",
        "description": "Implemented OAuth2 login with Google and GitHub providers"
    },
    {
        "id": "deliv-2",
        "title": "Performance dashboard",
        "description": "Created real-time monitoring dashboard for system metrics"
    }
]

goals = [
    {
        "goal_id": "goal-1",
        "goal_text": "Improve user onboarding experience"
    },
    {
        "goal_id": "goal-2",
        "goal_text": "Increase system reliability"
    }
]

result = score_alignment(deliverables, goals, threshold=0.40)
print(result)
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
traecy_mcp/
├── alignment_server.py     # Main MCP server implementation
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
├── .env.example            # Environment variables template
├── README.md               # This file
└── tests/                  # Unit tests (optional)
    └── test_alignment.py
```

## Design Philosophy

- **Pure Mathematics**: Scoring is deterministic and reproducible
- **No External Data**: All data is passed in by the calling agent
- **Separation of Concerns**: Scoring happens here; qualitative judgment is the agent's job
- **Offline-First**: TF-IDF backend works without internet

## Troubleshooting

### Model Download Issues

If using `embeddings` backend and the model fails to download:

1. Pre-download at home with good internet
2. Use `tfidf` backend instead (set `ALIGNMENT_BACKEND=tfidf`)

### Threshold Tuning

If results seem off:

- **Too few supporting deliverables**: Lower the threshold
- **Too many false positives**: Raise the threshold
- Backend-specific thresholds (see above)

## License

Internal use for cross-team PM pipeline.
