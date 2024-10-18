import pytest
import pytest_asyncio
from apps.accounting.models import Wallet

from ..constants import StaticData

# @pytest_asyncio.fixture(scope="module", autouse=True)
# async def setup_business():
#     business = Business(
#         business_id=StaticData.business_id_1,
#         business_name=StaticData.business_name_1,
#         domain=StaticData.business_domain_1,
#         name=StaticData.business_name_1,
#         user_id=StaticData.user_id_1_1,
#     )
#     await business.save()
#     yield business
#     await business.delete()


@pytest.fixture(scope="module")
def setup_wallet():
    async def mock_get_balance(self, currency=None):
        if currency is None:
            return {"USD": 500}

        return {currency: 500 if currency == "USD" else 0}

    original_get_balance = Wallet.get_balance
    Wallet.get_balance = mock_get_balance
    yield
    Wallet.get_balance = original_get_balance


@pytest_asyncio.fixture(scope="module")
async def wallet_1(setup_wallet):
    wallet = Wallet(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_1,
        uid=StaticData.wallet_id_1_1,
    )
    await wallet.save(exclude={"holds"})
    yield wallet
    await wallet.delete()


@pytest_asyncio.fixture(scope="module")
async def wallet_2(setup_wallet):
    wallet = Wallet(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_2,
        uid=StaticData.wallet_id_1_2,
    )
    await wallet.save(exclude={"holds"})
    yield wallet
    await wallet.delete()


@pytest_asyncio.fixture(scope="module")
async def wallet_2_original_balance():
    wallet = Wallet(
        business_name=StaticData.business_name_1,
        user_id=StaticData.user_id_1_2,
        uid=StaticData.wallet_id_1_2,
    )
    await wallet.save(exclude={"holds"})
    yield wallet
    await wallet.delete()


@pytest.fixture
def constants():
    return StaticData()
