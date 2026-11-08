# How We're Using This Repo

There are five of us working in the same code, and each of our papers has to show what we personally did. So we should be able to tell who changed what.

## Who's working on what

- **Andy**: coordination, architecture, setup, and security docs (`docs/`, `README.md`, this file). Branches start with `andy/`.
- **Khaled**: camera research and getting video in from an IP camera (`docs/camera-*.md`, plus any new video input code). Branches start with `khaled/`.
- **Parth**: backend: Flask, Socket.IO, storage (`backend/webserver.py`, database work). Branches start with `parth/`.
- **Jason**: the detection model (the model parts of `backend/yolo.py`, `backend/config.json`, test images). Branches start with `jason/`.
- **Amareen**: the dashboard (`frontend/`). Branches start with `amareen/`.

It's fine to change something in someone else's area, just tag them on the PR.

## Making a change

1. Get the latest `main`: `git checkout main && git pull`
2. Make a branch named after yourself and what you're doing: `git checkout -b <yourname>/<topic>`, e.g. `jason/bear-class-config`
3. Commit in small pieces with messages that say what you did, like `fix: create static/ folder on server start`
4. Push your branch and open a pull request into `main`. Say what you changed and how you tested it.
5. Get one teammate to look it over, then merge it yourself. Please don't push straight to `main`.

## Where to put things

- `docs/` is for notes the rest of us need: architecture, setup, security, meeting notes, test results.
- Test images and results go in `tests/`. Keep big datasets out of git and just link to them.
- Don't commit passwords, tokens, Tailscale keys, `node_modules/`, `.venv/`, or generated files like `images.csv`.

## Keeping track of work

Each task from our work plan should be a GitHub issue assigned to whoever owns it, with a label for the area (`backend`, `model`, `frontend`, `docs`, `security`, `camera`). If your PR finishes an issue, put `Closes #<number>` in the description so it closes on its own.

The problems I already found are listed in [docs/setup-guide.md](docs/setup-guide.md) (S-1 to S-11) and [docs/security-review.md](docs/security-review.md) (SEC-1 to SEC-9). Those still need to be made into issues.
