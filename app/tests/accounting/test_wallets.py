import logging

import httpx
import pytest
import pytest_asyncio

from apps.accounting.models import Wallet
from apps.business_mongo.models import Business

from ..constants import StaticData


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_business():
    business = Business(
        business_id=StaticData.business_id_1,
        business_name=StaticData.business_name_1,
        domain=StaticData.business_domain_1,
        name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
    )
    await business.save()
    yield business
    await business.delete()


@pytest.fixture(scope="module")
def setup_wallet():
    async def mock_get_balance(self, currency=None):
        if currency is None:
            return {"USD": 500}

        return {currency: 500 if currency == "USD" else 0}

    original_get_balance = Wallet.get_balance
    Wallet.get_balance = mock_get_balance
    yield
    Wallet.get_balance = original_get_balance


@pytest.mark.asyncio
async def test_wallet_list_user(client: httpx.AsyncClient, db, access_token_user):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(f"/api/v1/wallets/", headers=auth_headers)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert type(resp_json.get("items")) == list
    assert len(resp_json.get("items")) == 1
    wallet = resp_json.get("items")[0]
    StaticData.wallet_id_1_2 = wallet.get("uid")


@pytest.mark.asyncio
async def test_wallet_retrieve_user(client: httpx.AsyncClient, db, access_token_user):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/wallets/{StaticData.wallet_id_1_2}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("uid") == StaticData.wallet_id_1_2


@pytest.mark.asyncio
async def test_wallet_create_user(client: httpx.AsyncClient, db, access_token_user):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    data = dict(user_id=StaticData.user_id_1_1)
    response = await client.post(f"/api/v1/wallets/", headers=auth_headers, json=data)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_update_user(client: httpx.AsyncClient, db, access_token_user):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    data = dict(meta_data={"key": "value"})
    response = await client.patch(
        f"/api/v1/wallets/{StaticData.wallet_id_1_2}", headers=auth_headers, json=data
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_delete_user(client: httpx.AsyncClient, db, access_token_user):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.delete(
        f"/api/v1/wallets/{StaticData.wallet_id_1_2}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_create_business(
    client: httpx.AsyncClient, db, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    data = dict(user_id=StaticData.user_id_1_1)
    response = await client.post(f"/api/v1/wallets/", headers=auth_headers, json=data)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 201
    assert resp_json.get("user_id") == data.get("user_id")
    StaticData.wallet_id_1_1 = resp_json.get("uid")


@pytest.mark.asyncio
async def test_wallet_update_business(
    client: httpx.AsyncClient, db, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    data = dict(meta_data={"key": "value"})
    response = await client.patch(
        f"/api/v1/wallets/{StaticData.wallet_id_1_1}", headers=auth_headers, json=data
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("meta_data") == data.get("meta_data")

    response = await client.get(
        f"/api/v1/wallets/{StaticData.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("meta_data") == data.get("meta_data")


@pytest.mark.asyncio
async def test_wallet_list_business(
    client: httpx.AsyncClient, db, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    response = await client.get(f"/api/v1/wallets/", headers=auth_headers)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert type(resp_json.get("items")) == list
    assert len(resp_json.get("items")) >= 3


@pytest.mark.asyncio
async def test_wallet_delete_business(
    client: httpx.AsyncClient, db, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    response = await client.get(
        f"/api/v1/wallets/{StaticData.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("is_deleted") == False

    response = await client.delete(
        f"/api/v1/wallets/{StaticData.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("is_deleted") == True

    response = await client.get(
        f"/api/v1/wallets/{StaticData.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 404
