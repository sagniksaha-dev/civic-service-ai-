import re
from app.services.reference_service import reference_service


def test_generate_application_reference_format():
    """Verify application reference format matches APP-YYYYMMDD-XXXX."""
    ref = reference_service.generate_application_reference()
    pattern = r"^APP-\d{8}-[A-Z0-9]{4}$"
    assert re.match(pattern, ref), f"Reference '{ref}' does not match expected pattern"


def test_generate_grievance_reference_format():
    """Verify grievance reference format matches GRV-YYYYMMDD-XXXX."""
    ref = reference_service.generate_grievance_reference()
    pattern = r"^GRV-\d{8}-[A-Z0-9]{4}$"
    assert re.match(pattern, ref), f"Reference '{ref}' does not match expected pattern"


def test_reference_uniqueness():
    """Verify multiple generated references are distinct."""
    refs = {reference_service.generate_application_reference() for _ in range(50)}
    assert len(refs) == 50
