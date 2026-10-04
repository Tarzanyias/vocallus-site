#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_bridge.py — scaffold the Vocallus Twilio bridge project.

Run:
    python setup_bridge.py

What it does
------------
1. Creates a folder called vocallus-bridge next to this script.
2. Writes package.json, server.js, .gitignore, README.md.
3. Runs `npm install`.
4. Runs `git init`, `git add .`, `git commit`, `git branch -M main`.
5. Asks for your GitHub repo URL and adds it as `origin`.
6. Prints the final `git push` command for you to run.

Safe to re-run: existing files are left alone unless you pass --force.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# File contents
# ---------------------------------------------------------------------------

PACKAGE_JSON = """{
  "name": "vocallus-bridge",
  "version": "1.0.0",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "fastify": "^4.28.0",
    "@fastify/websocket": "^10.0.0",
    "ws": "^8.18.0",
    "dotenv": "^16.4.0"
  },
  "engines": {
    "node": ">=20"
  }
}
"""

SERVER_JS = """import Fastify from 'fastify';
import fastifyWebsocket from '@fastify/websocket';

const app = Fastify({ logger: true });
await app.register(fastifyWebsocket);

// Health check — Railway and your browser use this to confirm it's alive.
app.get('/health', async () => ({
  status: 'ok',
  service: 'vocallus-bridge',
  time: new Date().toISOString()
}));

// Root route — so visiting the bare URL doesn't 404.
app.get('/', async () => ({
  message: 'Vocallus bridge is running',
  endpoints: ['/health', '/incoming-call', '/media-stream']
}));

// Twilio will POST here when a call comes in. For now this is a stub
// that returns an empty TwiML response so we can test the deploy.
app.post('/incoming-call', async (req, reply) => {
  reply.type('text/xml').send(
    '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
  );
});

// Twilio Media Streams connects here. Full bridge logic comes later.
app.get('/media-stream', { websocket: true }, (socket, req) => {
  app.log.info('WebSocket client connected');
  socket.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw.toString());
      if (msg.event === 'start') app.log.info(`Stream started: ${msg.start.streamSid}`);
      if (msg.event === 'stop') app.log.info('Stream stopped');
    } catch (err) {
      app.log.error('Bad message from Twilio');
    }
  });
  socket.on('close', () => app.log.info('WebSocket closed'));
});

const port = process.env.PORT || 8080;
await app.listen({ port, host: '0.0.0.0' });
"""

GITIGNORE = """node_modules/
.env
.env.local
*.log
.DS_Store
"""

README_MD = """# Vocallus Bridge

Twilio Media Streams bridge for the Vocallus AI receptionist.

## Endpoints

- `GET /health` — health check
- `POST /incoming-call` — Twilio webhook
- `WS  /media-stream` — Twilio media stream

## Deploy

Deployed on Railway. Environment variables:

- `OPENAI_API_KEY` — OpenAI API key
- `SYSTEM_PROMPT` — Solana's system prompt
"""

