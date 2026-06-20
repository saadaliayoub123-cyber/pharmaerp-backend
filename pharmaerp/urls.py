from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from pharmacy import auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("pharmacy.urls")),
    path("api/auth/login/", auth_views.login_view, name="login"),
    path("api/auth/me/", auth_views.me_view, name="me"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
