import logging
import uuid

from apps.accounting.models import Proposal, Transaction, Wallet
from apps.business.models import Business


async def fail_proposal(proposal: Proposal, message: str = None):
    logging.error(f"Error processing proposal {proposal.id} - {message}")
    proposal.status = "error"
    proposal.save()


async def success_proposal(proposal: Proposal, **kwargs):
    ## Let's process the proposal
    # create metadata
    # get django atomic session
    # Create transaction for source wallet
    # Create transaction for each destination wallet
    # Update proposal status to success

    metadata = proposal.metadata or {}
    metadata["proposal_id"] = proposal.id

    source_wallet = kwargs.get("source_wallet")
    source_wallet_balance = kwargs.get("source_wallet_balance")
    recipients: list[Recipient] = kwargs.get("recipients")

    with transaction.atomic():
        source_transaction = Transaction(
            metadata=metadata,
            business_id=proposal.business_id,
            user_id=proposal.user_id,
            wallet=source_wallet,
            amount=-proposal.amount,
            balance=source_wallet_balance - proposal.amount,
            description=proposal.description,
            note=proposal.note,
        )
        source_transaction.save()

        for recipient in recipients:
            recipient_transaction = Transaction(
                metadata=metadata,
                business_id=proposal.business_id,
                user_id=proposal.user_id,
                wallet=recipient.wallet,
                amount=recipient.amount,
                balance=recipient.wallet.balance + recipient.amount,
                description=proposal.description,
                note=proposal.note,
            )
            recipient_transaction.save()
        proposal.status = "success"
        proposal.save()


async def notify_proposal(proposal: Proposal, message: str):
    logging.info(f"Proposal {proposal.id} - {message}")
    return


async def process_proposal(proposal_id: uuid.UUID):
    logging.info(f"Processing proposal {proposal_id}")
    try:
        proposal = Proposal.objects.get(id=proposal_id)
        if not proposal:
            logging.error(f"Proposal {proposal_id} does not exist")
            return

        # Check if the proposal is already processed / Check status
        if proposal.status != "init":
            logging.error(f"Proposal {proposal.id} is already processed")
            return

        # Check if business exists
        business = Business.objects.get(id=proposal.business_id)
        if not business:
            return fail_proposal(
                proposal, f"Business {proposal.business_id} does not exist"
            )

        # Check if the proposal recipients are in valid formats
        if not proposal.recipients:
            return fail_proposal(proposal, "Proposal recipients is empty")
        if type(proposal.recipients) != list:
            return fail_proposal(proposal, "Proposal recipients is not a list")

        recipients: list[Recipient] = []
        for recipient_dict in proposal.recipients:
            recipient = Recipient(**recipient_dict)
            if recipient:
                return fail_proposal(proposal, "Invalid recipient format")
            recipients.append(recipient)

        # Check if the proposal source wallet exists
        source_wallet = Wallet.objects.get(id=proposal.source_id)
        if not source_wallet:
            return fail_proposal(
                proposal, f"Source wallet {proposal.source_id} does not exist"
            )

        # Others check should be atomic

        # Check if the proposal source wallet user_id and business_id are valid
        if source_wallet.business_id != proposal.business_id:
            return fail_proposal(
                proposal,
                f"Business {proposal.business_id} does not have access to source wallet {source_wallet.id}",
            )

        if source_wallet.user_id != proposal.user_id:
            return fail_proposal(
                proposal,
                f"User {proposal.user_id} does not have access to source wallet {source_wallet.id}",
            )

        # Check if the proposal source wallet is active
        if source_wallet.is_deleted:
            return fail_proposal(
                proposal, f"Source wallet {source_wallet.id} is deleted"
            )

        # Check if the proposal destinations wallets are exists and active
        for recipient in recipients:
            destination_wallet = Wallet.objects.get(id=recipient.destination_id)
            if not destination_wallet:
                return fail_proposal(
                    proposal,
                    f"Destination wallet {recipient.destination_id} does not exist",
                )
            if destination_wallet.is_deleted:
                return fail_proposal(
                    proposal,
                    f"Destination wallet {destination_wallet.id} is deleted",
                )
            recipient.wallet = destination_wallet

        # Check if requester has access to source wallet
        if proposal.requester == "user":
            if source_wallet.user_id != proposal.user_id:
                return fail_proposal(
                    proposal,
                    f"User {proposal.user_id} does not have access to source wallet {source_wallet.id}",
                )
        elif proposal.requester == "business":
            if source_wallet.business_id != proposal.business_id:
                return fail_proposal(
                    proposal,
                    f"Business {proposal.business_id} does not have access to source wallet {source_wallet.id}",
                )

        # Check if requester has access to destinations
        for recipient in recipients:
            if recipient.wallet.business_id != proposal.business_id:
                return fail_proposal(
                    proposal,
                    f"The destination wallet {recipient.wallet.id} does not belongs to business {proposal.business_id}.",
                )

        # Check if sent amount equals to sum of all recipient amounts
        total_amount = sum([recipient.amount for recipient in recipients])
        if proposal.amount != total_amount:
            return fail_proposal(
                proposal,
                f"Total amount {total_amount} is not equal to proposal amount {proposal.amount}",
            )

        with transaction.atomic():
            # Check if source wallet has enough balance except the hold amount
            source_wallet_balance = source_wallet.balance
            if source_wallet_balance - source_wallet.hold_amount < proposal.amount:
                return fail_proposal(
                    proposal,
                    f"Insufficient balance in source wallet {source_wallet.id} after hold amount",
                )

            ## Let's process the proposal
            # create metadata
            # get django atomic session
            # Create transaction for source wallet
            # Create transaction for each destination wallet
            # Update proposal status to success

            metadata = proposal.metadata or {}
            metadata["proposal_id"] = proposal.id

            source_transaction = Transaction(
                metadata=metadata,
                business_id=proposal.business_id,
                user_id=proposal.user_id,
                wallet=source_wallet,
                amount=-proposal.amount,
                balance=source_wallet_balance - proposal.amount,
                description=proposal.description,
                note=proposal.note,
            )
            source_transaction.save()

            recipient_transactions = []
            for recipient in recipients:
                recipient_transaction = Transaction(
                    metadata=metadata,
                    business_id=proposal.business_id,
                    user_id=proposal.user_id,
                    wallet=recipient.wallet,
                    amount=recipient.amount,
                    balance=recipient.wallet.balance + recipient.amount,
                    description=proposal.description,
                    note=proposal.note,
                )
                recipient_transaction.save()
                recipient_transactions.append(recipient_transaction)
            proposal.status = "success"
            proposal.save()

        # Send notifications
        # Send notification to source wallet
        # Send notification to all recipients
        # Send notification to requester
        # Send notification to business
        source_wallet.notify(f"Transaction {source_transaction.id} is successful")
        for recipient in recipients:
            recipient.wallet.notify(
                f"Transaction {recipient_transaction.id} is successful"
            )
        if proposal.requester == "business":
            business.notify(f"Proposal {proposal.id} is successful")

        return {
            "source_transaction": source_transaction,
            "recipient_transactions": recipient_transactions,
        }

    except Exception:
        if proposal:
            fail_proposal(proposal)
