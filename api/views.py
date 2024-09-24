from typing import Dict, List, Optional, Union

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.http.request import HttpRequest
from django.shortcuts import aget_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import HttpBearer
from pydantic import Field, model_validator
from typing_extensions import Self

from accounts.models import CustomUser

from .models import Collection, Document

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

# get document by id (R)
# list documents in collection (R)
# patch document by id (U)
# delete document by id (D)


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


# search index (search for pages with embeddings similar to a given query)
# delete index (delete a collection and all its documents and pages)
# Emeddings - send a document or a query, get embeddings back - Example Response {"page_1": [0.1, 0.2, 0.3, ...], "page_2": [0.4, 0.5, 0.6, ...]}
