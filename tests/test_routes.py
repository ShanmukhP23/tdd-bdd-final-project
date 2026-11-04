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

"""Product API Service Test Suite."""

import os
import logging
from decimal import Decimal
from urllib.parse import quote_plus
from unittest import TestCase

from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(
                BASE_URL, json=test_product.serialize()
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test product",
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["message"], "OK")

    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        response = self.client.post(
            BASE_URL, json=test_product.serialize()
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        location = response.headers.get("Location")
        self.assertIsNotNone(location)

        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(
            BASE_URL, data={}, content_type="plain/text"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------

    def test_get_product(self):
        """It should Read a Product"""
        product = self._create_products()[0]

        response = self.client.get(f"{BASE_URL}/{product.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(Decimal(data["price"]), product.price)
        self.assertEqual(data["available"], product.available)
        self.assertEqual(data["category"], product.category.name)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------

    def test_update_product(self):
        """It should Update a Product"""
        product = self._create_products()[0]
        product.description = "Updated product description"

        response = self.client.put(
            f"{BASE_URL}/{product.id}",
            json=product.serialize(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(
            data["description"], "Updated product description"
        )

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------

    def test_delete_product(self):
        """It should Delete a Product"""
        product = self._create_products()[0]

        response = self.client.delete(f"{BASE_URL}/{product.id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------
    # TEST LIST ALL
    # ----------------------------------------------------------

    def test_get_products(self):
        """It should List all Products"""
        self._create_products(5)

        response = self.client.get(BASE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    # ----------------------------------------------------------
    # TEST QUERY BY NAME
    # ----------------------------------------------------------

    def test_query_product_by_name(self):
        """It should Query Products by Name"""
        products = self._create_products(5)
        name = products[0].name

        response = self.client.get(
            f"{BASE_URL}?name={quote_plus(name)}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)
        self.assertTrue(all(item["name"] == name for item in data))

    # ----------------------------------------------------------
    # TEST QUERY BY CATEGORY
    # ----------------------------------------------------------

    def test_query_product_by_category(self):
        """It should Query Products by Category"""
        products = self._create_products(5)
        category = products[0].category.name

        response = self.client.get(
            f"{BASE_URL}?category={category}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)
        self.assertTrue(
            all(item["category"] == category for item in data)
        )

    # ----------------------------------------------------------
    # TEST QUERY BY AVAILABILITY
    # ----------------------------------------------------------

    def test_query_product_by_availability(self):
        """It should Query Products by Availability"""
        products = self._create_products(5)
        available = str(products[0].available).lower()

        response = self.client.get(
            f"{BASE_URL}?available={available}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)
        self.assertTrue(
            all(item["available"] == (available == "true") for item in data)
        )

    # ----------------------------------------------------------
    # TEST INVALID FILTERS AND MISSING PRODUCTS
    # ----------------------------------------------------------

    def test_query_invalid_category(self):
        """It should reject an invalid category."""
        response = self.client.get(f"{BASE_URL}?category=INVALID")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_invalid_availability(self):
        """It should reject an invalid availability value."""
        response = self.client.get(f"{BASE_URL}?available=sometimes")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_missing_product(self):
        """It should return 404 for a missing product."""
        response = self.client.get(f"{BASE_URL}/999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_missing_product(self):
        """It should return 404 when updating a missing product."""
        response = self.client.put(
            f"{BASE_URL}/999999",
            json={
                "name": "Missing",
                "description": "Not here",
                "price": "10.00",
                "available": True,
                "category": "TOOLS",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_missing_product(self):
        """It should return 404 when deleting a missing product."""
        response = self.client.delete(f"{BASE_URL}/999999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def get_product_count(self):
        """Save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        return len(data)
