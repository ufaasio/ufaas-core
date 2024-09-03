import logging

import pytest
import pytest_asyncio

from apps.accounting.models import Participant, Proposal, Wallet
from apps.accounting.schemas import TransactionSchema
from apps.accounting.services import (
    ParticipantWallet,
    get_participant_wallets,
    process_proposal,
)

from .constants import StaticData


@pytest.fixture(scope="module")
def setup_wallet():
    async def mock_get_balance(self, currency=None):
        if currency is None:
            return {"USD": 500}

        return {currency: 500 if currency == "USD" else 0}

    Wallet.get_balance = mock_get_balance


@pytest_asyncio.fixture(scope="module")
async def wallet_1(db):
    wallet = Wallet(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        uid=StaticData.wallet_id_1_1,
    )
    await wallet.save(exclude={"holds"})
    return wallet


@pytest_asyncio.fixture(scope="module")
async def wallet_2(db):
    wallet = Wallet(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_2,
        uid=StaticData.wallet_id_1_2,
    )
    await wallet.save(exclude={"holds"})
    return wallet


@pytest.mark.asyncio
async def test_get_participant_wallets(
    wallet_1: Wallet, wallet_2: Wallet, setup_wallet
):
    participants = [
        Participant(wallet_id=wallet_1.uid, amount=100),
        Participant(wallet_id=wallet_2.uid, amount=-100),
    ]
    participant_wallets = await get_participant_wallets(
        participants, StaticData.business_name_1, "USD"
    )

    assert len(participant_wallets) == 2
    assert isinstance(participant_wallets[0], ParticipantWallet)
    assert participant_wallets[0].wallet == wallet_1
    assert participant_wallets[0].amount == 100
    assert participant_wallets[0].balance == 500

    assert isinstance(participant_wallets[1], ParticipantWallet)
    assert participant_wallets[1].wallet == wallet_2
    assert participant_wallets[1].amount == -100
    assert participant_wallets[1].balance == 500


@pytest.mark.asyncio
async def test_invalid_proposal_not_balanced(wallet_1: Wallet, wallet_2: Wallet):
    proposal = Proposal(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        issuer_id=StaticData.business_id_1,
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
async def test_invalid_proposal_not_balanced2(wallet_1: Wallet, wallet_2: Wallet):
    proposal = Proposal(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        issuer_id=StaticData.business_id_1,
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
async def test_invalid_proposal_no_participants():
    proposal = Proposal(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        issuer_id=StaticData.business_id_1,
        amount=100,
        currency="USD",
        task_status="init",
        participants=[],
    )

    await process_proposal(proposal)
    assert proposal.task_status == "error"


@pytest.mark.asyncio
async def test_invalid_proposal_draft(wallet_1: Wallet, wallet_2: Wallet):
    proposal = Proposal(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        issuer_id=StaticData.business_id_1,
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
async def test_invalid_proposal_no_amount(wallet_1: Wallet, wallet_2: Wallet):
    proposal = Proposal(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        issuer_id=StaticData.business_id_1,
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
async def test_valid_proposal(wallet_1: Wallet, wallet_2: Wallet):
    proposal = Proposal(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        issuer_id=StaticData.business_id_1,
        amount=100,
        currency="USD",
        task_status="init",
        participants=[
            Participant(wallet_id=wallet_1.uid, amount=100),
            Participant(wallet_id=wallet_2.uid, amount=-100),
        ],
    )

    await process_proposal(proposal)
    assert proposal.task_status == "completed"

    transactions = await wallet_1.get_transactions()
    transactions = [
        TransactionSchema(**transaction.__dict__) for transaction in transactions
    ]

    logging.info(
        "Transactions: \n" + "\n".join(str(transaction) for transaction in transactions)
    )
