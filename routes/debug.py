from flask import Blueprint, jsonify, request

from storage.chain import reset_blockchain_data


debug_bp = Blueprint("debug", __name__)


@debug_bp.post("/debug/reset")
def reset_blockchain_route():
    """
    Debug-only endpoint.

    Default behavior:
    - clears blockchain
    - clears mempool
    - clears balances
    - clears contracts
    - keeps wallets

    Optional JSON body:
    {
        "clear_wallets": true
    }
    """
    data = request.get_json(silent=True) or {}

    clear_wallets = data.get("clear_wallets", False)

    reset_result = reset_blockchain_data(clear_wallets=clear_wallets)

    return jsonify(
        {
            "success": True,
            "message": "Blockchain debug data reset successfully",
            "reset": reset_result,
        }
    ), 200
