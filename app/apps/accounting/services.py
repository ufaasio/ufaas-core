import asyncio
import logging
from decimal import Decimal

from apps.accounting.models import Participant, Proposal, Transaction, Wallet
from apps.business_mongo.models import Business
from pydantic import BaseModel
from server.db import async_session
from sqlalchemy.ext.asyncio import AsyncSession


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
        ## Let's process the proposal
        # create meta_data
        # get django atomic session
        # Create transaction for source wallet
        # Create transaction for each destination wallet
        # Update proposal status to success

        meta_data = proposal.meta_data or {}

        for participant in participants_wallets:
            if not await participant_validator(participant, business):
                return fail_proposal(
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


async def process_proposal(proposal: Proposal):
    logging.info(f"Processing proposal {proposal.uid}")
    async with async_session() as session:
        try:
            # Check if the proposal is already processed / Check status
            if proposal.task_status != "init":
                logging.error(f"Proposal {proposal.id} is already processed")
                return

            proposal.task_status = "processing"
            await proposal.save()

            # Check if business exists
            business = await Business.get_by_name(proposal.business_name)
            if not business:
                return fail_proposal(
                    proposal, f"Business {proposal.business_name} does not exist"
                )

            # Check if the proposal recipients are in valid formats
            if not proposal.participants:
                return fail_proposal(proposal, "Proposal participants is empty")
            if type(proposal.participants) != list:
                return fail_proposal(proposal, "Proposal participants is not a list")

            async def get_participant_wallets(participants: list[Participant]):
                async def get_participant_wallet(participant: Participant):
                    wallet: Wallet = await Wallet.get_item(
                        participant.wallet_id, business.name
                    )
                    return ParticipantWallet(
                        wallet=wallet,
                        amount=participant.amount,
                        balance=await wallet.get_balance(proposal.currency),
                    )

                return await asyncio.gather(
                    *[
                        get_participant_wallet(participant)
                        for participant in participants
                    ]
                )

            participants_wallets = await get_participant_wallets(proposal.participants)
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

            # Others check should be atomic

            # Check if the proposal source wallets are exists and active
            for source in sources:
                if source.wallet.business_name != proposal.business_name:
                    return fail_proposal(
                        proposal,
                        f"Business {proposal.business_name} does not have access to source wallet {source.wallet.id}",
                    )

                # Check if the proposal source wallet is active
                if source.wallet.is_deleted:
                    return fail_proposal(
                        proposal, f"Source wallet {source.wallet.id} is deleted"
                    )

            # Check if the proposal destinations wallets are exists and active
            for recipient in recipients:
                if recipient.wallet.business_name != proposal.business_name:
                    return fail_proposal(
                        proposal,
                        f"The destination wallet {recipient.wallet.id} does not belongs to business {proposal.business_name}.",
                    )
                if recipient.wallet.is_deleted:
                    return fail_proposal(
                        proposal,
                        f"Destination wallet {recipient.wallet.id} is deleted",
                    )

            # Check if requester has access to source wallet

            # Check if sent amount equals to sum of all recipient amounts
            source_amount = sum([source.amount for source in sources])
            recipient_amount = sum([recipient.amount for recipient in recipients])
            if -source_amount != recipient_amount:
                return fail_proposal(
                    proposal,
                    f"Total amount {source_amount} is not equal to proposal amount {recipient_amount}",
                )
            if proposal.amount != recipient_amount:
                return fail_proposal(
                    proposal,
                    f"Total amount {recipient_amount} is not equal to proposal amount {proposal.amount}",
                )

            # Check if source wallet has enough balance except the hold amount
            # todo: parallelize this
            for source in sources:
                held_amount = await source.wallet.get_held_amount(proposal.currency)
                if source.balance - held_amount < source.amount:
                    return fail_proposal(
                        proposal,
                        f"Insufficient balance in source wallet {source.wallet.id}",
                    )

            await success_proposal(
                business=business,
                proposal=proposal,
                participants_wallets=participants_wallets,
                session=session,
            )

        except Exception as e:
            await session.rollback()
            logging.error(f"Error processing proposal {proposal.uid} - {e}")
            if proposal:
                fail_proposal(proposal, str(e))
