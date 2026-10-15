FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy UV_NO_CACHE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1=12.2.0-14+deb12u1 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
COPY packages/contracts/python packages/contracts/python
COPY services/api services/api
COPY services/edge services/edge
COPY data/scenarios data/scenarios
RUN uv sync --locked --no-dev --no-editable
ENV PATH="/app/.venv/bin:$PATH"

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS build-tools
WORKDIR /app
USER root
RUN apt-get update && apt-get install -y --no-install-recommends g++=4:12.2.0-3 cmake=3.25.1-1 make=4.3-4.1 nlohmann-json3-dev=3.11.2-2 && rm -rf /var/lib/apt/lists/*
COPY cpp/digital-twin cpp/digital-twin
RUN cmake -S cpp/digital-twin -B /build -DCMAKE_BUILD_TYPE=Release && cmake --build /build --parallel 2 && ctest --test-dir /build --output-on-failure

FROM build-tools AS qa
COPY --from=base /app /app
COPY --from=base /usr/local/bin/uv /usr/local/bin/uv
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy UV_NO_CACHE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
RUN uv sync --locked
COPY tests tests
COPY tools tools
COPY packages/contracts/generated packages/contracts/generated
ENV AEGIS_TWIN_BINARY=/build/aegis-twin
CMD ["python", "-m", "pytest", "-q"]

FROM base AS runtime
COPY --from=build-tools /build/aegis-twin /usr/local/bin/aegis-twin
COPY --from=build-tools /build/libaegis_twin.so /usr/local/lib/libaegis_twin.so
RUN useradd --uid 10001 --no-create-home aegis
USER 10001:10001
CMD ["uvicorn", "aegis_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
