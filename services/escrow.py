import uuid

from models.contract import EscrowContract


def generate_contract_address() -> str:
    return "CONTRACT_ESCROW_" + uuid.uuid4().hex[:12].upper()


def deploy_escrow_contract(tx: dict, contracts: dict) -> tuple[bool, str, dict | None]:
    """
    Deploy a new escrow contract.

    contract_address must already exist before signing.
    Do NOT add contract_address after signing.
    """
    if tx.get("type") != "contract_deploy":
        return False, "Invalid transaction type for contract deployment", None

    if tx.get("contract_type") != "ESCROW":
        return False, "Only ESCROW contract type is supported", None

    owner = tx.get("owner")

    if not owner:
        return False, "Missing contract owner", None

    contract_address = tx.get("contract_address")

    if not contract_address:
        return False, "Missing contract_address", None

    if contract_address in contracts:
        return False, "Contract address already exists", None

    contract = EscrowContract(
        contract_address=contract_address,
        owner=owner,
    )

    contract_data = contract.to_dict()

    add_contract_event(
        contract_data,
        "ContractDeployed",
        tx,
        {
            "contract_address": contract_address,
            "owner": owner,
        },
    )

    contracts[contract_address] = contract_data

    return True, "Escrow contract deployed", contract_data


def add_contract_event(
    contract: dict,
    event_name: str,
    tx: dict,
    extra_data: dict | None = None,
) -> None:
    event = {
        "event": event_name,
        "tx_id": tx.get("tx_id"),
        "timestamp": tx.get("timestamp"),
    }

    if extra_data:
        event.update(extra_data)

    contract.setdefault("events", []).append(event)


def get_contract(tx: dict, contracts: dict) -> tuple[bool, str, dict | None]:
    contract_address = tx.get("contract_address")

    if not contract_address:
        return False, "Missing contract_address", None

    contract = contracts.get(contract_address)

    if not contract:
        return False, "Contract not found", None

    if contract.get("contract_type") != "ESCROW":
        return False, "Invalid contract type", None

    return True, "Contract found", contract


def get_order(contract: dict, order_id: str) -> tuple[bool, str, dict | None]:
    if not order_id:
        return False, "Missing order_id", None

    order = contract.get("orders", {}).get(order_id)

    if not order:
        return False, "Order not found", None

    return True, "Order found", order


def is_final_status(status: str) -> bool:
    return status in ["COMPLETED", "REFUNDED", "CANCELLED"]


def execute_escrow_contract_call(
    tx: dict,
    balances: dict,
    contracts: dict,
) -> tuple[bool, str]:
    """
    Execute escrow contract method.

    This is called during mining, not directly from routes.
    """
    valid, message, contract = get_contract(tx, contracts)

    if not valid:
        return False, message

    method = tx.get("method")

    if method == "create_order":
        return create_order(tx, contract)

    if method == "fund_order":
        return fund_order(tx, contract, balances)

    if method == "confirm_shipment":
        return confirm_shipment(tx, contract)

    if method == "confirm_received":
        return confirm_received(tx, contract, balances)

    if method == "raise_dispute":
        return raise_dispute(tx, contract)

    if method == "resolve_dispute":
        return resolve_dispute(tx, contract, balances)

    if method == "cancel_order":
        return cancel_order(tx, contract)

    if method == "get_order":
        return validate_get_order(tx, contract)

    return False, "Invalid escrow method"


def create_order(tx: dict, contract: dict) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")

    order_id = params.get("order_id")
    seller = params.get("seller")
    arbiter = params.get("arbiter")
    amount = params.get("amount")
    item_description = params.get("item_description", "")

    if not order_id:
        return False, "Missing order_id"

    if order_id in contract.get("orders", {}):
        return False, "order_id already exists"

    if not seller:
        return False, "Missing seller"

    if not arbiter:
        return False, "Missing arbiter"

    if not isinstance(amount, (int, float)):
        return False, "Amount must be a number"

    if amount <= 0:
        return False, "Amount must be greater than 0"

    order = {
        "buyer": caller,
        "seller": seller,
        "arbiter": arbiter,
        "amount": amount,
        "status": "CREATED",
        "locked_amount": 0,
        "item_description": item_description,
        "created_at": tx.get("timestamp"),
        "updated_at": tx.get("timestamp"),
    }

    contract.setdefault("orders", {})[order_id] = order

    add_contract_event(
        contract,
        "OrderCreated",
        tx,
        {
            "order_id": order_id,
            "buyer": caller,
            "seller": seller,
            "arbiter": arbiter,
            "amount": amount,
        },
    )

    return True, "Order created"


def fund_order(tx: dict, contract: dict, balances: dict) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")
    order_id = params.get("order_id")

    valid, message, order = get_order(contract, order_id)

    if not valid:
        return False, message

    if is_final_status(order.get("status")):
        return False, "Order is already final"

    if caller != order.get("buyer"):
        return False, "Only buyer can fund this order"

    if order.get("status") != "CREATED":
        return False, "Order must be in CREATED status"

    amount = order.get("amount")

    if balances.get(caller, 0) < amount:
        return False, "Buyer has insufficient balance"

    balances[caller] = balances.get(caller, 0) - amount

    order["locked_amount"] = amount
    order["status"] = "FUNDED"
    order["updated_at"] = tx.get("timestamp")

    add_contract_event(
        contract,
        "OrderFunded",
        tx,
        {
            "order_id": order_id,
            "buyer": caller,
            "locked_amount": amount,
        },
    )

    return True, "Order funded"


