import logging
from urllib.parse import urlparse

import httpx
import pytest

from .constants import StaticData


@pytest.mark.asyncio
async def test_business_create(client: httpx.AsyncClient, db, access_token):
    domain = urlparse(str(client.base_url)).netloc
    data = dict(
        name=StaticData.business_name_1,
        domain=domain,
        uid=str(StaticData.business_id_1),
    )
    response = await client.post(
        "/api/v1/businesses/",
        json=data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    logging.info(response.json())
    assert response.status_code == 201
    # assert response.json() == {"message": "Unauthorized", "error": "unauthorized"}
    resp_json = response.json()
    assert resp_json["name"] == data["name"]
    assert resp_json["domain"] == data["domain"]
    assert resp_json["uid"] != data["uid"]
