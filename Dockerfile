# Permit Horizon in a container: the website built with Node, served by Python on port 8080,
# with the Python engine installed too (so `docker compose run --rm app hre run --state ZZ
# --data-dir data/sample --out /tmp/ZZ.json` works). The results bundle is the committed
# web/public/results/ (decision 74); nothing here regenerates it.
#
#   docker compose up        # then open http://localhost:8080
#
# Verified in CI (.github/workflows/ci.yml, job "docker": build, start, smoke requests).
# Base images are pinned by digest; Dependabot (docker ecosystem) proposes updates.

# --- 1. Build the static site --------------------------------------------------------------
FROM node:26-slim@sha256:e4db4c914bf8ad241bd24804fc25d272d89bad97e68cdc8a1414862790a02c39 AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# --- 2. Python: the engine (hre) and the static file server --------------------------------
FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir uv==0.11.29
WORKDIR /app
COPY pyproject.toml uv.lock .python-version README.md LICENSE NOTICE ./
COPY src/ src/
RUN uv sync --frozen --all-extras --no-dev
COPY data/sample/ data/sample/
COPY --from=web /src/web/dist/ web/dist/
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/results/meta.json', timeout=2)"
CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", "/app/web/dist"]
