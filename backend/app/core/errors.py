from dataclasses import dataclass


@dataclass
class ApiProblem(Exception):
    code: str
    status_code: int
    message: str = "Request could not be completed."


class DuplicateOperation(ApiProblem):
    def __init__(self) -> None:
        super().__init__("idempotency_conflict", 409, "The operation reference was already used.")


class InsufficientBalance(ApiProblem):
    def __init__(self) -> None:
        super().__init__("insufficient_balance", 409, "The wallet balance is insufficient.")
