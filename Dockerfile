FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 apparmor \
    && command -v apparmor_parser \
    && test -f /etc/apparmor.d/tunables/global \
    && test -f /etc/apparmor.d/abstractions/base \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/ /app/app/
COPY static/ /app/static/
COPY tests/ /app/tests/
RUN chown -R root:root /app && chmod -R a=rX /app
USER app
EXPOSE 8000
CMD ["python3", "-m", "app"]
