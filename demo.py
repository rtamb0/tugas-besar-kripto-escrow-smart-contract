from services.wallet import create_wallet, sign_transaction
from services.mempool import add_to_mempool
from services.mining import mine_block
from services.blockchain import verify_chain
from services.escrow import generate_contract_address
from storage.chain import (
    save_chain,
    save_mempool,
    save_balances,
    save_contracts,
    load_balances,
    load_contracts,
    load_chain,
)


def submit_and_mine(tx: dict, signer_wallet: dict, miner_address: str, label: str):
    signed_tx = sign_transaction(tx, signer_wallet["address"])

    success, message = add_to_mempool(signed_tx)

    print(f"\n{label} - add to mempool:")
    print(success, message)

    result = mine_block(miner_address)

    print(f"{label} - mining:")
    print(result["message"])

    if result["skipped_transactions"]:
        print("Skipped transactions:")
        print(result["skipped_transactions"])

    return result


def get_order(contract_address: str, order_id: str):
    contracts = load_contracts()
    contract = contracts.get(contract_address, {})
    orders = contract.get("orders", {})
    return orders.get(order_id)


def print_order_state(title: str, contract_address: str, order_id: str):
    print(f"\n===== {title} =====")

    print("Balances:")
    print(load_balances())

    print(f"\nOrder {order_id}:")
    print(get_order(contract_address, order_id))


def print_contract_summary(contract_address: str):
    contracts = load_contracts()
    contract = contracts.get(contract_address)

    print("\n===== Final Contract Summary =====")

    if not contract:
        print("Contract not found")
        return

    print("Contract Address:", contract.get("contract_address"))
    print("Owner:", contract.get("owner"))

    print("\nOrders:")
    for order_id, order in contract.get("orders", {}).items():
        print(
            order_id,
            {
                "status": order.get("status"),
                "amount": order.get("amount"),
                "locked_amount": order.get("locked_amount"),
                "buyer": order.get("buyer"),
                "seller": order.get("seller"),
                "arbiter": order.get("arbiter"),
            },
        )

    print("\nEvents:")
    for event in contract.get("events", []):
        print(event)


def tamper_chain():
    """
    Simulate tampering by changing transaction data already stored inside a block.

    Expected result:
    verify_chain() should return False because recalculated block_hash
    will no longer match the stored block_hash.
    """
    chain = load_chain()

    for block in chain:
        for tx in block.get("transactions", []):
            if tx.get("tx_id") == "TX_CREATE_ORDER_001":
                tx["params"]["amount"] = 999
                save_chain(chain)

                return True, (
                    "Tampered TX_CREATE_ORDER_001: changed params.amount from 50 to 999"
                )

    return False, "Target transaction not found for tampering"


# Reset data for clean testing
save_chain([])
save_mempool([])
save_balances({})
save_contracts({})


# Create wallets
owner_wallet = create_wallet()
buyer_wallet = create_wallet()
seller_wallet = create_wallet()
arbiter_wallet = create_wallet()
miner_wallet = create_wallet()

contract_address = generate_contract_address()

normal_order_id = "ORDER-001"
dispute_order_id = "ORDER-002"

print("Owner:", owner_wallet["address"])
print("Buyer:", buyer_wallet["address"])
print("Seller:", seller_wallet["address"])
print("Arbiter:", arbiter_wallet["address"])
print("Miner:", miner_wallet["address"])
print("Contract:", contract_address)


# ============================================================
# 1. Initial mining so buyer has native coin
# ============================================================

print("\nInitial mining to give buyer balance...")
mine_block(buyer_wallet["address"])

print("\nBalances after initial mining:")
print(load_balances())


# ============================================================
# 2. Deploy Escrow Contract
# ============================================================

deploy_tx = {
    "tx_id": "TX_DEPLOY_ESCROW_001",
    "type": "contract_deploy",
    "contract_address": contract_address,
    "contract_type": "ESCROW",
    "owner": owner_wallet["address"],
    "nonce": 1,
    "timestamp": "2026-07-01 10:00:00",
}

submit_and_mine(
    deploy_tx,
    owner_wallet,
    miner_wallet["address"],
    "Deploy Escrow Contract",
)


# ============================================================
# SCENARIO 1: NORMAL FLOW
# CREATED → FUNDED → SHIPPED → COMPLETED
# ============================================================

print("\n\n==============================")
print("SCENARIO 1: NORMAL FLOW")
print("==============================")


create_order_1_tx = {
    "tx_id": "TX_CREATE_ORDER_001",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "create_order",
    "params": {
        "order_id": normal_order_id,
        "seller": seller_wallet["address"],
        "arbiter": arbiter_wallet["address"],
        "amount": 50,
        "item_description": "Mechanical Keyboard",
    },
    "caller": buyer_wallet["address"],
    "nonce": 1,
    "timestamp": "2026-07-01 10:05:00",
}

submit_and_mine(
    create_order_1_tx,
    buyer_wallet,
    miner_wallet["address"],
    "Create Normal Order",
)

print_order_state(
    "After Create Normal Order",
    contract_address,
    normal_order_id,
)


