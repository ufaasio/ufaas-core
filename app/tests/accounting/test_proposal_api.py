import logging

import httpx
import pytest

from apps.accounting.models import Participant, Proposal, Wallet

from ..constants import StaticData


@pytest.mark.asyncio
async def test_invalid_proposal_api_user(
    constants: StaticData,
    wallet_1: Wallet,
    wallet_2: Wallet,
    access_token_user: str,
    client: httpx.AsyncClient,
):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="USD",
        task_status="init",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=100),
            Participant(wallet_id=wallet_2.uid, amount=-100),
        ],
        note="Test note",
    )

    auth_headers = {
        "Authorization": f"Bearer {access_token_user}",
        "Content-Type": "application/json",
    }
    response = await client.post(
        f"/api/v1/proposals/", headers=auth_headers, content=proposal.model_dump_json()
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_proposal_api_list_business(
    access_token_business: str, client: httpx.AsyncClient
):
    auth_headers = {"Authorization": f"Bearer {access_token_business}"}
    response = await client.get(f"/api/v1/proposals/", headers=auth_headers)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_valid_proposal_api_create_business(
    constants: StaticData,
    wallet_1: Wallet,
    wallet_2: Wallet,
    access_token_business: str,
    client: httpx.AsyncClient,
):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="USD",
        task_status="draft",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=100),
            Participant(wallet_id=wallet_2.uid, amount=-100),
        ],
        note="Test note",
    )

    auth_headers = {
        "Authorization": f"Bearer {access_token_business}",
        "Content-Type": "application/json",
    }
    response = await client.post(
        f"/api/v1/proposals/",
        headers=auth_headers,
        content=proposal.model_dump_json(exclude={"user_id"}),
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 201
    proposal_id = resp_json.get("uid")

    response = await client.patch(
        f"/api/v1/proposals/{proposal_id}",
        headers=auth_headers,
        json={"meta_data": {"key": "value"}},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200

    response = await client.patch(
        f"/api/v1/proposals/{proposal_id}",
        headers=auth_headers,
        json={"task_status": "init"},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_proposal_api_update_business(
    constants: StaticData,
    wallet_1: Wallet,
    wallet_2: Wallet,
    access_token_business: str,
    client: httpx.AsyncClient,
):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="USD",
        task_status="init",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=100),
            Participant(wallet_id=wallet_2.uid, amount=-100),
        ],
        note="Test note",
    )

    auth_headers = {
        "Authorization": f"Bearer {access_token_business}",
        "Content-Type": "application/json",
    }
    response = await client.post(
        f"/api/v1/proposals/",
        headers=auth_headers,
        content=proposal.model_dump_json(exclude={"user_id"}),
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 201
    proposal_id = resp_json.get("uid")

    response = await client.patch(
        f"/api/v1/proposals/{proposal_id}",
        headers=auth_headers,
        json={"meta_data": {"key": "value"}},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 400

    response = await client.patch(
        f"/api/v1/proposals/{proposal_id}",
        headers=auth_headers,
        json={"task_status": "draft"},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_valid_proposal_api_start_business(
    constants: StaticData,
    wallet_1: Wallet,
    wallet_2: Wallet,
    access_token_business: str,
    client: httpx.AsyncClient,
):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="USD",
        task_status="draft",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=100),
            Participant(wallet_id=wallet_2.uid, amount=-100),
        ],
        note="Test note",
    )

    auth_headers = {
        "Authorization": f"Bearer {access_token_business}",
        "Content-Type": "application/json",
    }
    response = await client.post(
        f"/api/v1/proposals/",
        headers=auth_headers,
        content=proposal.model_dump_json(exclude={"user_id"}),
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 201

    response = await client.post(
        f"/api/v1/proposals/{resp_json.get('uid')}/start",
        headers=auth_headers,
        json={"task_status": "init"},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
