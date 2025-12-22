# Monlam Doccano

Custom [Doccano](https://github.com/doccano/doccano) annotation platform with Tibetan language support and Monlam AI enhancements.

![Monlam Tools](branding/static/logo.png)

## Features

### 🇹🇴 Tibetan Language Support
- Full Tibetan (བོད་སྐད་) UI translations
- Monlam Unicode font support
- RTL-compatible text handling

### 🎨 Monlam Branding
- Custom color scheme (gold/navy)
- Monlam logo and favicon
- Clean, distraction-free interface (GitHub buttons hidden)

### 🎙️ Speech-to-Text Enhancements
- **JSONL import with external audio URLs** - Import audio from S3/MinIO without uploading
- **Auto TextLabel creation** - Transcripts are automatically created as annotations
- **Pre-filled labels** - Annotators can review/edit instead of transcribing from scratch
- **Correct audio URL export** - Exports include the original audio URLs

### 🖼️ Image Classification Enhancements  
- **JSONL import with external image URLs** - Import images from S3/MinIO
- **Pre-filled category labels** - Labels are pre-populated for review/approval workflow

### ✅ UI Improvements
- **Review button styling**: 🔴 Red Circle for "not done", 🟢 Green Check for "done"

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/monlam-ai/monlam-doccano.git
cd monlam-doccano
cp .env.example .env
# Edit .env with your settings
```

### 2. Build and Run

```bash
docker-compose up -d --build
```

### 3. Access

Open http://localhost:8000 (or your configured port)

Default credentials (change in `.env`):
- Username: `admin`
- Password: `changeme123`

## JSONL Import Formats

### Speech-to-Text

```json
{"filename": "https://s3.example.com/audio/file1.wav", "text": "Transcript here", "label": "Transcript here"}
{"filename": "https://s3.example.com/audio/file2.wav", "text": "Another transcript", "label": "Another transcript"}
```

| Field | Description |
|-------|-------------|
| `filename` | Audio URL (S3, MinIO, or any HTTP URL) |
| `text` | Transcript text (stored in example) |
| `label` | Pre-filled annotation (shown to annotator) |
| `meta` | Optional metadata object |

### Image Classification

```json
{"filename": "https://s3.example.com/images/cat.jpg", "label": ["cat", "animal"]}
{"filename": "https://s3.example.com/images/dog.jpg", "label": ["dog", "pet"]}
```

| Field | Description |
|-------|-------------|
| `filename` | Image URL (S3, MinIO, or any HTTP URL) |
| `label` | Array of category labels (pre-filled) |
| `meta` | Optional metadata object |

## Project Structure

```
monlam-doccano/
├── Dockerfile              # Custom Doccano image
├── docker-compose.yml      # Container orchestration
├── .env.example            # Environment template
├── branding/
│   ├── i18n/               # Tibetan translations
│   │   ├── bo/             # བོད་སྐད་ locale files
│   │   └── index.js        # Locale registry
│   └── static/
│       ├── logo.png        # Monlam logo
│       └── favicon.png     # Browser favicon
└── patches/
    ├── backend/
    │   ├── celery_tasks.py # Auto TextLabel creation
    │   ├── serializers.py  # External URL handling
    │   ├── export_models.py# Correct export URLs
    │   ├── catalog.py      # JSONL import options
    │   └── datasets.py     # Custom dataset classes
    ├── frontend/
    │   ├── index.html      # UI customizations
    │   └── 200.html        # SPA fallback
    └── examples/
        ├── speech_to_text/
        │   └── example.jsonl
        └── image_classification/
            └── example.jsonl
```

## Development

### Live Frontend Updates

Uncomment the volume mounts in `docker-compose.yml` to enable live frontend updates:

```yaml
volumes:
  - ./patches/frontend/index.html:/doccano/backend/client/dist/index.html:ro
  - ./patches/frontend/200.html:/doccano/backend/client/dist/200.html:ro
```

### Rebuilding

After modifying backend patches:

```bash
docker-compose build --no-cache
docker-compose up -d
```

## Integration with Traefik

For production with Traefik reverse proxy:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.doccano.rule=Host(`annotate.example.com`)"
  - "traefik.http.routers.doccano.entrypoints=websecure"
  - "traefik.http.routers.doccano.tls=true"
  - "traefik.http.services.doccano.loadbalancer.server.port=8000"
```

## License

Based on [Doccano](https://github.com/doccano/doccano) (MIT License).

Monlam customizations © 2024 Monlam AI.

## Support

For issues with Monlam customizations, please open an issue in this repository.

For core Doccano issues, please refer to the [upstream repository](https://github.com/doccano/doccano).

