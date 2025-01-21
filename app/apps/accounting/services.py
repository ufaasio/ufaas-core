import asyncio
import logging
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from ufaas_fastapi_business.models import Business

from apps.accounting.models import (
    Participant,
    Proposal,
    Transaction,
    TransactionNote,
    Wallet,
)
from server.db import async_session


class ParticipantWallet(BaseModel):
    amount: Decimal
    wallet: Wallet
    balance: Decimal

    model_config = ConfigDict(allow_inf_nan=True)


async def participant_validator(
    participant_wallet: ParticipantWallet, business: Business
):
    return True


async def fail_proposal(proposal: Proposal, message: str = None, **kwargs):
    message_str = "\n".join([message] + [f"{k}: {v}" for k, v in kwargs.items()])
    logging.warning(f"Error processing proposal {proposal.uid} - {message_str}")
    proposal.task_status = "error"
    await proposal.save_report(message, emit=False)
    await proposal.save_and_emit()


async def success_proposal(
    business: Business,
    proposal: Proposal,
    participants_wallets: list[ParticipantWallet],
    session: AsyncSession,
    **kwargs,
):
    async with session.begin():
        meta_data = proposal.meta_data or {}
        balances = {}

        for participant in participants_wallets:
            new_balance = (
                balances.get(participant.wallet.id) or participant.balance
            ) + participant.amount
            transaction = Transaction(
                business_name=proposal.business_name,
                user_id=participant.wallet.user_id,
                meta_data=meta_data,
                proposal_id=proposal.uid,
                wallet_id=participant.wallet.uid,
                amount=participant.amount,
                currency=proposal.currency,
                balance=new_balance,
                description=proposal.description,
                # note=proposal.note,
            )
            balances[participant.wallet.id] = new_balance
            session.add(transaction)

    if proposal.note:
        for transaction in await proposal.get_transactions():
            note = TransactionNote(
                business_name=proposal.business_name,
                user_id=participant.wallet.user_id,
                transaction_id=transaction.uid,
                note=proposal.note,
            )
            await note.save()
    proposal.task_status = "completed"
    await proposal.save_report("Proposal processed successfully", emit=False)
    await proposal.save()


# New Functions for Separation of Concerns
async def get_participant_wallets(
    participants: list[Participant], business_name: str, currency: str = "IRR"
) -> list[ParticipantWallet]:
    async def get_participant_wallet(participant: Participant):
        wallet: Wallet = await Wallet.get_item(
            participant.wallet_id, business_name=business_name, user_id=None
        )
        balance = (await wallet.get_balance(currency)).get(currency, 0)
        return ParticipantWallet(
            wallet=wallet, amount=participant.amount, balance=balance
        )

    return await asyncio.gather(
        *[get_participant_wallet(participant) for participant in participants]
    )


async def validate_proposal(proposal: Proposal):
    if proposal.task_status != "init":
        raise ValueError(f"Proposal {proposal.id} is already processed")
    if not proposal.participants:
        raise ValueError("Proposal participants are empty")


async def validate_wallets(
    proposal: Proposal,
    participants: list[ParticipantWallet],
):
    for participant in participants:
        if participant.wallet.business_name != proposal.business_name:
            raise ValueError(
                f"Business {proposal.business_name} does not have access to source wallet {participant.wallet.id}"
            )
        if participant.wallet.is_deleted:
            raise ValueError(f"Source wallet {participant.wallet.id} is deleted")


async def validate_amounts(
    proposal: Proposal,
    participants: list[ParticipantWallet],
):
    received_amount = sum(
        [participant.amount for participant in participants if participant.amount > 0]
    )
    total_amount = sum([participant.amount for participant in participants])
    logging.info(
        f"Received amount: {received_amount}, Total amount: {total_amount}, Proposal amount: {proposal.amount}"
    )
    if received_amount != proposal.amount:
        raise ValueError(
            f"Transferred amount {received_amount} is not equal to proposal amount {proposal.amount}"
        )
    if total_amount != 0:
        raise ValueError(f"The sent and received amounts are not equal")


async def validate_participants(
    proposal: Proposal, participants: list[ParticipantWallet], business: Business
):
    for participant in participants:
        if not await participant_validator(participant, business):
            return await fail_proposal(
                proposal,
                f"Participant {participant.wallet.id} is not valid",
            )


async def check_balances(sources: list[ParticipantWallet], currency: str):
    for source in sources:
        held_amount = await source.wallet.get_held_amount(currency)
        if source.balance - held_amount < -source.amount:
            raise ValueError(
                f"Insufficient balance in source wallet {source.wallet.id}"
            )


async def process_proposal(proposal: Proposal):
    logging.info(f"Processing proposal {proposal.uid}")
    async with async_session() as session:
        try:
            await validate_proposal(proposal)
            proposal.task_status = "processing"
            await proposal.save()

            business = await Business.get_by_name(proposal.business_name)
            if not business:
                raise ValueError(f"Business {proposal.business_name} does not exist")

            participants_wallets = await get_participant_wallets(
                proposal.participants, proposal.business_name, proposal.currency
            )
            sources = [
                participant
                for participant in participants_wallets
                if participant.amount < 0
            ]
            recipients = [
                participant
                for participant in participants_wallets
                if participant.amount > 0
            ]

            await validate_wallets(proposal, participants_wallets)
            await validate_amounts(proposal, participants_wallets)
            await check_balances(sources, proposal.currency)
            await validate_participants(proposal, participants_wallets, business)

            await success_proposal(business, proposal, participants_wallets, session)

        except Exception as e:
            import traceback

            traceback_str = "".join(traceback.format_tb(e.__traceback__))

            await session.rollback()
            await fail_proposal(proposal, str(e), traceback=traceback_str)
