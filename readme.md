## PaliAPI

A document retrieval API with ColiPali as the backend.

Components:

1. Embeddings Service. Currently running as a seperate serverless function. Repo: [embeddings-service](https://github.com/tjmlabs/colipali-embeddings) - plan is to move this to the same docker-compose as the API as an optional service. (you need a GPU for this)

2. Postgres DB with pgvector extension for storing embeddings.

3. REST API for CRUD operations on collections and documents

### Models:

- **User**: Represents an individual user.
- **Collection**: Represents a collection of documents, owned by a user.
- **Document**: Each document belongs to a specific collection.
- **Page**: Each page belongs to a specific document and contains the embeddings.
- **PageEmbedding**: Represents the embeddings of a page.

### Endpoints:

Please check swagger documentation endpoint (v1/docs) for rest of endpoints. Typical flow

1. Create empty collection with metadata via Create Collection endpoint
2. Add documents to the collection with metadata Via Create Document endpoint
3. Search for documents in the collection via Search endpoint with Query and optional filtering. You will get back top k(3) pages with document and collection details.

There is endpoints for updating and deleting collections and documents as well.

You can import an openAPI spec (for example for Postman) from the swagger documentation endpoint at `v1/docs/openapi.json`

## Roadmap for 1.0 Release

1.  Python SDK for the API
2.  Filter by metadata on collection and document
3.  Embeddings Endpoint (user responsible for storage and querying - aka I want to use Qdrant as my storage)
4.  Embeddings service in the docker-compose instead of seperate serverless GPU (aka I want to host this fully on my own GPU server)
5.  Documentation for the API
6.  Basic sanity check evals

## Wishlist

1. Typescript SDK for the API
2. Consistent/reliable Evals

## Getting Started

1. Clone the repo
2. Create a .env.dev file in the root directory with the following variables:

```
DEBUG=True
SECRET_KEY="DUMMY123"
DJANGO_SECURE_SSL_REDIRECT="False"
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS="False"
DJANGO_SECURE_HSTS_PRELOAD="False"
DJANGO_SESSION_COOKIE_SECURE="False"
DJANGO_CSRF_COOKIE_SECURE="False"
LOCAL=True
EMBEDDINGS_URL="email me and I will give you the url while we in alpha"
EMBEDDINGS_URL_TOKEN="email me and I will give you the token while we are in alpha"
```

3. Run the following commands:

```
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
# get the token from the superuser creation
docker-compose exec web python manage.py shell
from accounts.models import CustomUser
user = CustomUser.objects.first().token # save this token somewhere (I will make this easier in the future)
```

4. Application will be running at http://localhost:8001 and the swagger documentation at http://localhost:8001/v1/docs

5. To run tests - we have 92% test coverage

```
docker-compose exec web pytest
```

6. mypy for type checking

```
docker-compose exec web mypy .
```

7. We use ruff as linter and formatting. Eventaully will setup pre-commit hooks for this.
