import logging

import httpx
import pytest

from .constants import StaticData

# @pytest.mark.asyncio
# async def test_business_list_empty(client: httpx.AsyncClient, auth_headers_business):
#     # list businesses empty
#     response = await client.get("/api/v1/businesses/", headers=auth_headers_business)

#     resp_json = response.json()
#     logging.info(f"business_list: {resp_json}")
#     assert response.status_code == 200
#     assert type(resp_json.get("items")) == list
#     assert len(resp_json.get("items")) == 0


# @pytest.mark.asyncio
# async def test_business_create(client: httpx.AsyncClient, auth_headers_business):
#     # create business
#     domain = urlparse(str(client.base_url)).netloc
#     data = dict(
#         name=StaticData.business_name_1,
#         domain=domain,
#         uid=str(StaticData.business_id_1),
#     )
#     response = await client.post(
#         "/api/v1/businesses/", headers=auth_headers_business, json=data
#     )

#     resp_json = response.json()
#     assert response.status_code == 201
#     assert resp_json["name"] == data["name"]
#     assert resp_json["domain"] == data["domain"]
#     assert resp_json["uid"] != data["uid"]

base_route = "/api/v1/apps/business/businesses/"


@pytest.mark.asyncio
async def test_business_list_with_business(auth_headers_business):
    # list business
    async with httpx.AsyncClient(
        base_url="https://business.ufaas.io", headers=auth_headers_business
    ) as business_client:
        response = await business_client.get(base_route)
        resp_json = response.json()

    logging.info(f"business_list: {resp_json}")
    assert response.status_code == 200
    assert type(resp_json.get("items")) == list
    assert len(resp_json.get("items")) > 0
    business = resp_json["items"][0]
    business_id = business.get("uid")
    StaticData.business_id_1 = business_id


@pytest.mark.asyncio
async def test_business_retrieve_no_auth():
    # retrieve business without access token
    async with httpx.AsyncClient(
        base_url="https://business.ufaas.io"
    ) as business_client:
        response = await business_client.get(f"{base_route}{StaticData.business_id_1}")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_business_retrieve_not_found(auth_headers_business):
    # retrieve business not found
    async with httpx.AsyncClient(
        base_url="https://business.ufaas.io", headers=auth_headers_business
    ) as business_client:
        response = await business_client.get(f"{base_route}{StaticData.business_id_2}")

        logging.info(f"business_retrieve: {response.json()}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_business_retrieve(auth_headers_business):
    # retrieve business
    async with httpx.AsyncClient(
        base_url="https://business.ufaas.io", headers=auth_headers_business
    ) as business_client:
        response = await business_client.get(f"{base_route}{StaticData.business_id_1}")
        resp_json = response.json()
        assert response.status_code == 200
    logging.info(f"business_retrieve: {resp_json}")
    assert resp_json["uid"] == StaticData.business_id_1


# @pytest.mark.asyncio
# async def test_business_update(client: httpx.AsyncClient, auth_headers_business):
#     # update business
#     data = dict(meta_data={"key": "value"})
#     response = await client.patch(
#         f"/api/v1/businesses/{StaticData.business_id_1}",
#         headers=auth_headers_business,
#         json=data,
#     )

#     resp_json = response.json()
#     logging.info(f"business_update: {resp_json}")
#     assert response.status_code == 200
#     assert resp_json["uid"] == StaticData.business_id_1
#     assert resp_json["meta_data"] == data["meta_data"]

#     # retrieve business after update
#     response = await client.get(
#         f"/api/v1/businesses/{StaticData.business_id_1}", headers=auth_headers_business
#     )
#     resp_json = response.json()
#     logging.info(f"business_retrieve: {resp_json}")
#     assert response.status_code == 200
#     assert resp_json["uid"] == StaticData.business_id_1
#     assert resp_json["meta_data"] == data["meta_data"]
