import base64

import pytest
from accounts.models import CustomUser
from ninja.testing import TestAsyncClient

from .models import Collection, Document, Page, PageEmbedding
from .views import Bearer, QueryFilter, QueryIn, filter_query, router


# sanity check
async def test_sanity():
    assert 1 == 1


pytestmark = [pytest.mark.django_db(transaction=True, reset_sequences=True)]

""" Authentication tests """


@pytest.fixture
async def user(db):
    """
    Fixture to create a test user with a token.
    """
    # get or create a user
    # delete any existing users
    await CustomUser.objects.all().adelete()
    user, _ = await CustomUser.objects.aget_or_create(
        username="test_user", token="valid_token"
    )
    return user


@pytest.fixture
def bearer():
    """
    Fixture to create an instance of the Bearer class.
    """
    return Bearer()


@pytest.fixture
def async_client():
    """
    Fixture to create an instance of the TestAsyncClient class.
    """
    return TestAsyncClient(router)


@pytest.fixture
async def collection(user):
    """
    Fixture to create a test collection.
    """
    # delete any existing collections
    await Collection.objects.all().adelete()
    collection, _ = await Collection.objects.aget_or_create(
        name="Test Collection Fixture", metadata={"key": "value"}, owner=user
    )
    return collection


@pytest.fixture
async def document(user, collection):
    """
    Fixture to create a test document.
    """
    # delete any existing documents
    await Document.objects.all().adelete()
    document, _ = await Document.objects.aget_or_create(
        name="Test Document Fixture",
        collection=collection,
        url="https://www.example.com",
    )
    # create a page for the document
    page = await Page.objects.acreate(
        document=document,
        page_number=1,
        img_base64="base64_string",
    )
    await PageEmbedding.objects.acreate(
        page=page,
        embedding=[0.1 for _ in range(128)],
    )
    return document


async def test_valid_token(bearer, user):
    """
    Test that a valid token authenticates the user successfully.
    """
    request = None  # We don't need the request object for this test
    token = "valid_token"

    authenticated_user = await bearer.authenticate(request, token)

    assert authenticated_user is not None
    assert authenticated_user.username == user.username


async def test_invalid_token(bearer, user):
    """
    Test that an invalid token returns None (authentication fails).
    """
    request = None
    token = "invalid_token"

    authenticated_user = await bearer.authenticate(request, token)

    assert authenticated_user is None


async def test_missing_token(bearer):
    """
    Test that a missing token returns None.
    """
    request = None
    token = None  # No token provided

    authenticated_user = await bearer.authenticate(request, token)

    assert authenticated_user is None


""" Collection tests """


async def test_create_collection(async_client, user):
    response = await async_client.post(
        "/collections",
        json={"name": "Test Collection Fixture", "metadata": {"key": "value"}},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 201
    # we return collectionOut in the response
    assert response.json() == {
        "id": 1,
        "name": "Test Collection Fixture",
        "metadata": {"key": "value"},
    }


async def test_create_collection_unique(async_client, user, collection):
    response = await async_client.post(
        "/collections",
        json={"name": "Test Collection Fixture", "metadata": {"key": "value"}},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 409


async def test_get_collections(async_client, user, collection):
    collection_name = "Test Collection Fixture"
    response = await async_client.get(
        f"/collections/{collection_name}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test Collection Fixture",
        "metadata": {"key": "value"},
    }


async def test_list_collection(async_client, user, collection):
    response = await async_client.get(
        "/collections",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Test Collection Fixture", "metadata": {"key": "value"}}
    ]


async def test_patch_collection(async_client, user, collection):
    collection_name = "Test Collection Fixture"
    response = await async_client.patch(
        f"/collections/{collection_name}",
        json={"name": "Test Collection Update", "metadata": {"key": "value"}},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test Collection Update",
        "metadata": {"key": "value"},
    }

    # now check if the collection was actually updated
    new_collection_name = "Test Collection Update"
    response = await async_client.get(
        f"/collections/{new_collection_name}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test Collection Update",
        "metadata": {"key": "value"},
    }


async def test_delete_collection(async_client, user, collection):
    collection_name = "Test Collection Fixture"
    response = await async_client.delete(
        f"/collections/{collection_name}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 204

    # now check if the collection was actually deleted
    response = await async_client.get(
        f"/collections/{collection_name}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 404


""" Document tests """


async def test_create_document_pdf_url(async_client, user, collection):
    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "url": "https://pdfobject.com/pdf/sample.pdf",
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}


async def test_create_document_pdf_base64(async_client, user, collection):
    # test_docs/ is a directory in the root of the project - we will use a sample PDF file from there

    with open("test_docs/sample.pdf", "rb") as f:
        # convert the file to base64
        base64_string = base64_string = base64.b64encode(f.read()).decode("utf-8")

    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "base64": base64_string,
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}


async def test_create_document_docx_url(async_client, user, collection):
    url = "https://www.cte.iup.edu/cte/Resources/DOCX_TestPage.docx"
    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "url": url,
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}

    await Document.objects.all().adelete()


async def test_create_document_docx_base64(async_client, user, collection):
    with open("test_docs/sample.docx", "rb") as f:
        # convert the file to base64
        base64_string = base64.b64encode(f.read()).decode("utf-8")

    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "base64": base64_string,
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}


