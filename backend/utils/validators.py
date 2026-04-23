"""
Form ve veri doğrulama yardımcıları.
Servisler çağrılmadan önce kullanıcı girdisi burada doğrulanır.
"""

import re


class ValidationError(Exception):
    """Doğrulama hatası. UI bu exception'ı yakalayıp kullanıcıya gösterir."""
    pass


# ── Kullanıcı Alanları ────────────────────────────────────────

def validate_username(value: str) -> str:
    value = value.strip()
    if len(value) < 3:
        raise ValidationError("Kullanıcı adı en az 3 karakter olmalıdır.")
    if len(value) > 50:
        raise ValidationError("Kullanıcı adı en fazla 50 karakter olabilir.")
    if not re.match(r"^[a-zA-Z0-9_]+$", value):
        raise ValidationError("Kullanıcı adı yalnızca harf, rakam ve _ içerebilir.")
    return value


def validate_email(value: str) -> str:
    value = value.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, value):
        raise ValidationError("Geçerli bir e-posta adresi giriniz.")
    return value


def validate_password(value: str) -> str:
    if len(value) < 6:
        raise ValidationError("Şifre en az 6 karakter olmalıdır.")
    return value


def validate_name(value: str, field_label: str = "Alan") -> str:
    value = value.strip()
    if len(value) < 2:
        raise ValidationError(f"{field_label} en az 2 karakter olmalıdır.")
    if len(value) > 100:
        raise ValidationError(f"{field_label} en fazla 100 karakter olabilir.")
    return value


# ── Ürün Alanları ─────────────────────────────────────────────

def validate_positive_float(value: float, field_label: str = "Değer") -> float:
    if value <= 0:
        raise ValidationError(f"{field_label} sıfırdan büyük olmalıdır.")
    return value


def validate_non_negative_float(value: float, field_label: str = "Değer") -> float:
    if value < 0:
        raise ValidationError(f"{field_label} negatif olamaz.")
    return value


def validate_non_negative_int(value: int, field_label: str = "Değer") -> int:
    if value < 0:
        raise ValidationError(f"{field_label} negatif olamaz.")
    return value


def validate_karat(value: str) -> str:
    allowed = {"8", "14", "18", "21", "22", "24"}
    if value not in allowed:
        raise ValidationError(f"Geçersiz ayar: {value}. İzin verilenler: {', '.join(sorted(allowed))}")
    return value


def validate_profit_margin(value: float) -> float:
    if not (0 <= value <= 100):
        raise ValidationError("Kar marjı 0–100 arasında olmalıdır.")
    return value
