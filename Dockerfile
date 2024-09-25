FROM python:3.12.2-slim-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
# we need libmagic1 for python-magic, and popler-utils for pdf2image
RUN apt-get update && apt-get install -y libmagic1 poppler-utils
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /code
COPY requirements.in /code/
RUN uv pip compile requirements.in -o requirements.txt
RUN uv pip sync requirements.txt --no-cache-dir --compile-bytecode --system
COPY . /code/