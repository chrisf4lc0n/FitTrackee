# FitTrackee Sink Folder Watcher
# This container watches a folder for workout files and auto-imports them
#
# Build: docker build -t fittrackee-sink -f docker-sink/Dockerfile .
# Run: docker run -d --name fittrackee-sink -v ./uploads:/usr/src/app/uploads fittrackee-sink

FROM python:3.13-alpine AS python-builder

RUN mkdir -p /usr/src/app/
WORKDIR /usr/src/app/

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV=/opt/venv

COPY pyproject.toml poetry.lock README.md /usr/src/app/
COPY fittrackee/. /usr/src/app/fittrackee/
RUN rm -rf /usr/src/app/fittrackee/tests

RUN apk add --no-cache g++ gdal-dev && \
    rm -rf /var/cache/apk/* && \
    python3 -m venv "$VIRTUAL_ENV" && \
    pip install --upgrade pip wheel && \
    pip install poetry==2.1.3 && \
    . "$VIRTUAL_ENV/bin/activate" && \
    poetry install --only main --no-interaction --quiet

FROM python:3.13-alpine AS runtime

RUN apk add --no-cache tini bash && \
    addgroup -g 1000 -S fittrackee && \
    adduser -H -D -u 1000 -S fittrackee -G fittrackee

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:$PATH"

COPY --chown=root --chmod=755 --from=python-builder /opt/venv "$VIRTUAL_ENV"
COPY --chown=root --chmod=755 --from=python-builder /usr/src/app/fittrackee /usr/src/app/fittrackee
COPY --chown=root --chmod=755 docker-sink/docker-sink-entrypoint.sh /usr/src/app/

USER fittrackee

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["sh", "/usr/src/app/docker-sink-entrypoint.sh"]
