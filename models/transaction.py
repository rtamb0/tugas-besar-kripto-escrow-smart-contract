from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transaction:
    tx_id: str
    type: str

    from_address: Optional[str] = None
    to: Optional[str] = None
    amount: Optional[int] = None

    contract_address: Optional[str] = None
    contract_type: Optional[str] = None
    owner: Optional[str] = None
    deployment_params: Optional[dict] = None

    method: Optional[str] = None
    params: dict = field(default_factory=dict)
    caller: Optional[str] = None

    nonce: Optional[int] = None
    timestamp: Optional[str] = None
    public_key: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "tx_id": self.tx_id,
            "type": self.type,
            "from": self.from_address,
            "to": self.to,
            "amount": self.amount,
            "contract_address": self.contract_address,
            "contract_type": self.contract_type,
            "owner": self.owner,
            "deployment_params": self.deployment_params,
            "method": self.method,
            "params": self.params,
            "caller": self.caller,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "public_key": self.public_key,
            "signature": self.signature,
        }

        return {key: value for key, value in data.items() if value is not None}

    def payload_dict(self) -> dict:
        """
        Data used for signing/verifying.
        Signature is excluded.
        Public key is also excluded because it is used to verify the signature.
        """
        data = self.to_dict()
        data.pop("signature", None)
        data.pop("public_key", None)
        return data

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        return Transaction(
            tx_id=data["tx_id"],
            type=data["type"],
            from_address=data.get("from"),
            to=data.get("to"),
            amount=data.get("amount"),
            contract_address=data.get("contract_address"),
            contract_type=data.get("contract_type"),
            owner=data.get("owner"),
            deployment_params=data.get("deployment_params"),
            method=data.get("method"),
            params=data.get("params", {}),
            caller=data.get("caller"),
            nonce=data.get("nonce"),
            timestamp=data.get("timestamp"),
            public_key=data.get("public_key"),
            signature=data.get("signature"),
        )
