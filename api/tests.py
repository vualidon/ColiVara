import random

import pytest
from ninja.testing import TestAsyncClient

from accounts.models import CustomUser

from .models import Collection
from .views import Bearer, router


# sanity check
async def test_sanity():
    assert 1 == 1


pytestmark = [pytest.mark.django_db]

""" Authentication tests """


@pytest.fixture
async def user(db):
    """
    Fixture to create a test user with a token.
    """
    # get or create a user
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
    return await Collection.objects.aget_or_create(
        name="Test Collection Fixture", metadata={"key": "value"}, owner=user
    )


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
    assert response.status_code == 200
    assert response.json() == {"id": 1, "message": "Collection created successfully"}


async def test_create_collection_unique(async_client, user, collection):
    response = await async_client.post(
        "/collections",
        json={"name": "Test Collection Fixture", "metadata": {"key": "value"}},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 409


async def test_get_collections(async_client, user, collection):
    response = await async_client.get(
        "/collections/1",
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
    response = await async_client.patch(
        "/collections/1",
        json={"name": "Test Collection Update", "metadata": {"key": "value"}},
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Collection updated successfully"}

    # now check if the collection was actually updated
    response = await async_client.get(
        "/collections/1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Test Collection Update",
        "metadata": {"key": "value"},
    }


async def test_delete_collection(async_client, user, collection):
    response = await async_client.delete(
        "/collections/1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Collection deleted successfully"}

    # now check if the collection was actually deleted
    response = await async_client.get(
        "/collections/1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 404


# documents tests
# 1. pdf url: https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf
# 2. pdf base64
# 3. docx url
# 4. docx base64
# 5. web page url
# 6. Image url
# 7. Image base64
