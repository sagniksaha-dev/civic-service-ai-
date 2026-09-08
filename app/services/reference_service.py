from datetime import datetime, timezone
import random
import string


class ReferenceService:
    """Service for generating unique, standardized reference numbers for civic entities."""

    @staticmethod
    def generate_application_reference() -> str:
        """Generate formatted service application reference number: APP-YYYYMMDD-XXXX."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"APP-{date_str}-{random_suffix}"

    @staticmethod
    def generate_grievance_reference() -> str:
        """Generate formatted grievance tracking reference number: GRV-YYYYMMDD-XXXX."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"GRV-{date_str}-{random_suffix}"


reference_service = ReferenceService()
