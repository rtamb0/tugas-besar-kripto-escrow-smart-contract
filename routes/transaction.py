import uuid

from flask import Blueprint, jsonify, request

from services.blockchain import get_current_timestamp
from services.mempool import add_to_mempool
from services.validator import validate_transaction
from services.wallet import sign_transaction


transaction_bp = Blueprint("transaction", __name__)


@transaction_bp.post("/tx/transfer")
def create_native_transfer_route():
    data = request.get_json() or {}

    sender = data.get("from")
    receiver = data.get("to")
    amount = data.get("amount")
    nonce = data.get("nonce")

    if not sender:
        return jsonify(
            {
                "success": False,
                "message": "Missing from address",
            }
        ), 400

    if not receiver:
        return jsonify(
            {
                "success": False,
                "message": "Missing to address",
            }
        ), 400

    if amount is None:
        return jsonify(
            {
                "success": False,
                "message": "Missing amount",
            }
        ), 400

    if nonce is None:
        return jsonify(
            {
                "success": False,
                "message": "Missing nonce",
            }
        ), 400

    tx = {
        "tx_id": data.get("tx_id", "TX_TRANSFER_" + uuid.uuid4().hex),
        "type": "native_transfer",
        "from": sender,
        "to": receiver,
        "amount": amount,
        "nonce": nonce,
        "timestamp": data.get("timestamp", get_current_timestamp()),
    }

    try:
        signed_tx = sign_transaction(tx, sender)
    except ValueError as error:
        return jsonify(
            {
                "success": False,
                "message": str(error),
            }
        ), 400

    success, message = add_to_mempool(signed_tx)

    status_code = 201 if success else 400

    return jsonify(
        {
            "success": success,
            "message": message,
            "transaction": signed_tx,
        }
    ), status_code


@transaction_bp.post("/verify_tx")
def verify_transaction_route():
    tx = request.get_json() or {}

    valid, message = validate_transaction(tx)

    return jsonify(
        {
            "success": valid,
            "message": message,
            "transaction": tx,
        }
    ), 200 if valid else 400
