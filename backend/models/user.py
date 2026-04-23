from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Sistemdeki tüm kullanıcıları (admin + müşteri) temsil eder."""

    username:   str
    email:      str
    first_name: str
    last_name:  str

    id:            Optional[int] = None
    role:          str  = "customer"   # "admin" | "customer"
    phone:         Optional[str] = None
    is_active:     bool = True
    password_hash: str  = ""
    created_at:    str  = ""
    updated_at:    str  = ""
    last_login_at: Optional[str] = None

    # ── Derived ────────────────────────────────────────────────

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_admin(self) -> bool:
        return self.role == "admin"

    def display_role(self) -> str:
        return "Yönetici" if self.is_admin() else "Müşteri"
