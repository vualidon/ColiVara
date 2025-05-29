<p align="center">
  <img src="colivara-image.png" alt="ColiVara" width=650px>
</p>

# ColiVara

**State of the Art Retrieval - with a delightful developer experience**

[![codecov](https://codecov.io/gh/tjmlabs/ColiVara/branch/main/graph/badge.svg)](https://codecov.io/gh/tjmlabs/ColiVara) [![Tests](https://github.com/tjmlabs/ColiVara/actions/workflows/test.yml/badge.svg)](https://github.com/tjmlabs/Colivara/actions/workflows/test.yml)


### Documentation

Our documentation is available at [docs.colivara.com](https://docs.colivara.com).

> [!NOTE]
> If you prefer Swagger, you can try our endpoints at [ColiVara API Swagger](https://api.colivara.com/v1/docs). You can also import an openAPI spec (for example for Postman) from the swagger documentation endpoint at [`v1/docs/openapi.json`](https://api.colivara.com/v1/docs/openapi.json)

### Why?

RAG (Retrieval Augmented Generation) is a powerful technique that allows us to enhance LLMs (Language Models) output with private documents and proprietary knowledge that is not available elsewhere. (For example, a company's internal documents or a researcher's notes).

However, it is limited by the quality of the text extraction pipeline. With limited ability to extract visual cues and other non-textual information, RAG can be suboptimal for documents that are visually rich.

ColiVara uses vision models to generate embeddings for documents, allowing you to retrieve documents based on their visual content.

_From the ColPali paper:_

> Documents are visually rich structures that convey information through text, as well as tables, figures, page layouts, or fonts. While modern document retrieval systems exhibit strong performance on query-to-text matching, they struggle to exploit visual cues efficiently, hindering their performance on practical document retrieval applications such as Retrieval Augmented Generation.

[Learn More in the ColPali Paper](https://arxiv.org/abs/2407.01449)

**How does it work?**

In short, ColPali is an advanced document retrieval model that leverages Vision Language Models to integrate both textual and visual elements for highly accurate and efficient document search. ColiVara builds on this model to provide a seamless and user-friendly API for document retrieval.

**If my documents are text-based, why do I need ColiVara?**

Even when your documents are text-based, ColiVara can provide a more accurate and efficient retrieval system. This is because ColiVara uses Late-Interaction style embeddings which is more accurate than pooled embeddings. Our benchmarks contains text-only datasets and we outperform existing systems on these datasets.

**Do I need a vector database?**

No - ColiVara uses Postgres and pgVector to store vectors for you. You DO NOT need to generate, save, or manage embeddings in anyway.

**Do you covert the documents to markdown/text?**

No - ColiVara treats everything as an image, and uses vision models. There are no parsing, chunking, or OCR involved. This method outperforms chunking, and OCR for both text-based documents and visual documents.

**How does non-pdf documents or web pages work?**

We run a pipeline to convert them to images, and perform our normal image-based retrieval. This all happen for you under the hood, and you get the top-k pages when performing retrieval.

**Can I use my vector database?**

Yes - we have an embedding endpoint that only generates embeddings without saving or doing anything else. You can store these embeddings at your end. Keep in mind that we use late-interaction and multi-vectors, many vector databases do not support this yet.

**Do I have to use the SDKs?**

No - the SDKs are provided for your convenience. You can use the REST API directly if you prefer.

## Key Features

- **State of the Art retrieval**: ColiVara outperforms existing retrieval systems on both quality and latency.
- **Wide Format Support**: Supports over 100 file formats including PDF, DOCX, PPTX, and more.
- **Filtering**: ColiVara allows for filtering on collections and documents on arbitrary metadata fields. For example, you can filter documents by author or year. Or filter collections by type. You get the best of both worlds - structured and unstructured data.
- **Convention over Configuration**: The API is designed to be easy to use with opinionated and optimized defaults.
- **Modern PgVector Features**: We use HalfVecs for faster search and reduced storage requirements.
- **REST API**: Easy to use REST API with Swagger documentation.
- **Comprehensive**: Full CRUD operations for documents, collections, and users.



## Getting Started (Local Setup)

1. Setup the Embeddings Service (ColiVarE) - This is a separate repo and is required for the API to work. The directions are available here: [ColiVarE](https://github.com/tjmlabs/ColiVarE/blob/main/readme.md)

```bash
docker run --runtime=nvidia -p 8000:8005 vualidon1403/colivare:20250528
```

2. Clone the repo

```bash
git clone https://github.com/tjmlabs/ColiVara
```

2. Create a .env.dev file in the root directory with the following variables:

```
EMBEDDINGS_URL="the serverless embeddings service url" # for local setup use http://host.docker.internal:8000/runsync
EMBEDDINGS_URL_TOKEN="the serverless embeddings service token"  # for local setup use any string will do.
AWS_S3_ACCESS_KEY_ID="an S3 or compatible storage access key"
AWS_S3_SECRET_ACCESS_KEY="an S3 or compatible storage secret key"
AWS_STORAGE_BUCKET_NAME="an S3 or compatible storage bucket name"
AWS_STORAGE_REGION_NAME="an S3 or compatible storage bucket region name"
```

3. Run the following commands:

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
# get the token from the superuser creation
docker compose exec web python manage.py shell
from accounts.models import CustomUser
user = CustomUser.objects.first().token 
print(user) # save this token somewhere (use it for authorization)
```

4. Application will be running at <http://localhost:8001> and the swagger documentation at <http://localhost:8001/v1/docs>
5. To run tests - we have 100% test coverage

```bash
docker compose exec web pytest
```

6. mypy for type checking

```bash
docker compose exec web mypy .
```

## Support

For support, join our Discord community where you can:

- Get help with setup and configuration
- Report bugs and request features
- Connect with other ColiVara users
- Stay updated on new releases and announcements

Click the badge below to join:

[![Discord](https://dcbadge.limes.pink/api/server/https://discord.gg/DtGRxWuj8y)](https://discord.gg/DtGRxWuj8y)

## License

This project is licensed under Functional Source License, Version 1.1, Apache 2.0 Future License. See the [LICENSE.md](LICENSE.md) file for details.

For commercial licensing, please contact us at [tjmlabs.com](https://tjmlabs.com). We are happy to work with you to provide a license that meets your needs.
