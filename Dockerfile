FROM python:3.9-slim as base-image
ARG POETRY_VERSION=1.8.0
WORKDIR /service
RUN pip install "poetry~=$POETRY_VERSION"
ADD pyproject.toml poetry.lock readme.md ./
ADD chatushka chatushka
RUN poetry build
RUN python -m venv .venv
RUN .venv/bin/pip install dist/*.whl

FROM python:3.9-alpine as runtime-image
WORKDIR /service
COPY --from=base-image /service/.venv ./.venv
ENTRYPOINT ["/service/.venv/bin/python3", "-m", "chatushka"]
