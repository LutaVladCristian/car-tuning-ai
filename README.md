# Car Tuning AI — Segmentation Microservice

> Upload a car photo, isolate any part, and let AI swap backgrounds or apply edits — all via a simple REST API.

---

## What It Does

| Endpoint | Description |
| --- | --- |
| `POST /car-segmentation` | Isolate the full car from the background |
| `POST /car-part-segmentation` | Isolate a specific car part by ID |
| `POST /edit-photo` | Replace the background using OpenAI image editing |

Powered by **YOLOv11** for part detection, **SAM (Segment Anything Model)** for masking, and **GPT Image** for AI-generated edits.

---

## Quick Start

**Prerequisites:** [Anaconda](https://www.anaconda.com/) must be installed.

```bash
# 1. Create and activate the environment
conda env create -f environment.yml
conda activate sam-microservice

# 2. Start the server
uvicorn server:app --reload
```

The API will be live at `http://127.0.0.1:8000`.

Explore and test all endpoints interactively via **Swagger UI**: `http://127.0.0.1:8000/docs`

---

## Environment Setup

Create a `.env` file inside `car-segmentation-ms/` with your OpenAI key:

```text
OPENAI_API_KEY=your-key-here
```

---

## Teardown & Troubleshooting

```bash
# Remove the conda environment
conda remove --name sam-microservice --all

# If conda can't find the defaults channel
conda config --add channels defaults
```

---

## References

- [YOLOv11 / Ultralytics Car Parts Dataset](https://docs.ultralytics.com/datasets/segment/carparts-seg/#dataset-yaml)
- [Segment Anything Model (SAM)](https://github.com/facebookresearch/segment-anything)
