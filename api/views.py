import base64
from typing import Dict, List, Optional, Union

import aiohttp
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.db.utils import IntegrityError
from django.http.request import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import File, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.security import HttpBearer
from pgvector.utils import HalfVector
from pydantic import Field, model_validator
from typing_extensions import Self

from accounts.models import CustomUser

from .models import Collection, Document, MaxSim, Page

router = Router()


@router.get("/health", tags=["health"])
async def health(request) -> Dict[str, str]:
    return {"status": "ok"}


"""AUTHENTICATION"""


class Request(HttpRequest):
    auth: CustomUser


class Bearer(HttpBearer):
    """
    Bearer class for handling HTTP Bearer authentication.

    Methods:
        authenticate(request, token):
            Authenticates the user based on the provided token.
            Args:
                request: The HTTP request object.
                token: The token string used for authentication.
            Returns:
                The authenticated user if the token is valid, otherwise None.
    """

    async def authenticate(
        self, request: HttpRequest, token: str
    ) -> Optional[CustomUser]:
        try:
            user = await CustomUser.objects.aget(token=token)
            return user
        except CustomUser.DoesNotExist:
            return None


"""Collections"""


class CollectionIn(Schema):
    name: str
    metadata: Optional[dict] = {}


class CollectionOut(Schema):
    id: int
    name: str
    metadata: dict


@router.post("/collections", tags=["collections"], auth=Bearer())
async def create_collection(
    request: Request, payload: CollectionIn
) -> Dict[str, Union[int, str]]:
    """
    Create a new collection.

    This endpoint allows the user to create a new collection with the specified name and metadata.

    Args:
        request: The HTTP request object, which includes the user information.
        payload (CollectionIn): The input data for creating the collection, which includes the name and metadata.

    Returns:
        dict: A dictionary containing the ID of the newly created collection and a success message.

    Raises:
        HttpError: If the user already has a collection with the same name.
    """
    try:
        collection = await Collection.objects.acreate(
            name=payload.name, owner=request.auth, metadata=payload.metadata
        )
        return {"id": collection.id, "message": "Collection created successfully"}
    except IntegrityError:
        raise HttpError(
            409,
            "You already have a collection with this name, did you mean to update it? Use PATCH instead.",
        )


@router.get(
    "/collections", response=List[CollectionOut], tags=["collections"], auth=Bearer()
)
async def list_collections(request: Request) -> List[CollectionOut]:
    """
    Endpoint to list collections.

    This endpoint retrieves a list of collections owned by the authenticated user.

    Args:
        request: The request object containing authentication information.

    Returns:
        A list of CollectionOut objects representing the collections owned by the authenticated user.

    Raises:
        HTTPException: If there is an issue with the request or authentication.
    """
    collections = []
    async for c in Collection.objects.filter(owner=request.auth):
        collections.append(CollectionOut(id=c.id, name=c.name, metadata=c.metadata))
    return collections


@router.get(
    "/collections/{collection_id}",
    response=CollectionOut,
    tags=["collections"],
    auth=Bearer(),
)
async def get_collection(request: Request, collection_id: int) -> CollectionOut:
    """
    Retrieve a collection by its ID.

    Args:
        request: The request object containing authentication information.
        collection_id (int): The ID of the collection to retrieve.

    Returns:
        CollectionOut: The retrieved collection with its ID, name, and metadata.

    Raises:
        HTTPException: If the collection is not found or the user is not authorized to access it.

    Endpoint:
        GET /collections/{collection_id}

    Tags:
        collections

    Authentication:
        Bearer token required.
    """
    collection = await aget_object_or_404(
        Collection, id=collection_id, owner=request.auth
    )
    return CollectionOut(
        id=collection.id, name=collection.name, metadata=collection.metadata
    )


