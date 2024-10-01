# Model

Download the models from huggingface and save them in the `models_hub` directory before building.

# Commands

1. Run local image

```bash
docker run -it --rm jonathanadly/colipali-embeddings:version-local
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
docker push jonathanadly/colipali-embeddings:version
```

## Hosting

Coming soon...
