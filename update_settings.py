import re

f = "pharmaerp/settings.py"
c = open(f, encoding="utf-8").read()

if "pharmacy" not in c:
    c = c.replace(
        "'django.contrib.staticfiles',",
        "'django.contrib.staticfiles',\n    'rest_framework',\n    'corsheaders',\n    'pharmacy',"
    )

if "corsheaders.middleware" not in c:
    c = c.replace(
        "'django.middleware.security.SecurityMiddleware',",
        "'corsheaders.middleware.CorsMiddleware',\n    'django.middleware.security.SecurityMiddleware',"
    )

if "CORS_ALLOWED_ORIGINS" not in c:
    c += """

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}
"""

open(f, "w", encoding="utf-8").write(c)
print("settings.py updated!")