FILES = {
    "package.json": PACKAGE_JSON,
    "server.js": SERVER_JS,
    ".gitignore": GITIGNORE,
    "README.md": README_MD,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(cmd: list[str], cwd: Path, *, check: bool = True, quiet: bool = False) -> int:
    """Run a command, streaming output unless quiet."""
    if not quiet:
        print(f"  $ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            text=True,
            capture_output=quiet,
            shell=False,
        )
        return result.returncode
    except FileNotFoundError:
        print(f"\nerror: `{cmd[0]}` is not installed or not on your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        if check:
            print(f"\nerror: command failed with exit code {exc.returncode}")
            if quiet and exc.stdout:
                print(exc.stdout)
            if quiet and exc.stderr:
                print(exc.stderr)
            sys.exit(exc.returncode)
        return exc.returncode


def which(name: str) -> bool:
    """Cross-platform check for a command on PATH."""
    import shutil
    return shutil.which(name) is not None


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def create_folder(base: Path, force: bool) -> Path:
    target = base / "vocallus-bridge"
    if target.exists() and not force:
        print(f"  [ok]   folder exists: {target}")
    else:
        target.mkdir(parents=True, exist_ok=True)
        print(f"  [new]  created folder: {target}")
    return target


def write_files(folder: Path, force: bool) -> None:
    for name, content in FILES.items():
        path = folder / name
        if path.exists() and not force:
            print(f"  [ok]   {name} (kept existing)")
            continue
        path.write_text(content, encoding="utf-8")
        print(f"  [new]  {name}")


def npm_install(folder: Path) -> None:
    if not which("npm"):
        print("  [skip] npm not found — install Node.js first: https://nodejs.org")
        return
    print("  (this takes ~30 seconds)")
    run(["npm", "install"], folder, quiet=True)
    print("  [ok]   dependencies installed")


def git_init(folder: Path) -> None:
    if not which("git"):
        print("  [skip] git not found — install from https://git-scm.com")
        return

    if (folder / ".git").exists():
        print("  [ok]   git already initialized")
    else:
        run(["git", "init"], folder, quiet=True)
        print("  [ok]   git initialized")

    run(["git", "add", "."], folder, quiet=True)
    print("  [ok]   staged all files")

    # Commit may fail if there's nothing to commit or user.email is unset.
    rc = run(
        ["git", "commit", "-m", "Initial bridge server"],
        folder,
        check=False,
        quiet=True,
    )
    if rc == 0:
        print("  [ok]   initial commit created")
    else:
        print("  [warn] commit failed — check git user.name / user.email config")

    run(["git", "branch", "-M", "main"], folder, check=False, quiet=True)
    print("  [ok]   branch set to main")


def add_remote(folder: Path) -> None:
    if not (folder / ".git").exists():
        return

    print()
    print("Paste the URL of your GitHub repo (created at https://github.com/new).")
    print("It looks like: https://github.com/YOUR_USERNAME/vocallus-bridge.git")
    print()
    url = input("Repo URL (or press Enter to skip): ").strip()

    if not url:
        print("  [skip] no URL provided — you can add it later with:")
        print("         git remote add origin <url>")
        return

    # Remove any existing origin first, then add.
    run(["git", "remote", "remove", "origin"], folder, check=False, quiet=True)
    run(["git", "remote", "add", "origin", url], folder, quiet=True)
    print(f"  [ok]   origin set to {url}")


def print_next_steps(folder: Path) -> None:
    print()
    print("=" * 60)
    print("DONE — the bridge project is ready.")
    print("=" * 60)
    print()
    print(f"Folder: {folder}")
    print()
    print("Next steps:")
    print()
    print("  1. Test it locally:")
    print(f"       cd \"{folder}\"")
    print("       npm start")
    print("     Then visit  http://localhost:8080/health")
    print()
    print("  2. Push to GitHub:")
    print(f"       cd \"{folder}\"")
    print("       git push -u origin main")
    print()
    print("  3. Deploy on Railway:")
    print("       railway.com/new -> GitHub Repository -> vocallus-bridge")
    print()
    print("  4. Add environment variables on Railway:")
    print("       OPENAI_API_KEY  = sk-...")
    print("       SYSTEM_PROMPT   = You are Solana, the AI receptionist for ...")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold the Vocallus bridge.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files in the target folder",
    )
    parser.add_argument(
        "--skip-npm",
        action="store_true",
        help="skip npm install",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent

    print("Setting up vocallus-bridge ...\n")

    print("Folder:")
    folder = create_folder(base, args.force)

    print("\nFiles:")
    write_files(folder, args.force)

    if not args.skip_npm:
        print("\nnpm install:")
        npm_install(folder)

    print("\nGit:")
    git_init(folder)

    add_remote(folder)

    print_next_steps(folder)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        raise SystemExit(1)