class TablioError(Exception):
    """Base error for all Tablio domain errors."""


class NotFoundError(TablioError):
    """Raised when a requested resource does not exist."""


class ForbiddenError(TablioError):
    """Raised when the user is not authorized to access a resource."""


class ConflictError(TablioError):
    """Raised when an operation conflicts with the current resource state."""


class BusinessRuleError(TablioError):
    """Raised when a business rule validation fails."""
