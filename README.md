# Hollywood

Hollywood is a local-first, agentic AI film pipeline. A director supplies a story brief; the pipeline creates a world and style bible, recurring character references, narrative scenes, filmable shots, paired keyframes, video clips, and a simple assembled movie.

## What is implemented

- FastAPI backend with typed Pydantic domain models and SQLite development persistence that can move to PostgreSQL through `DATABASE_URL`.
- A checkpointed LangGraph workflow with the required stage order, stage-level persistence, resumability, and Director Mode approval interrupts.
- An OpenAI structured-output story/planning adapter plus OpenAI image generation/editing for reference-conditioned keyframes.
- Google Veo 3.1 adapter using the official `google-genai` SDK, including start and end frame capability handling.
- WAN REST, local normalized-server, and ComfyUI adapter boundaries. These require deployment-specific request mapping before they are enabled; Hollywood does not claim a universal WAN API format.
- SSE progress stream, project/artifact/job persistence schema, dependency invalidation service, retry-friendly provider boundaries, and FFmpeg manifest/concatenation service.
- A React studio workspace that begins with the story prompt and then exposes Story, Characters, Scenes, Shots, Keyframes, Videos, and Timeline views.

## Run locally

1. Copy `.env.example` to `.env` and add the provider keys you plan to use.
2. In one terminal, run `py -m pip install -e "./backend[test]"` and then `py -m uvicorn app.main:app --app-dir backend --reload --port 8000`.
3. In a second terminal, run `npm run dev` and open `http://localhost:3000`.

`docker compose up --build` starts the same pair of services.

## Provider notes

OpenAI keys are required before Hollywood starts a real planning or image-generation run. Google video generation is selected per project; the Google adapter only passes a last frame when the selected Veo model advertises that capability. This matches the official Google SDK's Veo model API, which supports first-frame image input and Veo 3.1 last-frame interpolation. See the [Google Veo guide](https://ai.google.dev/gemini-api/docs/video) and [Python SDK examples](https://github.com/googleapis/python-genai).

WAN is deliberately an adapter boundary. Configure `WAN_BACKEND=rest|local|comfyui`; the remote/local contract expects `POST /generate` and `GET /jobs/{job_id}`. A deployment-specific ComfyUI workflow is intentionally left at that narrow boundary rather than guessed.

## API surface

- `POST /api/projects` creates a project and queues the graph.
- `GET /api/projects` and `GET /api/projects/{id}` return persisted state.
- `POST /api/projects/{id}/run` restarts an incomplete run; `POST /resume` continues a Director Mode checkpoint.
- `GET /api/projects/{id}/events` is a server-sent event stream for live pipeline progress.
- `GET /api/providers` reports configured provider capabilities.

## Tests

From `backend/`, run `pytest`. External API calls are isolated and mocked in tests; no provider key is needed for the test suite.