@router.patch("/collections/{collection_id}", tags=["collections"], auth=Bearer())
async def partial_update_collection(
    request: Request, collection_id: int, payload: CollectionIn
) -> Dict[str, str]:
    """
    Partially update a collection.

    This endpoint allows for partial updates to a collection's details. Only the fields provided in the payload will be updated.

    Args:
        request: The request object containing authentication details.
        collection_id (int): The ID of the collection to be updated.
        payload (CollectionIn): The payload containing the fields to be updated.

    Returns:
        dict: A message indicating the collection was updated successfully.

    Raises:
        HTTPException: If the collection is not found or the user is not authorized to update it.
    """
    collection = await aget_object_or_404(
        Collection, id=collection_id, owner=request.auth
    )
    collection.name = payload.name or collection.name
    collection.metadata = payload.metadata or collection.metadata
    await collection.asave()
    return {"message": "Collection updated successfully"}


@router.delete("/collections/{collection_id}", tags=["collections"], auth=Bearer())
async def delete_collection(request: Request, collection_id: int) -> Dict[str, str]:
    """
    Delete a collection by its ID.

    This endpoint deletes a collection specified by the `collection_id` parameter.
    The collection must belong to the authenticated user.

    Args:
        request: The HTTP request object, which includes authentication information.
        collection_id (int): The ID of the collection to be deleted.

    Returns:
        dict: A message indicating that the collection was deleted successfully.

    Raises:
        HTTPException: If the collection does not exist or does not belong to the authenticated user.
    """
    collection = await aget_object_or_404(
        Collection, id=collection_id, owner=request.auth
    )
    await collection.adelete()
    return {"message": "Collection deleted successfully"}


"""Documents"""


class DocumentIn(Schema):
    name: str
    metadata: dict = Field(default_factory=dict)
    url: Optional[str] = None
    base64: Optional[str] = None

    @model_validator(mode="after")
    def base64_or_url(self) -> Self:
        if not self.url and not self.base64:
            raise ValueError("Either 'url' or 'base64' must be provided.")
        if self.url and self.base64:
            raise ValueError("Only one of 'url' or 'base64' should be provided.")
        return self


class PageOut(Schema):
    document_name: Optional[str] = None
    img_base64: str
    page_number: int


class DocumentOut(Schema):
    id: int
    name: str
    metadata: dict = Field(default_factory=dict)
    url: Optional[str] = None
    base64: Optional[str] = None
    num_pages: int
    collection_name: str
    pages: Optional[List[PageOut]] = None

    @model_validator(mode="after")
    def base64_or_url(self) -> Self:
        if not self.url and not self.base64:
            raise ValueError("Either 'url' or 'base64' must be provided.")
        if self.url and self.base64:
            raise ValueError("Only one of 'url' or 'base64' should be provided.")
        return self


class DocumentInPatch(Schema):
    name: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)
    url: Optional[str] = None
    base64: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if not any([self.name, self.metadata, self.url, self.base64]):
            raise ValueError("At least one field must be provided to update.")
        if self.url and self.base64:
            raise ValueError("Only one of 'url' or 'base64' should be provided.")
        return self


@router.post("/collections/{collection_id}/document", tags=["documents"], auth=Bearer())
async def upsert_document(
    request: Request, collection_id: int, payload: DocumentIn
) -> Dict[str, Union[int, str]]:
    """
    Create or update a document in a collection.

    This endpoint allows the user to create or update a document in a collection.
    The document can be provided as a URL or a base64-encoded string.

    Args:
        request: The HTTP request object, which includes the user information.
        collection_id (int): The ID of the collection where the document should be created or updated.
        payload (DocumentIn): The input data for creating or updating the document.

    Returns:
        dict: A dictionary containing the ID of the document and a success message.

    Raises:
        HttpError: If the document cannot be created or updated.
    """
    collection = await aget_object_or_404(
        Collection, id=collection_id, owner=request.auth
    )
    url = payload.url or ""
    base64 = payload.base64 or ""
    try:
        # we look up the document by name and collection
        # if it exists, we update its metadate and embeddings (by calling embed_document)
        exists = await Document.objects.filter(
            name=payload.name, collection=collection
        ).aexists()
        if exists:
            # we update the metadata and embeddings
            document = await Document.objects.aget(
                name=payload.name, collection=collection
            )
            document.metadata = payload.metadata
            document.url = url
            document.base64 = base64
        else:
            # we create a new document
            document = Document(
                name=payload.name,
                metadata=payload.metadata,
                collection=collection,
                url=url,
                base64=base64,
            )

        # this method will embed the document and save it to the database
        await document.embed_document()
        return {"id": document.id, "message": "Document created successfully"}
    except ValidationError as e:
        raise HttpError(400, str(e))


