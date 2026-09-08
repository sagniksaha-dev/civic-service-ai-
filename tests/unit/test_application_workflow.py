import pytest
from fastapi import HTTPException
from app.models.service_application import ApplicationStatus
from app.services.application_service import application_workflow_service


def test_valid_status_transitions():
    """Verify valid workflow transitions succeed without error."""
    # SUBMITTED -> UNDER_REVIEW
    application_workflow_service.validate_status_transition(
        current_status=ApplicationStatus.SUBMITTED,
        new_status=ApplicationStatus.UNDER_REVIEW
    )

    # UNDER_REVIEW -> APPROVED
    application_workflow_service.validate_status_transition(
        current_status=ApplicationStatus.UNDER_REVIEW,
        new_status=ApplicationStatus.APPROVED
    )

    # UNDER_REVIEW -> ADDITIONAL_INFO_REQUIRED
    application_workflow_service.validate_status_transition(
        current_status=ApplicationStatus.UNDER_REVIEW,
        new_status=ApplicationStatus.ADDITIONAL_INFO_REQUIRED
    )


def test_invalid_status_transitions():
    """Verify invalid workflow transitions raise HTTP 400 Bad Request."""
    # Direct jump from SUBMITTED to APPROVED without review
    with pytest.raises(HTTPException) as exc_info:
        application_workflow_service.validate_status_transition(
            current_status=ApplicationStatus.SUBMITTED,
            new_status=ApplicationStatus.APPROVED
        )
    assert exc_info.value.status_code == 400

    # Transitioning from terminal state APPROVED
    with pytest.raises(HTTPException) as exc_info:
        application_workflow_service.validate_status_transition(
            current_status=ApplicationStatus.APPROVED,
            new_status=ApplicationStatus.UNDER_REVIEW
        )
    assert exc_info.value.status_code == 400
