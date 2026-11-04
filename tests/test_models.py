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

"""Test cases for Product Model."""

import os
import logging
import unittest
from decimal import Decimal

from service.models import Product, Category, DataValidationError, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """Runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(
            name="Fedora",
            description="A red hat",
            price=12.50,
            available=True,
            category=Category.CLOTHS,
        )
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertIsNotNone(product)
        self.assertIsNone(product.id)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertTrue(product.available)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        self.assertEqual(Product.all(), [])

        product = ProductFactory()
        product.create()

        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)

        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.create()

        found_product = Product.find(product.id)

        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.create()

        product.description = "Updated description"
        product.update()

        found_product = Product.find(product.id)
        self.assertEqual(found_product.description, "Updated description")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()

        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products"""
        self.assertEqual(len(Product.all()), 0)

        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        self.assertEqual(len(Product.all()), 5)

    def test_find_by_name(self):
        """It should Find Products by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        name = products[0].name
        matching = [p for p in products if p.name == name]
        found = list(Product.find_by_name(name))

        self.assertEqual(len(found), len(matching))
        self.assertTrue(all(p.name == name for p in found))

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()

        available = products[0].available
        matching = [p for p in products if p.available == available]
        found = list(Product.find_by_availability(available))

        self.assertEqual(len(found), len(matching))
        self.assertTrue(all(p.available == available for p in found))

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()

        category = products[0].category
        matching = [p for p in products if p.category == category]
        found = list(Product.find_by_category(category))

        self.assertEqual(len(found), len(matching))
        self.assertTrue(all(p.category == category for p in found))

    def test_update_without_id(self):
        """It should reject updating a product without an ID."""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.update()

    def test_deserialize_invalid_available(self):
        """It should reject a non-boolean availability value."""
        product = Product()
        data = {
            "name": "Hammer",
            "description": "Claw hammer",
            "price": "20.00",
            "available": "true",
            "category": "TOOLS",
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_missing_field(self):
        """It should reject product data with a missing field."""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({})

    def test_find_by_price(self):
        """It should Find Products by Price."""
        product = ProductFactory(price=Decimal("25.50"))
        product.create()

        found_decimal = list(Product.find_by_price(Decimal("25.50")))
        found_string = list(Product.find_by_price('"25.50"'))

        self.assertEqual(len(found_decimal), 1)
        self.assertEqual(len(found_string), 1)
        self.assertEqual(found_decimal[0].id, product.id)
        self.assertEqual(found_string[0].id, product.id)