async def test_create_document_webpage(async_client, user, collection):
    url = "https://gotenberg.dev/docs/getting-started/introduction"
    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "url": url,
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}


async def test_create_document_image_url(async_client, user, collection):
    url = "https://www.w3schools.com/w3css/img_lights.jpg"
    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "url": url,
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}


async def test_create_document_image_base64(async_client, user, collection):
    with open("test_docs/sample.png", "rb") as f:
        # convert the file to base64
        base64_string = base64.b64encode(f.read()).decode("utf-8")

    response = await async_client.post(
        "/collections/1/document",
        json={
            "name": "Test Document Fixture",
            "base64": base64_string,
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Document created successfully"}


async def test_get_document_by_id(async_client, user, collection, document):
    response = await async_client.get(
        "/collections/1/documents/1?expand=pages",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test Document Fixture",
        "metadata": {},
        "url": "https://www.example.com",
        "base64": "",
        "num_pages": 1,
        "collection_name": "Test Collection Fixture",
        "pages": [
            {
                "document_name": "Test Document Fixture",
                "img_base64": "base64_string",
                "page_number": 1,
            }
        ],
    }


async def test_get_documents(async_client, user, collection, document):
    response = await async_client.get(
        "/collections/1/documents",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Test Document Fixture",
            "metadata": {},
            "url": "https://www.example.com",
            "base64": "",
            "num_pages": 1,
            "collection_name": "Test Collection Fixture",
            "pages": None,
        }
    ]


async def test_patch_document_no_embed(async_client, user, collection, document):
    response = await async_client.patch(
        "/collections/1/documents/1",
        json={"name": "Test Document Update", "metadata": {"key": "value"}},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Document updated successfully"}

    # now check if the document was actually updated
    response = await async_client.get(
        "/collections/1/documents/1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test Document Update",
        "metadata": {"key": "value"},
        "url": "https://www.example.com",
        "base64": "",
        "num_pages": 1,
        "collection_name": "Test Collection Fixture",
        "pages": None,
    }


async def test_patch_document_embed(async_client, user, collection, document):
    # we will change the base64 string of the page
    with open("test_docs/sample.png", "rb") as f:
        # convert the file to base64
        base64_string = base64.b64encode(f.read()).decode("utf-8")

    # we updated the base64 string of the page
    response = await async_client.patch(
        "/collections/1/documents/1",
        json={
            "name": "Test Document Update",
            "base64": base64_string,
            "metadata": {"key": "value"},
        },
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Document updated successfully"}


async def test_delete_document(async_client, user, collection, document):
    response = await async_client.delete(
        "/collections/1/documents/1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Document deleted successfully"}

    # now check if the document was actually deleted
    response = await async_client.get(
        "/collections/1/documents/1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 404


async def test_search_documents(async_client, user, collection, document):
    response = await async_client.post(
        "/search",
        json={"query": "What is 1 + 1", "top_k": 1},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() != []


""" Search Filtering tests """


# we will create a fixture just for these tests
@pytest.fixture
async def search_filter_fixture(user):
    collection, _ = await Collection.objects.aget_or_create(
        name="Test Collection Filtering Fixture",
        metadata={"type": "AI papers"},
        owner=user,
    )
    document_1, _ = await Document.objects.aget_or_create(
        name="Attention is All You Need",
        collection=collection,
        url="https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf",
        metadata={"important": True},
    )
    document_2, _ = await Document.objects.aget_or_create(
        name="BMX : Entropy-weighted Similarity and Semantic-enhanced Lexical Search",
        collection=collection,
        url="https://arxiv.org/pdf/2408.06643v2",
        metadata={"important": False},
    )
    # create or get a page for the document
    page_1, _ = await Page.objects.aget_or_create(
        document=document_1,
        page_number=1,
        defaults={"img_base64": "base64_string"},
    )

    await PageEmbedding.objects.aget_or_create(
        page=page_1,
        defaults={"embedding": [0.1 for _ in range(128)]},
    )
    # create or get a page for the document
    page_2, _ = await Page.objects.aget_or_create(
        document=document_2,
        page_number=1,
        defaults={"img_base64": "base64_string"},
    )

    await PageEmbedding.objects.aget_or_create(
        page=page_2,
        defaults={"embedding": [0.1 for _ in range(128)]},
    )
    return collection, document_1, document_2


async def test_search_filter_collection_id(async_client, user, collection, document):
    response = await async_client.post(
        "/search",
        json={"query": "What is 1 + 1", "top_k": 1, "collection_id": 1},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() != []


async def test_search_filter_key_equals(async_client, user, search_filter_fixture):
    collection, document_1, document_2 = search_filter_fixture

    # Create a QueryIn object with a collection_id and a query_filter
    query_in = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(
            on="document", key="important", value=True, lookup="key_lookup"
        ),
    )

    # Call the filter_query function
    result = await filter_query(query_in, user)

    # Check if the result is a QuerySet
    assert isinstance(result, Page.objects.all().__class__)

    # Check if only one document is returned (the one with important=True)
    count = await result.acount()
    assert count == 1
    # get the page from the queryset
    page = await result.afirst()
    # check if the page belongs to the correct document
    assert page.document == document_1


async def test_filter_query_document_contains(search_filter_fixture, user):
    collection, document_1, _ = search_filter_fixture
    query_in = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(
            on="document", key="important", value=True, lookup="contains"
        ),
    )
    result = await filter_query(query_in, user)
    count = await result.acount()
    assert count == 1
    page = await result.afirst()
    assert page.document == document_1


async def test_filter_query_collection_metadata(search_filter_fixture, user):
    collection, _, _ = search_filter_fixture
    query_in = QueryIn(
        query="test query",
        query_filter=QueryFilter(
            on="collection", key="type", value="AI papers", lookup="key_lookup"
        ),
    )
    result = await filter_query(query_in, user)
    count = await result.acount()
    assert count == 2

    # now check when count should be 0
    query_in = QueryIn(
        query="test query",
        query_filter=QueryFilter(
            on="collection", key="type", value="AI papers 2", lookup="key_lookup"
        ),
    )
    result = await filter_query(query_in, user)
    count = await result.acount()
    assert count == 0


async def test_filter_query_has_key(search_filter_fixture, user):
    collection, _, _ = search_filter_fixture
    query_in = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(on="document", key="important", lookup="has_key"),
    )
    result = await filter_query(query_in, user)
    count = await result.acount()
    assert count == 2

    # test if key is not there
    query_in_2 = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(on="document", key="not_there", lookup="has_key"),
    )
    result = await filter_query(query_in_2, user)
    count = await result.acount()
    assert count == 0


async def test_filter_query_has_keys(search_filter_fixture, user):
    collection, _, _ = search_filter_fixture
    query_in = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(on="document", key=["important"], lookup="has_keys"),
    )
    result = await filter_query(query_in, user)
    count = await result.acount()
    assert count == 2

    # test if key is not there
    query_in_2 = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(on="document", key=["not_there"], lookup="has_keys"),
    )
    result = await filter_query(query_in_2, user)
    count = await result.acount()
    assert count == 0


async def test_filter_query_document_contained_by(search_filter_fixture, user):
    collection, document_1, _ = search_filter_fixture
    query_in = QueryIn(
        query="test query",
        collection_id=collection.id,
        query_filter=QueryFilter(
            on="document", key="important", value=True, lookup="contained_by"
        ),
    )
    result = await filter_query(query_in, user)
    count = await result.acount()
    assert count == 1
    page = await result.afirst()
    assert page.document == document_1


""" Embedding tests """


async def test_create_embedding(async_client, user):
    task = "query"
    input_data = ["What is 1 + 1"]
    response = await async_client.post(
        "/embeddings",
        json={"task": task, "input_data": input_data},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"] != []


""" Model tests """


async def test_collection_str_method(collection):
    assert str(collection) == "Test Collection Fixture"


async def test_document_str_method(document):
    assert str(document) == "Test Document Fixture"


async def test_page_str_method(document):
    page = await Page.objects.acreate(
        document=document,
        page_number=1,
        img_base64="base64_string",
    )
    assert str(page) == "Test Document Fixture - Page 1"