@router.get(
    "/collections/{collection_id}/documents/{document_id}",
    tags=["documents"],
    auth=Bearer(),
    response=DocumentOut,
)
async def get_document(
    request, collection_id: int, document_id: int, expand: Optional[str] = None
) -> DocumentOut:
    """
    Retrieve a specific document from a collection.

    Args:
        request: The HTTP request object.
        collection_id (int): The ID of the collection containing the document.
        document_id (int): The ID of the document to retrieve.
        expand (Optional[str]): A comma-separated list of fields to expand in the response.
                                If "pages" is included, the document's pages will be included.

    Returns:
        DocumentOut: The retrieved document with its details.

    Raises:
        HTTPException: If the document or collection is not found.
    """
    document = await aget_object_or_404(
        Document.objects.select_related("collection").annotate(
            num_pages=Count("pages")
        ),
        id=document_id,
        collection_id=collection_id,
    )
    document_out = DocumentOut(
        id=document.id,
        name=document.name,
        metadata=document.metadata,
        url=document.url,
        base64=document.base64,
        num_pages=document.num_pages,
        collection_name=document.collection.name,
    )
    if expand and "pages" in expand.split(","):
        document_out.pages = []
        async for page in document.pages.all():
            document_out.pages.append(
                PageOut(
                    document_name=document.name,
                    img_base64=page.img_base64,
                    page_number=page.page_number,
                )
            )
    return document_out


@router.get(
    "/collections/{collection_id}/documents",
    tags=["documents"],
    auth=Bearer(),
    response=List[DocumentOut],
)
async def list_documents(
    request: Request, collection_id: int, expand: Optional[str] = None
) -> List[DocumentOut]:
    """
    Fetch a list of documents for a given collection.

    This endpoint retrieves documents associated with a specified collection ID.
    Optionally, it can expand the response to include pages of each document.

    Args:
        request (Request): The request object.
        collection_id (int): The ID of the collection to fetch documents from.
        expand (Optional[str]): A comma-separated string specifying additional fields to include in the response.
                                If "pages" is included, the pages of each document will be included.

    Returns:
        List[DocumentOut]: A list of documents with their details. If expanded, includes pages of each document.

    Raises:
        HTTPException: If the collection or documents are not found.

    Example:
        GET /collections/1/documents?expand=pages
    """

    documents = []
    async for document in (
        Document.objects.select_related("collection")
        .annotate(num_pages=Count("pages"))
        .filter(collection_id=collection_id)
    ):
        document_out = DocumentOut(
            id=document.id,
            name=document.name,
            metadata=document.metadata,
            url=document.url,
            base64=document.base64,
            num_pages=document.num_pages,
            collection_name=document.collection.name,
        )
        if expand and "pages" in expand.split(","):
            document_out.pages = []
            async for page in document.pages.all():
                document_out.pages.append(
                    PageOut(
                        document_name=document.name,
                        img_base64=page.img_base64,
                        page_number=page.page_number,
                    )
                )
        documents.append(document_out)
    return documents


