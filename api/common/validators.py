import re
from typing import Literal

MOBILE_RE = re.compile(r"^[6-9]\d{9}$")

UserRole = Literal["hirer", "coach"]
HirerKind = Literal["player", "parent", "club"]
RateUnit = Literal["session", "month"]
HireRequestStatus = Literal["pending", "accepted", "declined", "withdrawn"]
StatusTransitionRole = Literal["coach", "hirer"]


def validate_mobile(mobile: str) -> str | None:
    trimmed = mobile.strip()
    if not MOBILE_RE.match(trimmed):
        return "Enter a valid 10-digit Indian mobile number starting with 6–9."
    return None


def validate_bio(bio: str) -> str | None:
    trimmed = bio.strip()
    if len(trimmed) < 1:
        return "Bio is required."
    if len(trimmed) > 500:
        return "Bio must be at most 500 characters."
    return None


def validate_message(message: str) -> str | None:
    trimmed = message.strip()
    if len(trimmed) < 1:
        return "Message is required."
    if len(trimmed) > 1000:
        return "Message must be at most 1000 characters."
    return None


def validate_rate_rupees(rate: int) -> str | None:
    if not isinstance(rate, int) or rate <= 0:
        return "Rate must be a whole number of rupees greater than zero."
    return None


def validate_years_experience(years: int) -> str | None:
    if not isinstance(years, int) or years < 0 or years > 60:
        return "Years of experience must be between 0 and 60."
    return None


def validate_city(city: str) -> str | None:
    trimmed = city.strip()
    if len(trimmed) < 1:
        return "City is required."
    if len(trimmed) > 80:
        return "City must be at most 80 characters."
    return None


def validate_display_name(name: str) -> str | None:
    trimmed = name.strip()
    if len(trimmed) < 1:
        return "Display name is required."
    if len(trimmed) > 80:
        return "Display name must be at most 80 characters."
    return None


def validate_club_name(hirer_kind: str | None, club_name: str | None) -> str | None:
    if hirer_kind != "club":
        return None
    trimmed = (club_name or "").strip()
    if len(trimmed) < 1:
        return "Club name is required for club hirers."
    if len(trimmed) > 120:
        return "Club name must be at most 120 characters."
    return None


def can_transition_hire_request_status(
    from_status: str, to_status: str, role: StatusTransitionRole
) -> bool:
    if from_status != "pending":
        return False
    if role == "coach":
        return to_status in ("accepted", "declined")
    if role == "hirer":
        return to_status == "withdrawn"
    return False


def whatsapp_url(mobile: str) -> str:
    digits = re.sub(r"\D", "", mobile)
    return f"https://wa.me/91{digits}"
