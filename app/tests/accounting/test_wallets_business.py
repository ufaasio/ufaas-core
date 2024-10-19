import logging

import httpx
import pytest

from ..constants import StaticData


@pytest.mark.asyncio
async def test_wallet_create_business(
    constants: StaticData, client: httpx.AsyncClient, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    data = dict(user_id=constants.user_id_1_1)
    response = await client.post(f"/api/v1/wallets/", headers=auth_headers, json=data)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 201
    assert resp_json.get("user_id") == data.get("user_id")
    constants.wallet_id_1_1 = resp_json.get("uid")


@pytest.mark.asyncio
async def test_wallet_update_business(
    constants: StaticData, client: httpx.AsyncClient, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    data = dict(meta_data={"key": "value"})
    response = await client.patch(
        f"/api/v1/wallets/{constants.wallet_id_1_1}", headers=auth_headers, json=data
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("meta_data") == data.get("meta_data")

    response = await client.get(
        f"/api/v1/wallets/{constants.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("meta_data") == data.get("meta_data")


@pytest.mark.asyncio
async def test_wallet_list_business(client: httpx.AsyncClient, access_token_business):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    response = await client.get(f"/api/v1/wallets/", headers=auth_headers)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert type(resp_json.get("items")) == list
    assert len(resp_json.get("items")) > 0


@pytest.mark.asyncio
async def test_wallet_delete_business(
    constants: StaticData, client: httpx.AsyncClient, access_token_business
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    response = await client.get(
        f"/api/v1/wallets/{constants.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("is_deleted") == False

    response = await client.delete(
        f"/api/v1/wallets/{constants.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("is_deleted") == True

    response = await client.get(
        f"/api/v1/wallets/{constants.wallet_id_1_1}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 404
