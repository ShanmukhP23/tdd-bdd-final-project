######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""Product Steps."""

import requests
from behave import given

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204


@given('the following products')
def step_impl(context):
    """Delete all Products and load new ones."""
    rest_endpoint = f"{context.base_url}/products"

    context.resp = requests.get(rest_endpoint)
    assert context.resp.status_code == HTTP_200_OK

    for product in context.resp.json():
        context.resp = requests.delete(
            f"{rest_endpoint}/{product['id']}"
        )
        assert context.resp.status_code == HTTP_204_NO_CONTENT

    for row in context.table:
        product = {
            "name": row["name"],
            "description": row["description"],
            "price": row["price"],
            "available": row["available"].lower() == "true",
            "category": row["category"],
        }

        context.resp = requests.post(
            rest_endpoint,
            json=product,
        )
        assert context.resp.status_code == HTTP_201_CREATED
