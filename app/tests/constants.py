import os
import uuid

import dotenv
from singleton import Singleton

dotenv.load_dotenv()


class StaticData(metaclass=Singleton):
    business_name_1 = "business_1"
    business_id_1 = uuid.UUID("00000000-0000-0000-0001-000000000000")

    business_name_2 = "business_2"
    business_id_2 = uuid.UUID("00000000-0000-0000-0002-000000000000")

    user_id_1_1 = uuid.UUID("00000001-0000-0000-0001-000000000001")
    user_id_1_2 = uuid.UUID("00000001-0000-0000-0001-000000000002")
    user_id_2_1 = uuid.UUID("00000001-0000-0000-0002-000000000001")
    user_id_2_2 = uuid.UUID("00000001-0000-0000-0002-000000000002")
    wallet_id_1_1 = uuid.UUID("00000002-0000-0000-0001-000000000001")
    wallet_id_1_2 = uuid.UUID("00000002-0000-0000-0001-000000000002")
    wallet_id_2_1 = uuid.UUID("00000002-0000-0000-0002-000000000001")
    wallet_id_2_2 = uuid.UUID("00000002-0000-0000-0002-000000000002")

    refresh_token = os.getenv("USSO_REFRESH_TOKEN")
