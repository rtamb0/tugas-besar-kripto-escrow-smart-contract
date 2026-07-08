import uuid
from copy import deepcopy

from services.blockchain import (
    DIFFICULTY,
    calculate_block_hash,
    create_genesis_block,
    execute_transaction,
    get_current_timestamp,
)
from services.wallet import get_wallet
from storage.chain import (
    load_chain,
    save_chain,
    load_mempool,
    save_balances,
    load_balances,
    load_contracts,
    save_contracts,
)
from services.mempool import remove_from_mempool


MINING_REWARD = 100


def proof_of_work(block: dict) -> dict:
    """
    Find nonce until block_hash starts with required number of zeroes.
    """
    block["nonce"] = 0

    while True:
        block_hash = calculate_block_hash(block)

        if block_hash.startswith("0" * block["difficulty"]):
            block["block_hash"] = block_hash
            return block

        block["nonce"] += 1


def create_coinbase_transaction(miner_address: str) -> dict:
    return {
        "tx_id": "COINBASE_" + uuid.uuid4().hex,
        "type": "coinbase",
        "to": miner_address,
        "amount": MINING_REWARD,
        "timestamp": get_current_timestamp(),
    }


def validate_miner_address(miner_address: str) -> tuple[bool, str]:
    """
    For this local assignment project, only allow mining rewards
    to be sent to wallets that exist in wallets.json.

    This prevents accidental mining to fake addresses like:
    PASTE_WALLET_ADDRESS_HERE
    """
    if not miner_address:
        return False, "Miner address is required"

    if not miner_address.startswith("ADDR_"):
        return False, "Invalid miner address format"

    wallet = get_wallet(miner_address)

    if wallet is None:
        return False, "Miner wallet does not exist"

    return True, "Miner address valid"


def mine_block(miner_address: str) -> dict:
    """
    Mine a new block.

    Flow:
    1. Validate miner wallet exists.
    2. Ensure genesis block exists.
    3. Load mempool.
    4. Add coinbase transaction.
    5. Execute valid transactions.
    6. Skip transactions that became invalid.
    7. Mine block hash.
    8. Save block, balances, contracts, and updated mempool.
    """
    valid_miner, miner_message = validate_miner_address(miner_address)

    if not valid_miner:
        raise ValueError(miner_message)

    chain = load_chain()

    if len(chain) == 0:
        create_genesis_block()
        chain = load_chain()

    mempool = load_mempool()
    balances = load_balances()
    contracts = load_contracts()

    temporary_balances = deepcopy(balances)
    temporary_contracts = deepcopy(contracts)

    coinbase_tx = create_coinbase_transaction(miner_address)

    success, message = execute_transaction(
        coinbase_tx,
        temporary_balances,
        temporary_contracts,
    )

    if not success:
        raise ValueError(message)

    included_transactions = [coinbase_tx]
    mined_tx_ids = []
    skipped_transactions = []

    for tx in mempool:
        balance_snapshot = deepcopy(temporary_balances)
        contract_snapshot = deepcopy(temporary_contracts)

        success, message = execute_transaction(
            tx,
            temporary_balances,
            temporary_contracts,
        )

        if success:
            included_transactions.append(tx)
            mined_tx_ids.append(tx.get("tx_id"))
        else:
            temporary_balances = balance_snapshot
            temporary_contracts = contract_snapshot
            skipped_transactions.append(
                {
                    "tx_id": tx.get("tx_id"),
                    "reason": message,
                }
            )

    previous_block = chain[-1]

    new_block = {
        "height": len(chain),
        "timestamp": get_current_timestamp(),
        "transactions": included_transactions,
        "prev_hash": previous_block["block_hash"],
        "nonce": 0,
        "difficulty": DIFFICULTY,
    }

    mined_block = proof_of_work(new_block)

    chain.append(mined_block)

    save_chain(chain)
    save_balances(temporary_balances)
    save_contracts(temporary_contracts)
    remove_from_mempool(mined_tx_ids)

    return {
        "message": "Block mined successfully",
        "block": mined_block,
        "skipped_transactions": skipped_transactions,
    }
