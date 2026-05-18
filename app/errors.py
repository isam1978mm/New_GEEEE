from __future__ import annotations


class AppError(Exception):
    status_code = 500
    public_code = "internal_error"
    public_message = "Request could not be processed."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)


class RedactionViolationError(AppError):
    status_code = 500
    public_code = "redaction_violation"
    public_message = "Response could not be processed safely."


class EEInitializationError(AppError):
    status_code = 503
    public_code = "ee_not_ready"
    public_message = "Service is not ready."

