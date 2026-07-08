from flask import Blueprint, jsonify

from services.wallet import create_wallet, get_wallet
from storage.chain import load_balances


wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.post("/wallet/create")
def create_wallet_route():
    wallet = create_wallet()

    return jsonify(
        {
            "success": True,
            "message": "Wallet created successfully",
            "wallet": wallet,
        }
    ), 201


@wallet_bp.get("/wallet/<address>/balance")
def get_wallet_balance_route(address: str):
    balances = load_balances()
    wallet = get_wallet(address)

    return jsonify(
        {
            "success": True,
            "address": address,
            "wallet_exists": wallet is not None,
            "balance": balances.get(address, 0),
        }
    ), 200