@router.patch(
    "/collections/{collection_id}/documents/{document_id}",
    tags=["documents"],
    auth=Bearer(),
)
async def partial_update_document(
    request: Request, collection_id: int, document_id: int, payload: DocumentInPatch
) -> Dict[str, str]:
    """
    Partially update a document.

    This endpoint allows for partial updates to a document's details. Only the fields provided in the payload will be updated.
    If the URL or base64 content is changed, the document will be re-embedded. Otherwise, only the metadata and name will be updated.

    Args:
        request: The request object containing authentication details.
        collection_id (int): The ID of the collection to which the document belongs.
        document_id (int): The ID of the document to be updated.
        payload (DocumentIn): The payload containing the fields to be updated.

    Returns:
        dict: A message indicating the document was updated successfully.

    Raises:
        HTTPException: If the document is not found or the user is not authorized to update it.
    """
    document = await aget_object_or_404(
        Document.objects.select_related("collection"),
        id=document_id,
        collection_id=collection_id,
    )
    if (payload.url and payload.url != document.url) or (
        payload.base64 and payload.base64 != document.base64
    ):
        # user had base64, but now gave url = delete base64 and embed url
        # user had url, but now gave base64 = delete url and embed base64
        # user had url, and now gave new url = embed url. Same url? no change
        # user had base64, and now gave new base64 = embed base64. Same base64? no change
        document.url = payload.url or ""
        document.base64 = payload.base64 or ""
        document.metadata = payload.metadata or document.metadata
        document.name = payload.name or document.name
        await document.embed_document()
    else:
        document.name = payload.name or document.name
        document.metadata = payload.metadata or document.metadata
        await document.asave()
    return {"message": "Document updated successfully"}


@router.delete(
    "/collections/{collection_id}/documents/{document_id}",
    tags=["documents"],
    auth=Bearer(),
)
async def delete_document(
    request: Request, collection_id: int, document_id: int
) -> Dict[str, str]:
    """
    Delete a document by its ID.

    This endpoint deletes a document specified by the `document_id` parameter.
    The document must belong to the authenticated user.

    Args:
        request: The HTTP request object, which includes authentication information.
        collection_id (int): The ID of the collection containing the document.
        document_id (int): The ID of the document to be deleted.

    Returns:
        dict: A message indicating that the document was deleted successfully.

    Raises:
        HTTPException: If the document does not exist or does not belong to the authenticated user.
    """
    document = await aget_object_or_404(
        Document.objects.select_related("collection"),
        id=document_id,
        collection_id=collection_id,
    )
    await document.adelete()
    return {"message": "Document deleted successfully"}


""" Search """


class QueryIn(Schema):
    query: str
    collection_id: Optional[int] = None
    top_k: Optional[int] = 3


class PageOutQuery(Schema):
    collection_name: str
    collection_id: int
    collection_metadata: Optional[dict] = {}
    document_name: str
    document_id: int
    document_metadata: Optional[dict] = {}
    page_number: int
    raw_score: float
    normalized_score: float
    img_base64: str


class QueryOut(Schema):
    query: str
    results: List[PageOutQuery]


