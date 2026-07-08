from storage.json_storage import load_json, save_json


CHAIN_FILE = "data/blockchain.json"
MEMPOOL_FILE = "data/mempool.json"
BALANCES_FILE = "data/balances.json"
CONTRACTS_FILE = "data/contracts.json"
WALLETS_FILE = "data/wallets.json"


def load_chain() -> list:
    return load_json(CHAIN_FILE, [])


def save_chain(chain: list) -> None:
    save_json(CHAIN_FILE, chain)


def load_mempool() -> list:
    return load_json(MEMPOOL_FILE, [])


def save_mempool(mempool: list) -> None:
    save_json(MEMPOOL_FILE, mempool)


def load_balances() -> dict:
    return load_json(BALANCES_FILE, {})


def save_balances(balances: dict) -> None:
    save_json(BALANCES_FILE, balances)


def load_contracts() -> dict:
    return load_json(CONTRACTS_FILE, {})


def save_contracts(contracts: dict) -> None:
    save_json(CONTRACTS_FILE, contracts)


def load_wallets() -> dict:
    return load_json(WALLETS_FILE, {})


def save_wallets(wallets: dict) -> None:
    save_json(WALLETS_FILE, wallets)


def reset_blockchain_data(clear_wallets: bool = False) -> dict:
    """
    Reset blockchain-related data for debugging.

    By default, wallets are NOT cleared so existing wallet addresses
    can still be used for testing after reset.
    """
    save_chain([])
    save_mempool([])
    save_balances({})
    save_contracts({})

    if clear_wallets:
        save_wallets({})

    return {
        "blockchain": [],
        "mempool": [],
        "balances": {},
        "contracts": {},
        "wallets_cleared": clear_wallets,
    }
