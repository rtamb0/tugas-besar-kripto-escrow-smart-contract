from dataclasses import dataclass


@dataclass
class Wallet:
    address: str
    public_key: str
    private_key: str

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "public_key": self.public_key,
            "private_key": self.private_key,
        }

    @staticmethod
    def from_dict(data: dict) -> "Wallet":
        return Wallet(
            address=data["address"],
            public_key=data["public_key"],
            private_key=data["private_key"],
        )
