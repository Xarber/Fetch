# SPDX-License-Identifier: AGPL-3.0-only
FROM denoland/deno:2.5.6 AS javascript
FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FETCH_DATA=/data FETCH_WEB=/app/web FETCH_SOURCE_ARCHIVE=/app/fetch-source.tar.gz YTDLP_NO_PLUGINS=1 DENO_DIR=/tmp/deno
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 10001 fetch && useradd -u 10001 -g fetch -d /app fetch \
    && mkdir /data /app && chown fetch:fetch /data /app
COPY --from=javascript /usr/bin/deno /usr/local/bin/deno
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
ARG FETCH_COMMIT=development
ENV FETCH_COMMIT=${FETCH_COMMIT}
COPY pyproject.toml ./
COPY backend ./backend
COPY web ./web
RUN pip install --no-cache-dir --no-deps .
COPY backend /source/backend
COPY ios /source/ios
COPY web /source/web
COPY docs /source/docs
COPY assets /source/assets
COPY scripts /source/scripts
COPY .github /source/.github
COPY LICENSE README.md AGENTS.md THIRD_PARTY_NOTICES.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md .env.example .gitignore .gitattributes .editorconfig .dockerignore Dockerfile compose.yaml pyproject.toml requirements.lock package.json package-lock.json tsconfig.json playwright.config.ts release.json /source/
RUN python /source/scripts/package_source.py --root /source --output /app/fetch-source.tar.gz && rm -rf /source
USER 10001:10001
EXPOSE 8000
CMD ["python","-m","uvicorn","fetch_server.api:app","--host","0.0.0.0","--port","8000","--no-access-log"]
