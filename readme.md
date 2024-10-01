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

(Note: bringing the embeddings service in the docker-compose is a work in progress. Once that is done, the EMBEDDINGS_URL and EMBEDDINGS_URL_TOKEN will not be needed)

```
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


## LOCAL GPU


Tested on Windows 11 with RTX 3090 TI (8g VRAM) on WSL2 backend running Ubuntu 24.04 LTS as the default WSL distr. 

1. Make sure you can access your GPUs via running:

`docker run -it --gpus=all --rm nvidia/cuda:12.6.1-cudnn-runtime-ubuntu24.04 nvidia-smi` 

The nvidia-smi utility allows users to query information on the accessible devices. If it worked, you are in luck. Otherwise, you will have to debug and fix the erros, which are specific to your machine and setup.

Here some helpful information to help you debug. Please note - local installation are highly-specific per machine and setup and generally not reproducible. How to enable GPU access in your WSL2 is outside the scope of this repo and not something we can help with.


1. Upgrade your Nvidia drivers from here: https://www.nvidia.com/Download/index.aspx


2. Install CUDA toolkit in WSL2: https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=WSL-Ubuntu&target_version=2.0&target_type=deb_local
```
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.6.1/local_installers/cuda-repo-wsl-ubuntu-12-6-local_12.6.1-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-6-local_12.6.1-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-6-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-6
```

3. Install NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installing-the-nvidia-container-toolkit

```
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

This direction are largely the same whether you are doing a Ubuntu inside WSL or a Ubuntu somewhere else (VPS) - and should work in production if you decide to go this route (we do not recommend). Check the links as some of the commands might have changed and are different for different versions of CUDA and Ubuntu.