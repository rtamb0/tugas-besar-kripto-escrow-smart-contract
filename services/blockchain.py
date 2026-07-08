import hashlib
import json
from copy import deepcopy
from datetime import datetime

from services.wallet import verify_signature, generate_address
from storage.chain import load_chain


DIFFICULTY = 2


def get_current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def calculate_block_hash(block: dict) -> str:
    """
    Calculate block hash.

    block_hash itself must not be included when recalculating the hash.
    """
    block_copy = deepcopy(block)
    block_copy.pop("block_hash", None)

    block_string = canonical_json(block_copy)
    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()


def create_genesis_block() -> dict:
    """
    Create the first block in the blockchain.
    """
    from storage.chain import save_chain

    chain = load_chain()

    if len(chain) > 0:
        return chain[0]

    genesis_block = {
        "height": 0,
        "timestamp": get_current_timestamp(),
        "transactions": [],
        "prev_hash": "0",
        "nonce": 0,
        "difficulty": DIFFICULTY,
    }

    while True:
        block_hash = calculate_block_hash(genesis_block)

        if block_hash.startswith("0" * DIFFICULTY):
            genesis_block["block_hash"] = block_hash
            break

        genesis_block["nonce"] += 1

    save_chain([genesis_block])

    return genesis_block


def validate_transaction_signature(tx: dict) -> tuple[bool, str]:
    """
    Validate signature for non-coinbase transactions.
    """
    if tx.get("type") == "coinbase":
        return True, "Coinbase does not need signature"

    public_key = tx.get("public_key")
    signature = tx.get("signature")

    if not public_key or not signature:
        return False, "Missing public_key or signature"

    tx_type = tx.get("type")

    if tx_type == "native_transfer":
        signer_address = tx.get("from")
    elif tx_type == "contract_deploy":
        signer_address = tx.get("owner")
    elif tx_type == "contract_call":
        signer_address = tx.get("caller")
    else:
        return False, "Invalid transaction type"

    expected_address = generate_address(public_key)

    if signer_address != expected_address:
        return False, "Signer address does not match public key"

    payload = tx.copy()
    payload.pop("signature", None)
    payload.pop("public_key", None)

    if not verify_signature(payload, public_key, signature):
        return False, "Invalid signature"

    return True, "Signature valid"


def execute_transaction(
    tx: dict,
    balances: dict,
    contracts: dict | None = None,
) -> tuple[bool, str]:
    """
    Execute one transaction and mutate temporary state.

    Supports:
    - coinbase
    - native_transfer
    - contract_deploy
    - contract_call
    """
    from services.escrow import deploy_escrow_contract, execute_escrow_contract_call

    if contracts is None:
        contracts = {}

    tx_type = tx.get("type")

    if tx_type == "coinbase":
        receiver = tx.get("to")
        amount = tx.get("amount", 0)

        if not receiver:
            return False, "Coinbase missing receiver"

        if amount <= 0:
            return False, "Coinbase amount must be greater than 0"

        balances[receiver] = balances.get(receiver, 0) + amount
        return True, "Coinbase executed"

    if tx_type == "native_transfer":
        valid_signature, signature_message = validate_transaction_signature(tx)

        if not valid_signature:
            return False, signature_message

        sender = tx.get("from")
        receiver = tx.get("to")
        amount = tx.get("amount")

        if not sender or not receiver:
            return False, "Missing sender or receiver"

        if not isinstance(amount, (int, float)):
            return False, "Amount must be a number"

        if amount <= 0:
            return False, "Amount must be greater than 0"

        if balances.get(sender, 0) < amount:
            return False, "Insufficient balance during mining"

        balances[sender] = balances.get(sender, 0) - amount
        balances[receiver] = balances.get(receiver, 0) + amount

        return True, "Native transfer executed"

    if tx_type == "contract_deploy":
        valid_signature, signature_message = validate_transaction_signature(tx)

        if not valid_signature:
            return False, signature_message

        success, message, _contract = deploy_escrow_contract(tx, contracts)

        if not success:
            return False, message

        return True, message

    if tx_type == "contract_call":
        valid_signature, signature_message = validate_transaction_signature(tx)

        if not valid_signature:
            return False, signature_message

        success, message = execute_escrow_contract_call(
            tx,
            balances,
            contracts,
        )

        if not success:
            return False, message

        return True, message

    return False, "Invalid transaction type"


def verify_chain() -> tuple[bool, str]:
    """
    Verify blockchain integrity.

    Checks:
    - block hash
    - previous hash link
    - Proof-of-Work
    - duplicate tx_id
    - duplicate nonce
    - transaction signatures
    - replay balances and contract state
    """
    chain = load_chain()

    if len(chain) == 0:
        return True, "Chain is empty"

    used_tx_ids = set()
    used_nonces = set()
    replay_balances = {}
    replay_contracts = {}

    for index, block in enumerate(chain):
        stored_hash = block.get("block_hash")
        recalculated_hash = calculate_block_hash(block)

        if stored_hash != recalculated_hash:
            return False, f"Invalid block hash at height {block.get('height')}"

        difficulty = block.get("difficulty", DIFFICULTY)

        if not stored_hash.startswith("0" * difficulty):
            return False, f"Invalid Proof-of-Work at height {block.get('height')}"

        if index == 0:
            if block.get("height") != 0:
                return False, "Invalid genesis block height"

            if block.get("prev_hash") != "0":
                return False, "Invalid genesis previous hash"
        else:
            previous_block = chain[index - 1]

            if block.get("prev_hash") != previous_block.get("block_hash"):
                return False, f"Invalid prev_hash at height {block.get('height')}"

        for tx in block.get("transactions", []):
            tx_id = tx.get("tx_id")

            if not tx_id:
                return False, "Transaction missing tx_id"

            if tx_id in used_tx_ids:
                return False, f"Duplicate tx_id found: {tx_id}"

            used_tx_ids.add(tx_id)

            if tx.get("type") != "coinbase":
                valid_signature, signature_message = validate_transaction_signature(tx)

                if not valid_signature:
                    return False, f"{signature_message} in tx {tx_id}"

                signer = tx.get("from") or tx.get("owner") or tx.get("caller")
                nonce = tx.get("nonce")

                nonce_key = f"{signer}:{nonce}"

                if nonce_key in used_nonces:
                    return False, f"Replay nonce detected in tx {tx_id}"

                used_nonces.add(nonce_key)

            success, message = execute_transaction(
                tx,
                replay_balances,
                replay_contracts,
            )

            if not success:
                return False, f"{message} in tx {tx_id}"

    return True, "Chain is valid"
