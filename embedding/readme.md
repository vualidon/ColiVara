# Model

Download the models from huggingface and save them in the `models_hub` directory before building.

# Commands

1. Run local image

```bash
docker run -it --rm tjmlabs/yarr-embedding-service:version-local
```

2. Build image
   version is usually date + version, e.g. 20240930-cloud or 20240930-local

```bash
# ./build_publish.sh local  # For local build
# ./build_publish.sh cloud  # For cloud build
```

3. Test locally without docker

```bash
python src/handler.py --rp_serve_api
```

4. Push image to docker hub

```bash
docker push tjmlabs/yarr-embedding-service::version
```

## Hosting

Coming soon...
