import logging

import httpx
import pytest
from apps.accounting.models import Wallet
from apps.accounting.schemas import TransactionSchema


@pytest.mark.asyncio
async def test_get_transactions(
    client: httpx.AsyncClient, access_token_user, wallet_2: Wallet
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(f"/api/v1/transactions/", headers=auth_headers)
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200

    transactions = await wallet_2.get_transactions()
    transactions = [
        TransactionSchema(**transaction.__dict__, note=None)
        for transaction in transactions
    ]
    logging.info(
        "Transactions: \n" + "\n".join(str(transaction) for transaction in transactions)
    )

    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/transactions/{transactions[0].uid}", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_transactions(
    client: httpx.AsyncClient, access_token_user, wallet_2: Wallet
):
    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.get(
        f"/api/v1/wallets/{wallet_2.uid}/transactions/", headers=auth_headers
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200

    transactions = await wallet_2.get_transactions()
    transactions = [
        TransactionSchema(**transaction.__dict__, note=None)
        for transaction in transactions
    ]
    logging.info(
        "Transactions: \n" + "\n".join(str(transaction) for transaction in transactions)
    )

    auth_headers = {"Authorization": f"Bearer {access_token_user}"}
    response = await client.patch(
        f"/api/v1/transactions/{transactions[0].uid}",
        headers=auth_headers,
        json={"note": "Test note"},
    )
    resp_json = response.json()
    logging.info(f"{resp_json}")
    assert response.status_code == 200
    assert resp_json["note"] == "Test note"
