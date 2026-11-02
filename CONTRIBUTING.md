# Working in This Repo

Five of us share this code, and everyone's paper has to show what they did, so every change should be traceable to one person.

## Who owns what

| Area | Owner | Main files | Branch prefix |
|---|---|---|---|
| Coordination, architecture, setup and security docs | Andy | `docs/`, `README.md`, `CONTRIBUTING.md` | `andy/` |
| Camera research and video input | Khaled | `docs/camera-*.md`, new video-input code | `khaled/` |
| Backend (Flask, Socket.IO, storage) | Parth | `backend/webserver.py`, database work | `parth/` |
| Detection model | Jason | `backend/yolo.py` (model parts), `backend/config.json`, test images | `jason/` |
| Dashboard | Amareen | `frontend/` | `amareen/` |

Changes to someone else's area are fine. Tag the owner on the pull request.

## How to make a change

1. Pull the latest `main`: `git checkout main && git pull`
2. Branch: `git checkout -b <yourname>/<short-topic>` (e.g. `jason/bear-class-config`)
3. Commit small steps with clear messages: `fix: create static/ folder on server start`
4. Push and open a pull request into `main`. Describe what changed and how you tested it.
5. One teammate reviews, then the author merges. Don't push straight to `main`.

## Where things go

- `docs/` holds written notes others need: architecture, setup guide, security review, meeting log, test results.
- Test images and results: `tests/` (keep large datasets out of git; link to them instead)
- Never commit secrets (tokens, Wi-Fi passwords, Tailscale keys), `node_modules/`, `.venv/`, or generated files like `images.csv`.

## Tracking work

Each task from the team work plan becomes a GitHub issue assigned to its owner and labeled with the area (`backend`, `model`, `frontend`, `docs`, `security`, `camera`). Close the issue from the pull request with `Closes #<n>`.

Known problems to file as issues are listed in [docs/setup-guide.md](docs/setup-guide.md) (S-1 to S-11) and [docs/security-review.md](docs/security-review.md) (SEC-1 to SEC-9).
