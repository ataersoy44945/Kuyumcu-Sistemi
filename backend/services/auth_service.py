"""
AuthService — Kimlik doğrulama ve kullanıcı yönetimi iş mantığı.
Şifre hashleme, giriş doğrulama, kayıt ve oturum yönetimi burada yaşar.
"""

import hashlib
import hmac
import logging
import os
from typing import Optional

from backend.models.user import User
from backend.repositories.user_repository import UserRepository
from backend.utils.validators import (
    validate_username, validate_email, validate_password, validate_name,
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Kimlik doğrulama servisi.

    Şifreler PBKDF2-HMAC-SHA256 + rastgele salt ile saklanır.
    Oturum bilgisi (aktif kullanıcı) bu sınıfta tutulur.
    """

    _HASH_ITERATIONS = 100_000

    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository
        self._current_user: Optional[User] = None

    # ── Public Interface ───────────────────────────────────────

    def login(self, username: str, password: str) -> Optional[User]:
        """
        Kullanıcı adı ve şifre ile giriş yapar.
        Başarılıysa User döner, değilse None (genel hata; hangisinin yanlış
        olduğu kasıtlı olarak söylenmez).
        """
        user = self._repo.get_by_username(username.strip())
        if user is None:
            logger.info("Giriş denemesi — kullanıcı bulunamadı: %s", username)
            return None

        if not user.is_active:
            logger.info("Giriş denemesi — pasif hesap: %s", username)
            return None

        stored_hash = self._repo.get_password_hash(user.id)
        if not stored_hash or not self._verify_password(password, stored_hash):
            logger.info("Giriş denemesi — yanlış şifre: %s", username)
            return None

        self._repo.update_last_login(user.id)
        self._current_user = user
        logger.info("Giriş başarılı: %s (rol=%s)", username, user.role)
        return user

    def register(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
    ) -> User:
        """
        Yeni müşteri hesabı oluşturur.
        Doğrulama hatalarında ValidationError fırlatır.
        Kullanıcı adı/e-posta çakışmasında ValueError fırlatır.
        """
        # Doğrulama
        username   = validate_username(username)
        email      = validate_email(email)
        password   = validate_password(password)
        first_name = validate_name(first_name, "Ad")
        last_name  = validate_name(last_name, "Soyad")

        # Benzersizlik kontrolü
        if self._repo.get_by_username(username):
            raise ValueError("Bu kullanıcı adı zaten kullanılıyor.")
        if self._repo.get_by_email(email):
            raise ValueError("Bu e-posta adresi zaten kayıtlı.")

        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role="customer",
        )

        created = self._repo.create(new_user, self._hash_password(password))
        if created is None:
            raise RuntimeError("Kullanıcı oluşturulamadı.")

        logger.info("Yeni kayıt: %s (%s)", username, email)
        return created

    def logout(self) -> None:
        if self._current_user:
            logger.info("Çıkış: %s", self._current_user.username)
        self._current_user = None

    def get_current_user(self) -> Optional[User]:
        return self._current_user

    def is_logged_in(self) -> bool:
        return self._current_user is not None

    def register_admin(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> Optional[User]:
        """Yalnızca AppContext ilk kurulumunda varsayılan admin oluşturmak için."""
        new_user = User(
            username=username, email=email,
            first_name=first_name, last_name=last_name, role="admin",
        )
        return self._repo.create(new_user, self._hash_password(password))

    def admin_create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        role: str = "customer",
        is_active: bool = True,
    ) -> User:
        """
        Admin panelinden yeni kullanıcı oluşturur.
        Temel doğrulama yapılır, şifre min uzunluk kontrolü gevşektir (4+).
        Benzersizlik kontrollü.
        """
        username   = username.strip().lower()
        email      = email.strip().lower()
        first_name = first_name.strip()
        last_name  = last_name.strip()

        if len(username) < 3:
            raise ValueError("Kullanıcı adı en az 3 karakter olmalıdır.")
        if "@" not in email or "." not in email:
            raise ValueError("Geçerli bir e-posta adresi giriniz.")
        if len(password) < 4:
            raise ValueError("Şifre en az 4 karakter olmalıdır.")
        if not first_name or not last_name:
            raise ValueError("Ad ve soyad boş bırakılamaz.")
        if role not in ("admin", "customer"):
            raise ValueError("Rol 'admin' veya 'customer' olmalıdır.")

        if self._repo.get_by_username(username):
            raise ValueError("Bu kullanıcı adı zaten kullanılıyor.")
        if self._repo.get_by_email(email):
            raise ValueError("Bu e-posta adresi zaten kayıtlı.")

        new_user = User(
            username=username, email=email,
            first_name=first_name, last_name=last_name,
            phone=phone or None, role=role, is_active=is_active,
        )
        created = self._repo.create(new_user, self._hash_password(password))
        if created is None:
            raise RuntimeError("Kullanıcı oluşturulamadı.")

        logger.info("Admin yeni %s oluşturdu: %s", role, username)
        return created

    def set_user_active(self, user_id: int, active: bool) -> bool:
        """Admin panelinden kullanıcıyı engeller (False) / aktif eder (True)."""
        ok = self._repo.set_active(user_id, active)
        if ok:
            logger.info("Kullanıcı aktifliği değişti: id=%d → %s", user_id, active)
        return ok

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Mevcut şifreyi doğrulayarak yenisiyle değiştirir."""
        validate_password(new_password)

        stored_hash = self._repo.get_password_hash(user_id)
        if not stored_hash or not self._verify_password(old_password, stored_hash):
            return False

        return self._repo.update_password(user_id, self._hash_password(new_password))

    # ── Private ───────────────────────────────────────────────

    def _hash_password(self, password: str) -> str:
        """PBKDF2-HMAC-SHA256 ile şifreyi hashler. salt:key formatında döner."""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self._HASH_ITERATIONS
        )
        return salt.hex() + ":" + key.hex()

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt_hex, key_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            actual_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, self._HASH_ITERATIONS
            )
            # Zamanlama saldırısına karşı sabit zamanlı karşılaştırma
            return hmac.compare_digest(actual_key, expected_key)
        except (ValueError, AttributeError):
            return False
