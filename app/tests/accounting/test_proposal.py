import logging

import httpx
import pytest

from apps.accounting.models import Participant, Proposal, Wallet
from apps.accounting.schemas import TransactionSchema
from apps.accounting.services import process_proposal


@pytest.mark.asyncio
async def test_invalid_proposal_not_balanced(
    constants, wallet_1: Wallet, wallet_2: Wallet
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
            Participant(wallet_id=wallet_2.uid, amount=-1000),
        ],
    )

    await process_proposal(proposal)
    assert proposal.task_status == "error"


@pytest.mark.asyncio
async def test_invalid_proposal_not_balanced2(
    constants, wallet_1: Wallet, wallet_2: Wallet
):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="USD",
        task_status="init",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=1000),
            Participant(wallet_id=wallet_2.uid, amount=-1000),
        ],
    )

    await process_proposal(proposal)
    assert proposal.task_status == "error"


@pytest.mark.asyncio
async def test_invalid_proposal_no_participants(constants):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="USD",
        task_status="init",
        participants=[],
    )

    await process_proposal(proposal)
    assert proposal.task_status == "error"


@pytest.mark.asyncio
async def test_invalid_proposal_draft(constants, wallet_1: Wallet, wallet_2: Wallet):
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
    )

    await process_proposal(proposal)
    assert proposal.task_status == "error"


@pytest.mark.asyncio
async def test_invalid_proposal_no_amount(
    constants, wallet_1: Wallet, wallet_2: Wallet
):
    proposal = Proposal(
        business_name=constants.business_name_1,
        user_id=constants.user_id_1_1,
        issuer_id=constants.business_id_1,
        amount=100,
        currency="IRT",
        task_status="init",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=100),
            Participant(wallet_id=wallet_2.uid, amount=-100),
        ],
    )

    await process_proposal(proposal)
    assert proposal.task_status == "error"


@pytest.mark.asyncio
async def test_valid_proposal(constants, wallet_1: Wallet, wallet_2: Wallet):
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

    await proposal.start_processing()
    assert proposal.task_status == "completed"

    transactions = await wallet_1.get_transactions()
    transactions = [
        TransactionSchema(**transaction.__dict__, note=None)
        for transaction in transactions
    ]

    logging.info(
        "Transactions: \n" + "\n".join(str(transaction) for transaction in transactions)
    )

    proposal_transactions = await proposal.get_transactions()
    transactions = [
        TransactionSchema(**transaction.__dict__, note=None)
        for transaction in proposal_transactions
    ]

    logging.info(
        "Transactions: \n" + "\n".join(str(transaction) for transaction in transactions)
    )


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
