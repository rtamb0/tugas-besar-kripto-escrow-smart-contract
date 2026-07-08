import uuid

from flask import Blueprint, jsonify, request

from services.blockchain import get_current_timestamp
from services.escrow import generate_contract_address
from services.mempool import add_to_mempool
from services.wallet import sign_transaction
from storage.chain import load_contracts


contract_bp = Blueprint("contract", __name__)


@contract_bp.post("/contract/deploy")
def deploy_contract_route():
    data = request.get_json() or {}

    owner = data.get("owner")

    if not owner:
        return jsonify(
            {
                "success": False,
                "message": "Missing owner address",
            }
        ), 400

    contract_address = data.get("contract_address", generate_contract_address())

    tx = {
        "tx_id": data.get("tx_id", "TX_DEPLOY_" + uuid.uuid4().hex),
        "type": "contract_deploy",
        "contract_address": contract_address,
        "contract_type": "ESCROW",
        "owner": owner,
        "nonce": data.get("nonce"),
        "timestamp": data.get("timestamp", get_current_timestamp()),
    }

    if tx["nonce"] is None:
        return jsonify(
            {
                "success": False,
                "message": "Missing nonce",
            }
        ), 400

    try:
        signed_tx = sign_transaction(tx, owner)
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
            "contract_address": contract_address,
            "transaction": signed_tx,
        }
    ), status_code


@contract_bp.post("/contract/call")
def call_contract_route():
    data = request.get_json() or {}

    contract_address = data.get("contract_address")
    method = data.get("method")
    params = data.get("params", {})
    caller = data.get("caller")
    nonce = data.get("nonce")

    if not contract_address:
        return jsonify(
            {
                "success": False,
                "message": "Missing contract_address",
            }
        ), 400

    if not method:
        return jsonify(
            {
                "success": False,
                "message": "Missing method",
            }
        ), 400

    if not caller:
        return jsonify(
            {
                "success": False,
                "message": "Missing caller",
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
        "tx_id": data.get("tx_id", "TX_CALL_" + uuid.uuid4().hex),
        "type": "contract_call",
        "contract_address": contract_address,
        "method": method,
        "params": params,
        "caller": caller,
        "nonce": nonce,
        "timestamp": data.get("timestamp", get_current_timestamp()),
    }

    try:
        signed_tx = sign_transaction(tx, caller)
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


@contract_bp.get("/contract/<contract_address>")
def get_contract_route(contract_address: str):
    contracts = load_contracts()
    contract = contracts.get(contract_address)

    if not contract:
        return jsonify(
            {
                "success": False,
                "message": "Contract not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "contract": contract,
        }
    ), 200


@contract_bp.get("/contract/<contract_address>/orders/<order_id>")
def get_contract_order_route(contract_address: str, order_id: str):
    contracts = load_contracts()
    contract = contracts.get(contract_address)

    if not contract:
        return jsonify(
            {
                "success": False,
                "message": "Contract not found",
            }
        ), 404

    order = contract.get("orders", {}).get(order_id)

    if not order:
        return jsonify(
            {
                "success": False,
                "message": "Order not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "order": order,
        }
    ), 200
