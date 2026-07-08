import hashlib
import json
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError

from models.wallet import Wallet
from storage.chain import load_wallets, save_wallets


def canonical_json(data: dict) -> str:
    """
    Converts dictionary into consistent JSON string.
    Important for signing and verifying.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def generate_address(public_key: str) -> str:
    """
    Address format required by the assignment:
    ADDR_ + SHA256(public_key)[0:40]
    """
    public_key_hash = hashlib.sha256(public_key.encode()).hexdigest()
    return "ADDR_" + public_key_hash[:40]


def create_wallet() -> dict:
    """
    Create ECDSA private/public key pair and save it locally.
    """
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()

    private_key_hex = private_key.to_string().hex()
    public_key_hex = public_key.to_string().hex()

    address = generate_address(public_key_hex)

    wallet = Wallet(
        address=address,
        public_key=public_key_hex,
        private_key=private_key_hex,
    )

    wallets = load_wallets()
    wallets[address] = wallet.to_dict()
    save_wallets(wallets)

    return wallet.to_dict()


def get_wallet(address: str) -> dict | None:
    wallets = load_wallets()
    return wallets.get(address)


def sign_payload(payload: dict, private_key_hex: str) -> str:
    """
    Sign transaction payload using private key.
    The signature is returned as a hex string.
    """
    private_key = SigningKey.from_string(
        bytes.fromhex(private_key_hex),
        curve=SECP256k1,
    )

    payload_string = canonical_json(payload)

    signature = private_key.sign_deterministic(payload_string.encode("utf-8"))

    return signature.hex()


def verify_signature(payload: dict, public_key_hex: str, signature_hex: str) -> bool:
    """
    Verify transaction signature using public key.
    """
    try:
        public_key = VerifyingKey.from_string(
            bytes.fromhex(public_key_hex),
            curve=SECP256k1,
        )

        payload_string = canonical_json(payload)

        return public_key.verify(
            bytes.fromhex(signature_hex),
            payload_string.encode("utf-8"),
        )

    except BadSignatureError:
        return False
    except Exception:
        return False


def sign_transaction(transaction_data: dict, address: str) -> dict:
    """
    Sign a transaction using the wallet stored locally.

    The private key is NOT inserted into the transaction.
    Only public_key and signature are added.
    """
    wallet = get_wallet(address)

    if wallet is None:
        raise ValueError("Wallet not found")

    payload = transaction_data.copy()
    payload.pop("signature", None)
    payload.pop("public_key", None)

    signature = sign_payload(payload, wallet["private_key"])

    signed_transaction = payload.copy()
    signed_transaction["public_key"] = wallet["public_key"]
    signed_transaction["signature"] = signature

    return signed_transaction
