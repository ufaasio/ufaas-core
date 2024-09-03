import logging

import httpx
import pytest

from ..constants import StaticData


@pytest.mark.asyncio
async def test_wallet_list_user(
    client: httpx.AsyncClient, access_token_user, constants
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(f"/api/v1/wallets/", headers=auth_headers)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert type(resp_json.get("items")) == list
    assert len(resp_json.get("items")) == 1
    wallet = resp_json.get("items")[0]
    constants.wallet_id_1_2 = wallet.get("uid")


@pytest.mark.asyncio
async def test_wallet_retrieve_user(
    client: httpx.AsyncClient, access_token_user, constants
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/wallets/{constants.wallet_id_1_2}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("uid") == constants.wallet_id_1_2
    assert resp_json.get("user_id") == constants.user_id_1_2


@pytest.mark.asyncio
async def test_wallet_create_user(
    client: httpx.AsyncClient, access_token_user, constants
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    data = dict(user_id=constants.user_id_1_1)
    response = await client.post(f"/api/v1/wallets/", headers=auth_headers, json=data)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_update_user(
    client: httpx.AsyncClient, access_token_user, constants
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    data = dict(meta_data={"key": "value"})
    response = await client.patch(
        f"/api/v1/wallets/{constants.wallet_id_1_2}", headers=auth_headers, json=data
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_delete_user(
    client: httpx.AsyncClient, access_token_user, constants
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.delete(
        f"/api/v1/wallets/{constants.wallet_id_1_2}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wallet_retrieve_user_have_balance(
    client: httpx.AsyncClient, access_token_user, wallet_2_original_balance
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/wallets/{StaticData.wallet_id_1_2}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json.get("uid") == StaticData.wallet_id_1_2
    assert resp_json.get("user_id") == StaticData.user_id_1_2

    for currency, balance in resp_json.get("balance").items():
        resp_json.get("balance")[currency] = int(float(balance))
    assert resp_json.get("balance") == {"USD": 400}
