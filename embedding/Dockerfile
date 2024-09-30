FROM nvidia/cuda:12.6.1-cudnn-runtime-ubuntu24.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV DEBIAN_FRONTEND=noninteractive

#install python 3.12
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-venv python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --set python3 /usr/bin/python3.12 && \
    ln -s /usr/bin/python3 /usr/bin/python

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv


# copy the requirements file
COPY builder/requirements.in .

# Copy the pre-downloaded model files into the image
COPY models_hub /models_hub

# Python dependencies
RUN uv venv /opt/venv
# Use the virtual environment automatically
ENV VIRTUAL_ENV=/opt/venv
# Place entry points in the environment at the front of the path
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip compile requirements.in -o requirements.txt
RUN uv pip sync requirements.txt --no-cache-dir --compile-bytecode


# Add src files to the image
COPY src .

EXPOSE 8000

# Run the application
CMD ["uvicorn", "handler:app", "--host", "0.0.0.0", "--port", "8000"]