@router.post("/search", tags=["search"], auth=Bearer())
async def search(request: Request, payload: QueryIn) -> QueryOut:
    """
    Search for pages similar to a given query.

    This endpoint allows the user to search for pages similar to a given query.
    The search is performed across all documents in the specified collection.

    Args:
        request: The HTTP request object, which includes the user information.
        payload (QueryIn): The input data for the search, which includes the query string and collection ID.

    Returns:
        QueryOut: The search results, including the query and a list of similar pages.

    Raises:
        HttpError: If the collection does not exist or the query is invalid.
    """
    query_embeddings = await get_query_embeddings(payload.query)

    query_length = len(query_embeddings)  # we need this for normalization

    # we want to cast the embeddings to halfvec
    casted_query_embeddings = [
        HalfVector(embedding).to_text() for embedding in query_embeddings
    ]

    # building the query: 1. get all pages in collection/collection owner
    base_query = Page.objects.select_related("document__collection")
    if payload.collection_id:
        base_query = base_query.filter(document__collection_id=payload.collection_id)
    else:
        base_query = base_query.filter(document__collection__owner=request.auth)

    # 2. annotate the query with the max sim score
    # maxsim needs 2 arrays of embeddings, one for the pages and one for the query
    pages_query = (
        base_query.annotate(page_embeddings=ArrayAgg("embeddings__embedding"))
        .annotate(max_sim=MaxSim("page_embeddings", casted_query_embeddings))
        .order_by("-max_sim")[: payload.top_k or 3]
    )
    # 3. execute the query
    results = pages_query.values(
        "id",
        "page_number",
        "img_base64",
        "document__id",
        "document__name",
        "document__metadata",
        "document__collection__id",
        "document__collection__name",
        "document__collection__metadata",
        "max_sim",
    )
    # Normalization
    extra_tokens = 12
    normalization_factor = query_length + extra_tokens

    # Format the results
    formatted_results = [
        PageOutQuery(
            collection_name=row["document__collection__name"],
            collection_id=row["document__collection__id"],
            collection_metadata=(
                row["document__collection__metadata"]
                if row["document__collection__metadata"]
                else {}
            ),
            document_name=row["document__name"],
            document_id=row["document__id"],
            document_metadata=(
                row["document__metadata"] if row["document__metadata"] else {}
            ),
            page_number=row["page_number"],
            raw_score=row["max_sim"],
            normalized_score=row["max_sim"] / normalization_factor,
            img_base64=row["img_base64"],
        )
        async for row in results
    ]
    return QueryOut(query=payload.query, results=formatted_results)


async def get_query_embeddings(query: str) -> List:
    EMBEDDINGS_URL = settings.EMBEDDINGS_URL
    embed_token = settings.EMBEDDINGS_URL_TOKEN
    headers = {"Authorization": f"Bearer {embed_token}"}
    payload = {
        "input": {
            "task": "query",
            "input_data": [query],
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            EMBEDDINGS_URL, json=payload, headers=headers
        ) as response:
            if response.status != 200:
                raise ValidationError(
                    "Failed to get embeddings from the embeddings service."
                )
            out = await response.json()
            # returning  a dynamic array of embeddings, each of which is a list of 128 floats
            # example: [[0.1, 0.2, 0.3, ...], [0.4, 0.5, 0.6, ...]]
            return out["output"]["data"][0]["embedding"]
    return []


""" helpers """


class FileOut(Schema):
    img_base64: str
    page_number: int


@router.post(
    "helpers/file-to-imgbase64", tags=["helpers"], response=List[FileOut], auth=Bearer()
)
async def file_to_imgbase64(request, file: UploadedFile = File(...)) -> List[FileOut]:
    """
    Upload one file, converts to images and return their base64 encoded strings with 1-indexed page numberss.

    Args:
        request: The HTTP request object.
        file UploadedFile): One uploaded file

    Returns:
        List[FileOut]: A list of FileOut objects containing the base64 encoded strings of the images.
    """
    document_data = file.read()
    document = Document()
    img_base64 = await document._prep_document(document_data)
    results = []
    for i, img in enumerate(img_base64):
        results.append(FileOut(img_base64=img, page_number=i + 1))
    return results


@router.post("helpers/file-to-base64", tags=["helpers"], auth=Bearer())
async def file_to_base64(request, file: UploadedFile = File(...)) -> Dict[str, str]:
    """
    Upload one file, converts to base64 encoded strings.

    Args:
        request: The HTTP request object.
        file UploadedFile): One uploaded file

    Returns:
    str: base64 encoded string of the file.
    """
    document_data = file.read()
    return {"data": base64.b64encode(document_data).decode()}


# Emeddings - send a document or a query, get embeddings back - Example Response {"page_1": [0.1, 0.2, 0.3, ...], "page_2": [0.4, 0.5, 0.6, ...]}
