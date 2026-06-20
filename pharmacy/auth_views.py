from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Login endpoint - retourne JWT tokens"""
    username = request.data.get("username") or request.data.get("email", "").split("@")[0]
    password = request.data.get("password")
    
    if not username or not password:
        return Response(
            {"error": "Username et password requis"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        # Try with email
        try:
            user_obj = User.objects.get(email=request.data.get("email"))
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
    
    if user is None:
        return Response(
            {"error": "Identifiants incorrects"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    refresh = RefreshToken.for_user(user)
    
    # Determine role based on groups/permissions
    role = "Caissier"
    if user.is_superuser:
        role = "Administrateur"
    elif user.is_staff:
        role = "Pharmacien"
    elif user.groups.filter(name="Pharmacien").exists():
        role = "Pharmacien"
    elif user.groups.filter(name="ResponsableDepot").exists():
        role = "ResponsableDepot"
    
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nom": user.last_name or user.username,
            "prenom": user.first_name,
            "role": role,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        }
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Get current user info"""
    user = request.user
    role = "Caissier"
    if user.is_superuser:
        role = "Administrateur"
    elif user.is_staff:
        role = "Pharmacien"
    
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nom": user.last_name or user.username,
        "prenom": user.first_name,
        "role": role,
    })

