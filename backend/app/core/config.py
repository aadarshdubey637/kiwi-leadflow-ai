import logging
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me"


class Settings(BaseSettings):
    """All configuration comes from environment variables / .env — nothing hardcoded."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LeadFlow AI"
    environment: str = "development"  # set to "production" to enforce a real JWT secret
    company_name: str = "Kiwi Connect Digital"
    database_url: str = "sqlite:///./leadflow.db"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Auth ---
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    password_hash_iterations: int = 600_000
    admin_username: str | None = None  # optional: seeds the first admin at startup
    admin_email: str | None = None
    admin_password: str | None = None

    # --- AI providers ---
    ai_primary_provider: str = "gemini"
    ai_fallback_provider: str | None = "groq"
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "openai/gpt-oss-120b"
    groq_reasoning_effort: str | None = "low"  # low | medium | high (only used by gpt-oss models)
    ai_timeout_seconds: float = 30.0
    ai_max_attempts: int = 3  # attempts per provider (transient errors / invalid output)
    ai_retry_backoff_seconds: float = 1.0
    ai_max_concurrency: int = 2  # simultaneous LLM calls across all enquiries
    ai_min_interval_seconds: float = 0.0  # spacing between LLM calls (e.g. 6 for a 10 requests/min free tier)
    # Tokens-per-minute budget per provider (free-tier defaults). The scheduler stays under these instead of
    # hitting HTTP 429. Override with AI_TPM_LIMITS='{"groq": 30000}' on a paid plan; use {} to disable.
    ai_tpm_limits: dict[str, int] = {"groq": 8000, "gemini": 250000}
    # Requests-per-minute budget per provider (free-tier defaults; Gemini 2.5 Flash free is ~10 RPM). {} disables.
    ai_rpm_limits: dict[str, int] = {"groq": 30, "gemini": 10}
    ai_capacity_skip_seconds: float = 3.0  # if the primary would have to wait longer than this, use the fallback instead
    ai_low_confidence_threshold: float = 0.5  # below this => manual review

    # --- Email (SMTP). Leave smtp_host empty to disable email features; nothing is faked. ---
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None  # e.g. "Kiwi Connect Digital <leads@yourdomain.com>"
    smtp_security: str = "starttls"  # starttls | ssl | none
    smtp_timeout_seconds: float = 15.0
    notify_email: str | None = None  # comma-separated team inboxes for hot / high-priority / needs-review alerts
    notify_all_enquiries: bool = False  # True = alert the team inboxes for every new enquiry
    frontend_url: str = "http://localhost:5173"  # used for deep links in notification emails

    # --- WhatsApp click-to-chat ---
    default_country_code: str = "91"  # prepended to 10-digit numbers saved without a country code

    # --- Business rules (configurable) ---
    hot_lead_threshold: int = 80
    warm_lead_threshold: int = 50
    duplicate_similarity_threshold: float = 0.85
    duplicate_lookback: int = 300
    # Rough FX table used ONLY to compare budgets in lead scoring (not for accounting).
    currency_to_inr: dict[str, float] = {"INR": 1, "USD": 83, "EUR": 90, "GBP": 105, "AED": 22.6}

    # --- Rate limiting (per client IP, per minute) ---
    rate_limit_enquiries_per_minute: int = 20
    rate_limit_login_per_minute: int = 10

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    @property
    def notify_emails(self) -> list[str]:
        return [e.strip() for e in (self.notify_email or "").split(",") if e.strip()]

    @model_validator(mode="after")
    def _check_secret(self):
        if self.jwt_secret == DEFAULT_JWT_SECRET:
            if self.environment == "production":
                raise ValueError("JWT_SECRET must be set to a strong value in production")
            logging.getLogger("leadflow").warning("Using default JWT secret — development only")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
