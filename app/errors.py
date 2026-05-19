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


class ArtifactServeViolation(AppError):
    status_code = 404
    public_code = "artifact_unavailable"
    public_message = "Artifact is unavailable."


class ArtifactNotFoundError(AppError):
    status_code = 404
    public_code = "artifact_unavailable"
    public_message = "Artifact is unavailable."


class ActiveRunConflictError(AppError):
    status_code = 409
    public_code = "active_run_exists"
    public_message = "Another run is already active."


class StageError(AppError):
    status_code = 500
    public_code = "stage_failed"
    public_message = "Pipeline stage execution failed."


class ArtifactClassError(AppError):
    status_code = 500
    public_code = "artifact_class_required"
    public_message = "Artifact could not be recorded safely."


class ParityMetadataError(AppError):
    status_code = 500
    public_code = "invalid_stage_metadata"
    public_message = "Stage metadata is invalid."

