# portal/settings.py
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ===== Security / ENV =====
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "CHANGE_ME_DEV_ONLY")
DEBUG = os.getenv("DEBUG", "0") == "1"

def _split_env(name: str):
    v = os.getenv(name, "")
    return [i.strip() for i in v.split(",") if i.strip()]

ALLOWED_HOSTS = _split_env("ALLOWED_HOSTS") or [".onrender.com", "127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = _split_env("CSRF_TRUSTED_ORIGINS") or ["https://*.onrender.com"]

# (เผื่อใช้ในอีเมล/ลิงก์)
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000")

# >>> อนุมัติผ่านอีเมลแบบไม่เช็คสิทธิ์ <<<
# views._perform_email_action จะอ่านค่านี้:
# ถ้า "0" หรือ falsey -> ไม่เช็คสิทธิ์ (one-click approve/reject)
# ถ้า "1" -> ต้องมีสิทธิ์ (หัวหน้าทีม/manager/staff) และ/หรือ login
APPROVAL_REQUIRE_PERMISSION = os.getenv("APPROVAL_REQUIRE_PERMISSION", "0")

# ===== Email (Anymail + SendGrid API) =====
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"

ANYMAIL = {
    "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY", ""),
}

# ต้องตรงกับ Single Sender ที่ยืนยันบน SendGrid
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "AccountWorks Portal <hr.accworks@gmail.com>",
)
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "20"))

# ===== Apps =====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "hr.apps.HrConfig",
    "anymail",
]

# ===== Middleware =====
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,  # จะปิดใน prod ด้านล่างเมื่อ DEBUG=False
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "hr.context_processors.role_flags",
            ],
        },
    },
]

WSGI_APPLICATION = "portal.wsgi.application"

# ===== Database =====
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR/'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=True if os.getenv("RENDER") else False,
    )
}

# ===== Password validators =====
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ===== I18N / TZ =====
LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

# ===== Static & Media =====
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ===== Auth redirects =====
LOGIN_URL = "auth:login"
LOGIN_REDIRECT_URL = "/home/"
LOGOUT_REDIRECT_URL = "auth:login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== Production hardening =====
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

    # cache template loaders
    TEMPLATES[0]["APP_DIRS"] = False
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        )
    ]

# ===== Logging =====
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django": {"handlers": ["console"], "level": "INFO"},
        "anymail": {"handlers": ["console"], "level": "INFO"},
    },
}
