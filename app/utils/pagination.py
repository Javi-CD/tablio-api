from dataclasses import dataclass

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass
class PaginationParams:
    page: int = 1
    limit: int = DEFAULT_LIMIT

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.limit < 1:
            self.limit = 1
        if self.limit > MAX_LIMIT:
            self.limit = MAX_LIMIT

    def offset(self) -> int:
        return (self.page - 1) * self.limit


def total_pages(total: int, limit: int) -> int:
    if limit <= 0:
        return 0
    return (total + limit - 1) // limit
