# VibeCast Studio

A full-featured web application for creating multi-speaker audio content using Microsoft's VibeVoice TTS models. Create podcasts, audiobooks, interviews, and more with up to 90 minutes of audio and 4 distinct speakers.

## Features

- **Multi-Speaker Support**: Up to 4 distinct speakers with voice mapping
- **Long-Form Generation**: Support for up to 90 minutes of audio content
- **9 Embedded Voices**: English, Chinese, and Indian English voices
- **Real-time Preview**: Quick preview using VibeVoice-Realtime-0.5B
- **Script Editor**: Screenplay-style editor with drag-and-drop reordering
- **Claude Integration**: AI-powered dialogue enhancement (optional)
- **Professional Export**: MP3/WAV export with chapter markers
- **Safety Features**: Audio watermarking and AI disclaimers

## Requirements

### NVIDIA GPU (Recommended)
- **GPU**: NVIDIA RTX 3060 (8GB VRAM) or better
- **Docker**: Docker Engine with NVIDIA Container Toolkit
- **Memory**: 16GB RAM recommended
- **Storage**: 20GB+ for models and generated audio

### Apple Silicon (M1/M2/M3)
- **Mac**: Apple Silicon Mac with 16GB+ unified memory
- **Python**: 3.11+
- **PyTorch**: 2.0+ with MPS support
- **Docker**: Docker Desktop for Mac (for supporting services)

### CPU-Only (Slower)
- **Memory**: 32GB RAM recommended
- **Docker**: Docker Engine
- **Storage**: 20GB+ for models and generated audio

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/zhound420/vibecast-studio.git
cd vibecast-studio

# Run the interactive setup wizard
./setup.sh
```

The setup wizard will:
- Detect your platform (NVIDIA GPU / Apple Silicon / CPU)
- Configure environment variables
- Set up Python virtual environment (Apple Silicon only)
- Pull Docker images

### 2. Start the Application

```bash
./start.sh
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Task Monitor)**: http://localhost:5555

### Other Commands

```bash
./stop.sh      # Stop all services
./status.sh    # Check service status
./logs.sh      # View logs (all services)
./logs.sh backend   # View backend logs only
```

### Manual Setup (Alternative)

<details>
<summary>Click to expand manual setup instructions</summary>

#### NVIDIA GPU

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d
```

#### Apple Silicon (M1/M2/M3/M4)

```bash
cp .env.example .env
docker compose up -d redis frontend

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal:
celery -A app.workers.celery_app worker -l info -c 1 -Q generation,export
```

#### CPU-Only

```bash
cp .env.example .env
docker compose up -d
```

</details>

## Architecture

```
vibecast-studio/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST API routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── workers/      # Celery tasks
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── store/        # Zustand stores
└── storage/              # Generated files
```

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | React app served by Nginx |
| backend | 8000 | FastAPI REST API |
| worker | - | Celery worker for TTS generation |
| beat | - | Celery scheduler |
| redis | 6379 | Message broker |
| flower | 5555 | Task monitoring |

## Available Voices

| Voice ID | Name | Language | Gender |
|----------|------|----------|--------|
| en-Alice_woman | Alice | English | Female |
| en-Carter_man | Carter | English | Male |
| en-Frank_man | Frank | English | Male |
| en-Mary_woman_bgm | Mary | English | Female |
| en-Maya_woman | Maya | English | Female |
| in-Samuel_man | Samuel | Indian English | Male |
| zh-Anchen_man_bgm | Anchen | Chinese | Male |
| zh-Bowen_man | Bowen | Chinese | Male |
| zh-Xinran_woman | Xinran | Chinese | Female |

## API Usage

### Create a Project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Podcast"}'
```

### Add Script Content

```bash
curl -X POST http://localhost:8000/api/v1/scripts/{project_id}/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[1] Hello, welcome to our podcast!\n[2] Thanks for having me!",
    "format": "bracket"
  }'
```

### Start Generation

```bash
curl -X POST http://localhost:8000/api/v1/generation/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "voice_mapping": {
      "1": "en-Carter_man",
      "2": "en-Alice_woman"
    }
  }'
```

## Script Formats

VibeCast supports multiple script formats:

### Bracket Format
```
[1] Speaker one dialogue
[2] Speaker two dialogue
```

### Named Speaker Format
```
Host: Welcome to the show!
Guest: Thanks for having me!
```

### Numbered Format
```
1. First speaker's line
2. Second speaker's line
```

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Safety & Ethics

VibeCast Studio implements several safety measures:

1. **Audio Watermarking**: All generated audio includes an imperceptible watermark
2. **AI Disclaimers**: Generated content includes "AI Generated" metadata
3. **Rate Limiting**: Generation requests are rate-limited to prevent abuse
4. **Usage Logging**: Generation requests are logged (hashed) for traceability

### Prohibited Uses

- Voice impersonation or deepfakes
- Disinformation or misleading content
- Content in unsupported languages
- Real-time voice conversion for deceptive purposes

## Troubleshooting

### GPU Not Detected (NVIDIA)

Ensure NVIDIA Container Toolkit is installed:
```bash
nvidia-ctk --version
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

### MPS Not Working (Apple Silicon)

Verify MPS is available in Python:
```python
import torch
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")
```

If MPS is not available:
- Update to macOS 12.3 or later
- Install PyTorch 2.0+ with MPS support: `pip install torch torchvision torchaudio`
- Ensure you're running Python natively (not through Rosetta)

### Model Download Issues

Models are downloaded on first use. Ensure you have:
- Stable internet connection
- Sufficient disk space (10GB+)
- HuggingFace access (no token required for public models)

### Out of Memory

If you encounter OOM errors:
- Close other GPU-intensive applications
- Reduce batch size in generation options
- Consider using shorter content chunks

For Apple Silicon:
- MPS uses unified memory shared with the system
- Close memory-intensive applications
- 16GB unified memory is minimum recommended

## License

This project uses Microsoft's VibeVoice models which are released under MIT license.
See individual component licenses for details.

## Acknowledgments

- [Microsoft VibeVoice](https://github.com/microsoft/VibeVoice) for the TTS models
- [Anthropic Claude](https://anthropic.com) for dialogue enhancement
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework
- [React](https://react.dev) for the frontend framework
