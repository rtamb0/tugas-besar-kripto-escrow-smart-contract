from flask import Flask, jsonify

from routes.wallet import wallet_bp
from routes.transaction import transaction_bp
from routes.blockchain import blockchain_bp
from routes.contract import contract_bp
from routes.debug import debug_bp


def create_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(wallet_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(blockchain_bp)
    app.register_blueprint(contract_bp)
    app.register_blueprint(debug_bp)

    @app.get("/")
    def index():
        return jsonify(
            {
                "message": "MiniCrypto Escrow Blockchain API",
                "endpoints": {
                    "wallet": [
                        "POST /wallet/create",
                        "GET /wallet/<address>/balance",
                    ],
                    "transaction": [
                        "POST /tx/transfer",
                        "POST /verify_tx",
                    ],
                    "contract": [
                        "POST /contract/deploy",
                        "POST /contract/call",
                        "GET /contract/<address>",
                        "GET /contract/<address>/orders/<order_id>",
                    ],
                    "blockchain": [
                        "GET /mempool",
                        "POST /mine",
                        "GET /chain",
                        "GET /balances",
                        "GET /verify_chain",
                    ],
                    "debug": [
                        "POST /debug/reset",
                    ],
                },
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
