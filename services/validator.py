from services.wallet import verify_signature, generate_address
from storage.chain import load_chain, load_mempool, load_balances


VALID_TRANSACTION_TYPES = {
    "native_transfer",
    "contract_deploy",
    "contract_call",
    "coinbase",
}


def get_signer_address(tx: dict) -> str | None:
    """
    Get the address of whoever is supposed to sign the transaction.
    """
    tx_type = tx.get("type")

    if tx_type == "native_transfer":
        return tx.get("from")

    if tx_type == "contract_deploy":
        return tx.get("owner")

    if tx_type == "contract_call":
        return tx.get("caller")

    return None


def is_tx_id_used(tx_id: str) -> bool:
    """
    Check whether tx_id already exists in chain or mempool.
    """
    if not tx_id:
        return False

    mempool = load_mempool()

    for tx in mempool:
        if tx.get("tx_id") == tx_id:
            return True

    chain = load_chain()

    for block in chain:
        for tx in block.get("transactions", []):
            if tx.get("tx_id") == tx_id:
                return True

    return False


def is_nonce_used(address: str, nonce: int) -> bool:
    """
    Check whether this address already used this nonce in chain or mempool.
    """
    if not address:
        return False

    mempool = load_mempool()

    for tx in mempool:
        signer = get_signer_address(tx)
        if signer == address and tx.get("nonce") == nonce:
            return True

    chain = load_chain()

    for block in chain:
        for tx in block.get("transactions", []):
            signer = get_signer_address(tx)
            if signer == address and tx.get("nonce") == nonce:
                return True

    return False


def validate_required_fields(tx: dict) -> tuple[bool, str]:
    tx_type = tx.get("type")

    if not tx.get("tx_id"):
        return False, "Missing tx_id"

    if tx_type not in VALID_TRANSACTION_TYPES:
        return False, "Invalid transaction type"

    if tx_type == "coinbase":
        required_fields = [
            "tx_id",
            "type",
            "to",
            "amount",
            "timestamp",
        ]

    elif tx_type == "native_transfer":
        required_fields = [
            "tx_id",
            "type",
            "from",
            "to",
            "amount",
            "nonce",
            "timestamp",
            "public_key",
            "signature",
        ]

    elif tx_type == "contract_deploy":
        required_fields = [
            "tx_id",
            "type",
            "contract_address",
            "contract_type",
            "owner",
            "nonce",
            "timestamp",
            "public_key",
            "signature",
        ]

    else:
        required_fields = [
            "tx_id",
            "type",
            "contract_address",
            "method",
            "params",
            "caller",
            "nonce",
            "timestamp",
            "public_key",
            "signature",
        ]

    for field in required_fields:
        if field not in tx:
            return False, f"Missing field: {field}"

    return True, "Required fields valid"


def validate_amount(tx: dict) -> tuple[bool, str]:
    tx_type = tx.get("type")

    if tx_type not in ["native_transfer", "coinbase"]:
        return True, "Amount validation skipped"

    amount = tx.get("amount")

    if not isinstance(amount, (int, float)):
        return False, "Amount must be a number"

    if amount <= 0:
        return False, "Amount must be greater than 0"

    return True, "Amount valid"


def validate_balance(tx: dict) -> tuple[bool, str]:
    """
    Only native transfer balance is checked here.

    Escrow-specific balance checks, such as fund_order,
    will be handled by escrow service during mining/execution.
    """
    if tx.get("type") != "native_transfer":
        return True, "Balance validation skipped"

    balances = load_balances()

    sender = tx.get("from")
    amount = tx.get("amount")

    sender_balance = balances.get(sender, 0)

    if sender_balance < amount:
        return False, "Insufficient balance"

    return True, "Balance valid"


def validate_signature(tx: dict) -> tuple[bool, str]:
    """
    Coinbase has no sender signature.
    Other transaction types must have valid signature.
    """
    if tx.get("type") == "coinbase":
        return True, "Coinbase does not require signature"

    public_key = tx.get("public_key")
    signature = tx.get("signature")

    if not public_key or not signature:
        return False, "Missing public_key or signature"

    signer_address = get_signer_address(tx)

    if not signer_address:
        return False, "Missing signer address"

    expected_address = generate_address(public_key)

    if signer_address != expected_address:
        return False, "Signer address does not match public key"

    payload = tx.copy()
    payload.pop("signature", None)
    payload.pop("public_key", None)

    if not verify_signature(payload, public_key, signature):
        return False, "Invalid signature"

    return True, "Signature valid"


def validate_nonce(tx: dict) -> tuple[bool, str]:
    if tx.get("type") == "coinbase":
        return True, "Coinbase does not require nonce"

    nonce = tx.get("nonce")

    if not isinstance(nonce, int):
        return False, "Nonce must be an integer"

    if nonce < 1:
        return False, "Nonce must be greater than 0"

    signer_address = get_signer_address(tx)

    if is_nonce_used(signer_address, nonce):
        return False, "Nonce already used"

    return True, "Nonce valid"


def validate_transaction(tx: dict) -> tuple[bool, str]:
    """
    Main validation function before a transaction enters the mempool.
    """
    if is_tx_id_used(tx.get("tx_id")):
        return False, "tx_id already exists"

    checks = [
        validate_required_fields,
        validate_amount,
        validate_signature,
        validate_nonce,
        validate_balance,
    ]

    for check in checks:
        valid, message = check(tx)

        if not valid:
            return False, message

    return True, "Transaction valid"
