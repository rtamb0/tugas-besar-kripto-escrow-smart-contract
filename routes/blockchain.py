from flask import Blueprint, jsonify, request

from services.blockchain import verify_chain
from services.mempool import get_mempool
from services.mining import mine_block
from storage.chain import load_chain, load_balances


blockchain_bp = Blueprint("blockchain", __name__)


@blockchain_bp.get("/mempool")
def get_mempool_route():
    return jsonify(
        {
            "success": True,
            "mempool": get_mempool(),
        }
    ), 200


@blockchain_bp.post("/mine")
def mine_block_route():
    data = request.get_json() or {}

    miner_address = data.get("miner_address")

    if not miner_address:
        return jsonify(
            {
                "success": False,
                "message": "Missing miner_address",
            }
        ), 400

    try:
        result = mine_block(miner_address)
    except ValueError as error:
        return jsonify(
            {
                "success": False,
                "message": str(error),
            }
        ), 400

    return jsonify(
        {
            "success": True,
            **result,
        }
    ), 201


@blockchain_bp.get("/chain")
def get_chain_route():
    return jsonify(
        {
            "success": True,
            "chain": load_chain(),
        }
    ), 200


@blockchain_bp.get("/balances")
def get_balances_route():
    return jsonify(
        {
            "success": True,
            "balances": load_balances(),
        }
    ), 200


@blockchain_bp.get("/verify_chain")
def verify_chain_route():
    valid, message = verify_chain()

    return jsonify(
        {
            "success": valid,
            "message": message,
        }
    ), 200 if valid else 400
