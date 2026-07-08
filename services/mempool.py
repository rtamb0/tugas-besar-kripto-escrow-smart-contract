from services.validator import validate_transaction
from storage.chain import load_mempool, save_mempool


def get_mempool() -> list:
    """
    Return all pending transactions.
    """
    return load_mempool()


def add_to_mempool(tx: dict) -> tuple[bool, str]:
    """
    Validate transaction first.
    If valid, add it to mempool.
    """
    valid, message = validate_transaction(tx)

    if not valid:
        return False, message

    mempool = load_mempool()
    mempool.append(tx)
    save_mempool(mempool)

    return True, "Transaction added to mempool"


def remove_from_mempool(tx_ids: list[str]) -> None:
    """
    Remove transactions from mempool after they are mined.
    """
    mempool = load_mempool()

    updated_mempool = [tx for tx in mempool if tx.get("tx_id") not in tx_ids]

    save_mempool(updated_mempool)


def clear_mempool() -> None:
    """
    Clear all pending transactions.
    Useful for testing.
    """
    save_mempool([])
