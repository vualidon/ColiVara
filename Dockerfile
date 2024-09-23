FROM python:3.12.2-slim-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
# we need libmagic1 for python-magic, and popler-utils for pdf2image
RUN apt-get update && apt-get install -y libmagic1 poppler-utils
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/