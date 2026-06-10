# Security Policy

## Scope

Live Speech Translator FI is a **local-first** application. By default it binds to `127.0.0.1` and processes audio on the user's machine. It does not send speech to cloud translation APIs.

## Reporting a Vulnerability

If you discover a security issue, please open a private report via GitHub Security Advisories or contact the maintainer through the repository issue tracker with the label `security`.

Do not include real session logs, `.env` files, or audio recordings in public issues.

## Local deployment notes

- Do not expose the backend to the public internet without authentication and TLS review.
- Session logs in `backend/logs/` may contain spoken content — treat them as sensitive data.
- Never commit `.env`, API tokens, or downloaded model weights.
- CORS is permissive (`*`) for local development; review before remote deployment.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
