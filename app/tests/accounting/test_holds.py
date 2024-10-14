import logging
import uuid

import httpx
import pytest

from apps.accounting.models import Wallet

from ..constants import StaticData


@pytest.mark.asyncio
async def test_holds_user(
    client: httpx.AsyncClient, access_token_user, wallet_1: Wallet
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/wallets/{wallet_1.uid}/holds/", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_holds_user_USD(
    client: httpx.AsyncClient, access_token_user, wallet_1: Wallet
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/wallets/{wallet_1.uid}/holds/USD", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_holds_create_user(
    client: httpx.AsyncClient, access_token_user, wallet_1: Wallet
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    data = {"amount": 100, "expires_at": "2024-10-01T00:00:00Z"}
    currency = "USD"
    response = await client.post(
        f"/api/v1/wallets/{wallet_1.uid}/holds/{currency}",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_proposal_api_update_user(
    access_token_user: str,
    client: httpx.AsyncClient,
):
    auth_headers = {
        "Authorization": f"Bearer {access_token_user}",
        "Content-Type": "application/json",
    }
    response = await client.patch(
        f"/api/v1/holds/{uuid.uuid4()}",
        headers=auth_headers,
        json={"meta_data": {"key": "value"}},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_holds_create_business_not_found(
    client: httpx.AsyncClient,
    access_token_business,
    wallet_1: Wallet,
    constants: StaticData,
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    data = {
        "amount": 100,
        "expires_at": "2024-10-01T00:00:00Z",
        "user_id": constants.user_id_1_1,
    }
    currency = "USD"
    response = await client.post(
        f"/api/v1/wallets/{constants.wallet_id_1_3}/holds/{currency}",
        headers=auth_headers,
        json=data,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_holds_create_business(
    client: httpx.AsyncClient, access_token_business, wallet_1: Wallet, constants
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    data = {
        "amount": 100,
        "expires_at": "2024-10-01T00:00:00Z",
        "user_id": constants.user_id_1_1,
    }
    currency = "USD"
    response = await client.post(
        f"/api/v1/wallets/{wallet_1.uid}/holds/{currency}",
        headers=auth_headers,
        json=data,
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 201

    # update
    data = {
        "description": "for test",
    }
    response = await client.patch(
        f"/api/v1/holds/{resp_json.get('uid')}",
        headers=auth_headers,
        json=data,
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")

    assert response.status_code == 200