def confirm_shipment(tx: dict, contract: dict) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")
    order_id = params.get("order_id")

    valid, message, order = get_order(contract, order_id)

    if not valid:
        return False, message

    if is_final_status(order.get("status")):
        return False, "Order is already final"

    if caller != order.get("seller"):
        return False, "Only seller can confirm shipment"

    if order.get("status") != "FUNDED":
        return False, "Order must be in FUNDED status"

    order["status"] = "SHIPPED"
    order["updated_at"] = tx.get("timestamp")

    add_contract_event(
        contract,
        "ShipmentConfirmed",
        tx,
        {
            "order_id": order_id,
            "seller": caller,
        },
    )

    return True, "Shipment confirmed"


def confirm_received(
    tx: dict,
    contract: dict,
    balances: dict,
) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")
    order_id = params.get("order_id")

    valid, message, order = get_order(contract, order_id)

    if not valid:
        return False, message

    if is_final_status(order.get("status")):
        return False, "Order is already final"

    if caller != order.get("buyer"):
        return False, "Only buyer can confirm received"

    if order.get("status") != "SHIPPED":
        return False, "Order must be in SHIPPED status"

    locked_amount = order.get("locked_amount", 0)

    if locked_amount <= 0:
        return False, "No locked fund to release"

    seller = order.get("seller")

    balances[seller] = balances.get(seller, 0) + locked_amount

    order["locked_amount"] = 0
    order["status"] = "COMPLETED"
    order["updated_at"] = tx.get("timestamp")

    add_contract_event(
        contract,
        "OrderCompleted",
        tx,
        {
            "order_id": order_id,
            "buyer": caller,
            "seller": seller,
            "released_amount": locked_amount,
        },
    )

    return True, "Order completed and fund released to seller"


def raise_dispute(tx: dict, contract: dict) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")
    order_id = params.get("order_id")
    reason = params.get("reason", "")

    valid, message, order = get_order(contract, order_id)

    if not valid:
        return False, message

    if is_final_status(order.get("status")):
        return False, "Order is already final"

    if caller not in [order.get("buyer"), order.get("seller")]:
        return False, "Only buyer or seller can raise dispute"

    if order.get("status") not in ["FUNDED", "SHIPPED"]:
        return False, "Order must be in FUNDED or SHIPPED status"

    order["status"] = "DISPUTED"
    order["updated_at"] = tx.get("timestamp")

    add_contract_event(
        contract,
        "DisputeRaised",
        tx,
        {
            "order_id": order_id,
            "caller": caller,
            "reason": reason,
        },
    )

    return True, "Dispute raised"


def resolve_dispute(
    tx: dict,
    contract: dict,
    balances: dict,
) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")
    order_id = params.get("order_id")
    decision = params.get("decision")
    reason = params.get("reason", "")

    valid, message, order = get_order(contract, order_id)

    if not valid:
        return False, message

    if is_final_status(order.get("status")):
        return False, "Order is already final"

    if caller != order.get("arbiter"):
        return False, "Only arbiter can resolve dispute"

    if order.get("status") != "DISPUTED":
        return False, "Order must be in DISPUTED status"

    locked_amount = order.get("locked_amount", 0)

    if locked_amount <= 0:
        return False, "No locked fund to resolve"

    if decision == "RELEASE_TO_SELLER":
        seller = order.get("seller")

        balances[seller] = balances.get(seller, 0) + locked_amount

        order["locked_amount"] = 0
        order["status"] = "COMPLETED"
        order["updated_at"] = tx.get("timestamp")

        add_contract_event(
            contract,
            "DisputeResolved",
            tx,
            {
                "order_id": order_id,
                "arbiter": caller,
                "decision": decision,
                "reason": reason,
            },
        )

        add_contract_event(
            contract,
            "OrderCompleted",
            tx,
            {
                "order_id": order_id,
                "seller": seller,
                "released_amount": locked_amount,
            },
        )

        return True, "Dispute resolved: fund released to seller"

    if decision == "REFUND_BUYER":
        buyer = order.get("buyer")

        balances[buyer] = balances.get(buyer, 0) + locked_amount

        order["locked_amount"] = 0
        order["status"] = "REFUNDED"
        order["updated_at"] = tx.get("timestamp")

        add_contract_event(
            contract,
            "DisputeResolved",
            tx,
            {
                "order_id": order_id,
                "arbiter": caller,
                "decision": decision,
                "reason": reason,
            },
        )

        add_contract_event(
            contract,
            "OrderRefunded",
            tx,
            {
                "order_id": order_id,
                "buyer": buyer,
                "refunded_amount": locked_amount,
            },
        )

        return True, "Dispute resolved: fund refunded to buyer"

    return False, "Invalid dispute decision"


def cancel_order(tx: dict, contract: dict) -> tuple[bool, str]:
    params = tx.get("params", {})
    caller = tx.get("caller")
    order_id = params.get("order_id")

    valid, message, order = get_order(contract, order_id)

    if not valid:
        return False, message

    if is_final_status(order.get("status")):
        return False, "Order is already final"

    if caller != order.get("buyer"):
        return False, "Only buyer can cancel order"

    if order.get("status") != "CREATED":
        return False, "Only CREATED order can be cancelled"

    order["status"] = "CANCELLED"
    order["updated_at"] = tx.get("timestamp")

    add_contract_event(
        contract,
        "OrderCancelled",
        tx,
        {
            "order_id": order_id,
            "buyer": caller,
        },
    )

    return True, "Order cancelled"


def validate_get_order(tx: dict, contract: dict) -> tuple[bool, str]:
    params = tx.get("params", {})
    order_id = params.get("order_id")

    valid, message, _order = get_order(contract, order_id)

    if not valid:
        return False, message

    return True, "Order exists"
