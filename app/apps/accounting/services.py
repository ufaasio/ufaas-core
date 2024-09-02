import asyncio
import logging
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.accounting.models import Participant, Proposal, Transaction, Wallet
from apps.business_mongo.models import Business
from server.db import async_session


class ParticipantWallet(BaseModel):
    amount: Decimal
    wallet: Wallet
    balance: Decimal


async def participant_validator(
    participant_wallet: ParticipantWallet, business: Business
):
    return True


async def fail_proposal(proposal: Proposal, message: str = None):
    logging.error(f"Error processing proposal {proposal.id} - {message}")
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

        for participant in participants_wallets:
            if not await participant_validator(participant, business):
                return await fail_proposal(
                    proposal,
                    f"Participant {participant.wallet.id} is not valid",
                )

            transaction = Transaction(
                business_name=proposal.business_name,
                user_id=participant.wallet.user_id,
                meta_data=meta_data,
                proposal_id=proposal.uid,
                wallet_id=participant.wallet.uid,
                amount=participant.amount,
                currency=proposal.currency,
                balance=participant.balance + participant.amount,
                description=proposal.description,
                # note=proposal.note,
            )
            session.add(transaction)
        proposal.task_status = "completed"
        await proposal.save_report("Proposal processed successfully", emit=False)
        await proposal.save()


async def notify_proposal(proposal: Proposal, message: str):
    logging.info(f"Proposal {proposal.id} - {message}")
    return


# New Functions for Separation of Concerns
async def get_participant_wallets(
    participants: list[Participant], business_name: str, currency: str = "IRR"
) -> list[ParticipantWallet]:
    async def get_participant_wallet(participant: Participant):
        wallet: Wallet = await Wallet.get_item(
            participant.wallet_id, business_name=business_name, user_id=None
        )
        balance = await wallet.get_balance(currency)
        print(f"Balance type: {type(balance)}, value: {balance}")
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
    if not isinstance(proposal.participants, list):
        raise ValueError("Proposal participants are not a list")


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
    if received_amount != proposal.amount:
        raise ValueError(
            f"Total amount {total_amount} is not equal to proposal amount {proposal.amount}"
        )
    if total_amount != 0:
        raise ValueError(f"The sent and received amounts are not equal")


async def check_balances(sources: list[ParticipantWallet], currency: str):
    for source in sources:
        held_amount = await source.wallet.get_held_amount(currency)
        if source.balance - held_amount < source.amount:
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

            await success_proposal(business, proposal, participants_wallets, session)

        except Exception as e:
            await session.rollback()
            logging.error(f"Error processing proposal {proposal.uid} - {e}")
            await fail_proposal(proposal, str(e))
