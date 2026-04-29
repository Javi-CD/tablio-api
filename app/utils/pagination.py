from dataclasses import dataclass


@dataclass
class PaginationParams:
    page: int = 1
    limit: int = 20

    def offset(self) -> int:
        return (self.page - 1) * self.limit


def total_pages(total: int, limit: int) -> int:
    if limit <= 0:
        return 0
    return (total + limit - 1) // limit
