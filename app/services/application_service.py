from typing import Set, Tuple
from fastapi import HTTPException, status
from app.models.service_application import ApplicationStatus


class ApplicationWorkflowService:
    """Service to validate and manage service application state transitions."""

    # Define valid transitions: source_status -> allowed target_statuses
    VALID_TRANSITIONS: dict[ApplicationStatus, Set[ApplicationStatus]] = {
        ApplicationStatus.SUBMITTED: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.REJECTED
        },
        ApplicationStatus.UNDER_REVIEW: {
            ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
            ApplicationStatus.APPROVED,
            ApplicationStatus.REJECTED
        },
        ApplicationStatus.ADDITIONAL_INFO_REQUIRED: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.REJECTED
        },
        ApplicationStatus.APPROVED: set(),  # Terminal state
        ApplicationStatus.REJECTED: set(),  # Terminal state
    }

    @classmethod
    def validate_status_transition(
        cls,
        current_status: ApplicationStatus,
        new_status: ApplicationStatus
    ) -> None:
        """Ensure the requested status transition conforms to civic workflow rules."""
        if current_status == new_status:
            return

        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from '{current_status.value}' to '{new_status.value}'. Allowed target states: {[s.value for s in allowed]}"
            )


application_workflow_service = ApplicationWorkflowService()
