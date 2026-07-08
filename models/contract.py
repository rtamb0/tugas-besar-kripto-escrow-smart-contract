from dataclasses import dataclass, field


@dataclass
class Order:
    order_id: str
    buyer: str
    seller: str
    arbiter: str
    amount: int
    status: str
    locked_amount: int
    item_description: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "buyer": self.buyer,
            "seller": self.seller,
            "arbiter": self.arbiter,
            "amount": self.amount,
            "status": self.status,
            "locked_amount": self.locked_amount,
            "item_description": self.item_description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(order_id: str, data: dict) -> "Order":
        return Order(
            order_id=order_id,
            buyer=data["buyer"],
            seller=data["seller"],
            arbiter=data["arbiter"],
            amount=data["amount"],
            status=data["status"],
            locked_amount=data.get("locked_amount", 0),
            item_description=data.get("item_description", ""),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class EscrowContract:
    contract_address: str
    owner: str
    contract_type: str = "ESCROW"
    orders: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "contract_address": self.contract_address,
            "contract_type": self.contract_type,
            "owner": self.owner,
            "orders": self.orders,
            "events": self.events,
        }

    @staticmethod
    def from_dict(data: dict) -> "EscrowContract":
        return EscrowContract(
            contract_address=data["contract_address"],
            contract_type=data.get("contract_type", "ESCROW"),
            owner=data["owner"],
            orders=data.get("orders", {}),
            events=data.get("events", []),
        )
