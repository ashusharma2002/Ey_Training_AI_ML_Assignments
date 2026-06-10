import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

ORDER_PAYLOAD = {
    "customer": {
        "name": "Aarav Sharma",
        "email": "aarav@example.com",
        "phone": "+919876543210",
        "shipping_address": {
            "street": "42 MG Road",
            "city": "Dehradun",
            "state": "Uttarakhand",
            "pincode": "248001",
            "country": "India"
        }
    },
    "items": [
        {
            "product": {
                "name": "Wireless Headphones",
                "price": 2999.00,
                "sku": "WH-001"
            },
            "quantity": 2,
            "discount": 10.0
        }
    ],
    "payment_method": "upi",
    "notes": "Leave at gate"
}


def test_health():

    r = client.get("/")

    assert r.status_code == 200


def test_create_order():

    r = client.post(
        "/orders/",
        json=ORDER_PAYLOAD
    )

    assert r.status_code == 201

    data = r.json()

    assert "summary" in data


def test_get_order():

    create_r = client.post(
        "/orders/",
        json=ORDER_PAYLOAD
    )

    order_id = create_r.json()["id"]

    r = client.get(f"/orders/{order_id}")

    assert r.status_code == 200


def test_update_order_status():

    create_r = client.post(
        "/orders/",
        json=ORDER_PAYLOAD
    )

    order_id = create_r.json()["id"]

    r = client.patch(
        f"/orders/{order_id}/status?new_status=confirmed"
    )

    assert r.status_code == 200

    assert r.json()["status"] == "confirmed"


def test_delete_order():

    create_r = client.post(
        "/orders/",
        json=ORDER_PAYLOAD
    )

    order_id = create_r.json()["id"]

    del_r = client.delete(f"/orders/{order_id}")

    assert del_r.status_code == 204


def test_filter_orders():

    r = client.get("/orders/?status=confirmed")

    assert r.status_code == 200


def test_pagination():

    r = client.get("/orders/?skip=0&limit=5")

    assert r.status_code == 200


def test_sorting():

    r = client.get("/orders/?sort_by=grand_total")

    assert r.status_code == 200


def test_invalid_pincode():

    bad_payload = {
        **ORDER_PAYLOAD,
        "customer": {
            **ORDER_PAYLOAD["customer"],
            "shipping_address": {
                **ORDER_PAYLOAD["customer"]["shipping_address"],
                "pincode": "12AB"
            }
        }
    }

    r = client.post(
        "/orders/",
        json=bad_payload
    )

    assert r.status_code == 422