fund_order_1_tx = {
    "tx_id": "TX_FUND_ORDER_001",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "fund_order",
    "params": {
        "order_id": normal_order_id,
    },
    "caller": buyer_wallet["address"],
    "nonce": 2,
    "timestamp": "2026-07-01 10:10:00",
}

submit_and_mine(
    fund_order_1_tx,
    buyer_wallet,
    miner_wallet["address"],
    "Fund Normal Order",
)

print_order_state(
    "After Fund Normal Order",
    contract_address,
    normal_order_id,
)


confirm_shipment_tx = {
    "tx_id": "TX_CONFIRM_SHIPMENT_001",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "confirm_shipment",
    "params": {
        "order_id": normal_order_id,
    },
    "caller": seller_wallet["address"],
    "nonce": 1,
    "timestamp": "2026-07-01 10:15:00",
}

submit_and_mine(
    confirm_shipment_tx,
    seller_wallet,
    miner_wallet["address"],
    "Confirm Shipment",
)

print_order_state(
    "After Confirm Shipment",
    contract_address,
    normal_order_id,
)


confirm_received_tx = {
    "tx_id": "TX_CONFIRM_RECEIVED_001",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "confirm_received",
    "params": {
        "order_id": normal_order_id,
    },
    "caller": buyer_wallet["address"],
    "nonce": 3,
    "timestamp": "2026-07-01 10:20:00",
}

submit_and_mine(
    confirm_received_tx,
    buyer_wallet,
    miner_wallet["address"],
    "Confirm Received",
)

print_order_state(
    "After Confirm Received",
    contract_address,
    normal_order_id,
)


# ============================================================
# SCENARIO 2: DISPUTE + REFUND
# CREATED → FUNDED → DISPUTED → REFUNDED
# ============================================================

print("\n\n==============================")
print("SCENARIO 2: DISPUTE + REFUND")
print("==============================")


create_order_2_tx = {
    "tx_id": "TX_CREATE_ORDER_002",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "create_order",
    "params": {
        "order_id": dispute_order_id,
        "seller": seller_wallet["address"],
        "arbiter": arbiter_wallet["address"],
        "amount": 50,
        "item_description": "Gaming Mouse",
    },
    "caller": buyer_wallet["address"],
    "nonce": 4,
    "timestamp": "2026-07-01 10:25:00",
}

submit_and_mine(
    create_order_2_tx,
    buyer_wallet,
    miner_wallet["address"],
    "Create Dispute Order",
)

print_order_state(
    "After Create Dispute Order",
    contract_address,
    dispute_order_id,
)


fund_order_2_tx = {
    "tx_id": "TX_FUND_ORDER_002",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "fund_order",
    "params": {
        "order_id": dispute_order_id,
    },
    "caller": buyer_wallet["address"],
    "nonce": 5,
    "timestamp": "2026-07-01 10:30:00",
}

submit_and_mine(
    fund_order_2_tx,
    buyer_wallet,
    miner_wallet["address"],
    "Fund Dispute Order",
)

print_order_state(
    "After Fund Dispute Order",
    contract_address,
    dispute_order_id,
)


raise_dispute_tx = {
    "tx_id": "TX_RAISE_DISPUTE_001",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "raise_dispute",
    "params": {
        "order_id": dispute_order_id,
        "reason": "Seller did not ship the item",
    },
    "caller": buyer_wallet["address"],
    "nonce": 6,
    "timestamp": "2026-07-01 10:35:00",
}

submit_and_mine(
    raise_dispute_tx,
    buyer_wallet,
    miner_wallet["address"],
    "Raise Dispute",
)

print_order_state(
    "After Raise Dispute",
    contract_address,
    dispute_order_id,
)


resolve_dispute_tx = {
    "tx_id": "TX_RESOLVE_DISPUTE_001",
    "type": "contract_call",
    "contract_address": contract_address,
    "method": "resolve_dispute",
    "params": {
        "order_id": dispute_order_id,
        "decision": "REFUND_BUYER",
        "reason": "Buyer evidence accepted",
    },
    "caller": arbiter_wallet["address"],
    "nonce": 1,
    "timestamp": "2026-07-01 10:40:00",
}

submit_and_mine(
    resolve_dispute_tx,
    arbiter_wallet,
    miner_wallet["address"],
    "Resolve Dispute With Refund",
)

print_order_state(
    "After Resolve Dispute With Refund",
    contract_address,
    dispute_order_id,
)


# ============================================================
# 3. Verify valid chain before tampering
# ============================================================

valid, verify_message = verify_chain()

print("\n===== Verify Chain Before Tampering =====")
print(valid, verify_message)

print_contract_summary(contract_address)


# ============================================================
# 4. Tampering Test
# ============================================================

print("\n\n==============================")
print("TAMPERING TEST")
print("==============================")

tampered, tamper_message = tamper_chain()

print("\nTampering result:")
print(tampered, tamper_message)

valid_after_tamper, tamper_verify_message = verify_chain()

print("\n===== Verify Chain After Tampering =====")
print(valid_after_tamper, tamper_verify_message)
