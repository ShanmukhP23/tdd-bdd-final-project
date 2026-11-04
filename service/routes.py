######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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

"""Product Store Service with UI."""

from flask import jsonify, request, abort
from flask import url_for
from service.models import Product, Category
from service.common import status
from . import app


######################################################################
# HEALTH CHECK
######################################################################

@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating."""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# HOME PAGE
######################################################################

@app.route("/")
def index():
    """Base URL for our service."""
    return app.send_static_file("index.html")


######################################################################
# UTILITY FUNCTIONS
######################################################################

def check_content_type(content_type):
    """Checks that the media type is correct."""
    if "Content-Type" not in request.headers:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# CREATE A NEW PRODUCT
######################################################################

@app.route("/products", methods=["POST"])
def create_products():
    """Creates a Product."""
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)

    product = Product()
    product.deserialize(data)
    product.create()

    message = product.serialize()
    location_url = url_for(
        "get_products", product_id=product.id, _external=True
    )

    return jsonify(message), status.HTTP_201_CREATED, {
        "Location": location_url
    }


######################################################################
# LIST ALL PRODUCTS
######################################################################

@app.route("/products", methods=["GET"])
def list_products():
    """Returns all Products, optionally filtered by query parameters."""
    products = Product.all()

    name = request.args.get("name")
    category = request.args.get("category")
    available = request.args.get("available")

    if name:
        products = Product.find_by_name(name)

    if category:
        try:
            category_enum = Category[category.upper()]
        except KeyError:
            abort(status.HTTP_400_BAD_REQUEST, "Invalid category")
        products = Product.find_by_category(category_enum)

    if available is not None:
        if available.lower() not in ["true", "false"]:
            abort(status.HTTP_400_BAD_REQUEST, "Invalid availability")
        products = Product.find_by_availability(
            available.lower() == "true"
        )

    return jsonify([product.serialize() for product in products]), status.HTTP_200_OK


######################################################################
# READ A PRODUCT
######################################################################

@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """Reads a single Product."""
    app.logger.info("Request to Read product with id: %s", product_id)

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, "Product not found")

    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE A PRODUCT
######################################################################

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_products(product_id):
    """Updates an existing Product."""
    app.logger.info("Request to Update product with id: %s", product_id)
    check_content_type("application/json")

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, "Product not found")

    data = request.get_json()
    product.deserialize(data)
    product.update()

    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# DELETE A PRODUCT
######################################################################

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_products(product_id):
    """Deletes a Product."""
    app.logger.info("Request to Delete product with id: %s", product_id)

    product = Product.find(product_id)
    if not product:
        abort(status.HTTP_404_NOT_FOUND, "Product not found")

    product.delete()
    return "", status.HTTP_204_NO_CONTENT
