import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.citizen import Citizen
from app.models.department import Department
from app.models.service import Service, ServiceStatus
from app.core.security import get_password_hash
from app.core.logging import logger


def create_initial_users_and_domain() -> None:
    """Seed initial Admin, Department Officer, Citizen users, and sample civic departments and services."""
    db = SessionLocal()
    try:
        # 1. Seed Users
        users_to_seed = [
            {
                "name": "System Administrator",
                "email": "admin@civic.local",
                "password": "AdminPassword123!",
                "role": UserRole.ADMIN
            },
            {
                "name": "Department Officer",
                "email": "officer@civic.local",
                "password": "OfficerPassword123!",
                "role": UserRole.DEPARTMENT_OFFICER
            },
            {
                "name": "Demo Citizen",
                "email": "citizen@civic.local",
                "password": "CitizenPassword123!",
                "role": UserRole.CITIZEN
            }
        ]

        for user_data in users_to_seed:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                if user.role == UserRole.CITIZEN:
                    citizen = Citizen(
                        user_id=user.id,
                        phone="9876543210",
                        address={
                            "street": "123 Civil Lines",
                            "city": "Metropolis",
                            "district": "Central",
                            "state": "State",
                            "postal_code": "700001"
                        }
                    )
                    db.add(citizen)
                    db.commit()

                logger.info("Created user: %s (%s) with role '%s'", user.name, user.email, user.role.value)
            else:
                logger.info("User already exists: %s (%s)", existing.name, existing.email)

        # 2. Seed Sample Departments
        depts_to_seed = [
            {
                "name": "Urban Water Supply Department",
                "code": "UWSD",
                "description": "Potable municipal drinking water connections, meter installation, and pipeline maintenance."
            },
            {
                "name": "Municipal Revenue Department",
                "code": "REV",
                "description": "Property tax assessments, municipal rates, mutation records, and holding tax certificates."
            },
            {
                "name": "Commerce & Trade Licensing Authority",
                "code": "TRADE",
                "description": "Commercial trade licenses, renewals, and business establishment compliance permits."
            },
            {
                "name": "Civil Registration & Vital Statistics",
                "code": "CIV-REG",
                "description": "Official issuance and correction of Birth and Death certificates."
            },
            {
                "name": "Urban Planning & Building Sanction",
                "code": "URB-PLAN",
                "description": "Architectural scrutiny, residential/commercial building permits, and structural NOCs."
            },
            {
                "name": "Department of Public Sanitation",
                "code": "DPS-SAN",
                "description": "City-wide solid waste management, sewage upkeep, drainage unclogging, and sanitation permits."
            },
            {
                "name": "Fire Safety & Disaster Management Authority",
                "code": "FIRE-EMERG",
                "description": "Commercial building Fire Safety NOC clearances, periodic fire hydrant testing, emergency flood relief, and building safety audits."
            },
            {
                "name": "Department of Public Health & Food Safety",
                "code": "DPH-FOOD",
                "description": "Issuance of food business hygiene ratings, mosquito eradication drives, municipal immunization centers, and public health inspection clearance certificates."
            },
            {
                "name": "Department of Environment & Urban Greenery",
                "code": "ENV-PARKS",
                "description": "Tree trimming permits, public municipal park maintenance, urban afforestation drives, and air quality monitoring initiatives."
            },
            {
                "name": "Municipal Transport & Traffic Management",
                "code": "MUNI-TRANS",
                "description": "Commercial parking permits, electric vehicle charging zone allocation, street light maintenance, and road digging NOC permits."
            }
        ]

        dept_map = {}
        for d in depts_to_seed:
            existing_d = db.query(Department).filter(Department.code == d["code"]).first()
            if not existing_d:
                new_d = Department(name=d["name"], code=d["code"], description=d["description"], is_active=True)
                db.add(new_d)
                db.commit()
                db.refresh(new_d)
                dept_map[d["code"]] = new_d
                logger.info("Created department: %s (%s)", new_d.name, new_d.code)
            else:
                dept_map[d["code"]] = existing_d

        # 3. Seed Sample Services
        services_to_seed = [
            {
                "dept_code": "UWSD",
                "name": "New Domestic Water Connection",
                "code": "UWSD-WTR-01",
                "description": "Sanction and meter installation for new residential potable water connection.",
                "requirements": {
                    "required_documents": [
                        "Proof of Address (Electricity bill / rental deed)",
                        "Current Year Property Tax Receipt",
                        "Plumbing Hookup Layout Plan"
                    ],
                    "fee_structure": "Rs. 500 Application Fee + Rs. 1500 Meter Security Deposit"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "residency_required": True,
                    "no_outstanding_arrears": True
                },
                "processing_time_days": 15
            },
            {
                "dept_code": "UWSD",
                "name": "Residential Pipeline Installation",
                "code": "WAT-INST-01",
                "description": "Municipal pipeline extension and secondary plumbing line connection for residential houses.",
                "requirements": {
                    "required_documents": [
                        "Holding Tax Receipt",
                        "Sanctioned Site Blueprint"
                    ],
                    "fee_structure": "Rs. 1,200 standard installation charge"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "municipal_line_available": True
                },
                "processing_time_days": 10
            },
            {
                "dept_code": "REV",
                "name": "Property Tax Assessment & Mutation",
                "code": "REV-MUT-01",
                "description": "Official update of title ownership in municipal tax registers and property records.",
                "requirements": {
                    "required_documents": [
                        "Registered Sale Deed / Gift Deed Copy",
                        "Prior Mutation Certificate",
                        "Latest Property Tax Clear Challan"
                    ],
                    "fee_structure": "0.5% of Assessed Property Valuation"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "title_holder": True
                },
                "processing_time_days": 21
            },
            {
                "dept_code": "TRADE",
                "name": "General Commercial Trade License",
                "code": "TRADE-LIC-01",
                "description": "Annual statutory trade license for retail, wholesale, and service establishments.",
                "requirements": {
                    "required_documents": [
                        "Commercial Rent Agreement or Ownership Deed",
                        "Fire Safety NOC (for >500 sq ft)",
                        "Trade Description & Goods Declaration"
                    ],
                    "fee_structure": "Rs. 1,000 to Rs. 5,000 depending on floor area"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "commercial_zone_compliant": True
                },
                "processing_time_days": 10
            },
            {
                "dept_code": "CIV-REG",
                "name": "Birth Certificate Registration & Issuance",
                "code": "CIV-BIRTH-01",
                "description": "Official vital statistics registration and issuance of standard Birth Certificate.",
                "requirements": {
                    "required_documents": [
                        "Hospital Discharge / Birth Event Report",
                        "Parents Identity & Address Proof",
                        "Municipal Registration Form"
                    ],
                    "fee_structure": "Free within 21 days; Rs. 50 for certified copies"
                },
                "eligibility_criteria": {
                    "event_within_jurisdiction": True
                },
                "processing_time_days": 7
            },
            {
                "dept_code": "URB-PLAN",
                "name": "Residential Building Plan Sanction",
                "code": "PLAN-SANCT-01",
                "description": "Architectural approval and building construction permit up to 4 storeys.",
                "requirements": {
                    "required_documents": [
                        "CAD Architectural Drawings (Signed by LBS)",
                        "Structural Stability Certificate",
                        "Land Title Deed & Mutation Copy"
                    ],
                    "fee_structure": "Rs. 25 per sq meter of built-up area"
                },
                "eligibility_criteria": {
                    "clear_land_title": True,
                    "compliant_setbacks": True
                },
                "processing_time_days": 30
            },
            {
                "dept_code": "DPS-SAN",
                "name": "Bulk Commercial Waste Disposal & Sanitation Clearance",
                "code": "SAN-BULK-01",
                "description": "Scheduled bulk solid waste collection, hazardous waste clearance, and municipal sanitation clearance certificate.",
                "requirements": {
                    "required_documents": [
                        "Trade License / Property Ownership Proof",
                        "Waste Segregation Storage Facility Declaration",
                        "Bio-waste Composting Agreement (if applicable)"
                    ],
                    "fee_structure": "Rs. 800 per month or Rs. 5,000 annual subscription"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "waste_generator_tier": "commercial"
                },
                "processing_time_days": 7
            },
            {
                "dept_code": "FIRE-EMERG",
                "name": "Commercial Building Fire Safety NOC Clearance",
                "code": "FIRE-NOC-01",
                "description": "Statutory Fire Safety No Objection Certificate (NOC) for commercial establishments, hotels, hospitals, and high-rise structures.",
                "requirements": {
                    "required_documents": [
                        "Approved Architectural Floor Plans with Emergency Fire Exits",
                        "Firefighting System Installation Proof (Extinguishers, Sprinklers, Hydrant)",
                        "Structural Fire Resistance & Electrical Load Safety Certificate",
                        "Commercial Property Lease or Ownership Deed"
                    ],
                    "fee_structure": "Rs. 2,500 for premises <2,000 sq ft; Rs. 5,000 for high-rise commercial structures"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "fire_equipment_installed": True
                },
                "processing_time_days": 15
            },
            {
                "dept_code": "FIRE-EMERG",
                "name": "Annual Fire Safety Certificate Renewal & Audit",
                "code": "FIRE-AUDIT-01",
                "description": "Mandatory annual inspection, sprinkler system check, and fire safety certificate renewal.",
                "requirements": {
                    "required_documents": [
                        "Previous Fire Safety NOC Copy",
                        "Annual Extinguisher Refill & Maintenance Receipt",
                        "Fire Evacuation Drill Log Sheet"
                    ],
                    "fee_structure": "Rs. 1,000 Annual Audit & Renewal Fee"
                },
                "eligibility_criteria": {
                    "existing_noc_holder": True
                },
                "processing_time_days": 7
            },
            {
                "dept_code": "DPH-FOOD",
                "name": "Commercial Food Hygiene & Safety Rating Certificate",
                "code": "FOOD-HYG-01",
                "description": "Public health inspection and hygiene rating certification for restaurants, cafes, and food vendors.",
                "requirements": {
                    "required_documents": [
                        "FSSAI Registration / License Copy",
                        "Staff Medical Health Fitness Certificates",
                        "Quarterly Pest Control Certificate",
                        "Potable Water Microbial Test Report"
                    ],
                    "fee_structure": "Rs. 1,500 for eateries; Rs. 3,500 for large restaurants"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "food_safety_supervisor_certified": True
                },
                "processing_time_days": 10
            },
            {
                "dept_code": "ENV-PARKS",
                "name": "Dangerous Tree Trimming & Arboriculture Clearance",
                "code": "ENV-TREE-01",
                "description": "Official municipal permit for trimming overgrown, hazardous, or power-line obstructing trees.",
                "requirements": {
                    "required_documents": [
                        "Proof of Property Ownership / Ward Councillor Recommendation",
                        "Photographs of Hazardous Tree / Overgrown Branches",
                        "Site Access Consent Form"
                    ],
                    "fee_structure": "Rs. 300 inspection fee"
                },
                "eligibility_criteria": {
                    "min_age": 18,
                    "hazard_verified": True
                },
                "processing_time_days": 5
            },
            {
                "dept_code": "MUNI-TRANS",
                "name": "Road Digging NOC & Utility Trenching Permit",
                "code": "TRANS-ROAD-01",
                "description": "Municipal clearance and traffic coordination permit for underground cable laying, pipeline trenching, and road excavation.",
                "requirements": {
                    "required_documents": [
                        "Approved Utility Alignment Trenching Map",
                        "Traffic Management & Diversion Plan (Traffic Police Approved)",
                        "Road Surface Restoration Bank Guarantee"
                    ],
                    "fee_structure": "Rs. 3,000 per linear meter refundable restoration deposit"
                },
                "eligibility_criteria": {
                    "authorized_utility_agency_or_contractor": True
                },
                "processing_time_days": 14
            }
        ]

        for s in services_to_seed:
            existing_s = db.query(Service).filter(Service.code == s["code"]).first()
            if not existing_s and s["dept_code"] in dept_map:
                new_s = Service(
                    department_id=dept_map[s["dept_code"]].id,
                    name=s["name"],
                    code=s["code"],
                    description=s["description"],
                    requirements=s["requirements"],
                    eligibility_criteria=s["eligibility_criteria"],
                    processing_time_days=s["processing_time_days"],
                    status=ServiceStatus.ACTIVE
                )
                db.add(new_s)
                db.commit()
                logger.info("Created service: %s (%s)", new_s.name, new_s.code)

        print("\n" + "=" * 60)
        print("Initial Users & Domain Seed Summary:")
        print("-" * 60)
        print("Admin:   admin@civic.local   / AdminPassword123!")
        print("Officer: officer@civic.local / OfficerPassword123!")
        print("Citizen: citizen@civic.local / CitizenPassword123!")
        print(f"Seeded {len(depts_to_seed)} Departments and {len(services_to_seed)} Services.")
        print("=" * 60)

    except Exception as e:
        logger.error("Error creating initial setup: %s", e)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_users_and_domain()
