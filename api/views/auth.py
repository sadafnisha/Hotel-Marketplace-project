"""
Authentication & "current user" endpoints.

Auth uses Django's built-in ``authenticate()`` / password hashing plus DRF's
TokenAuthentication (``rest_framework.authtoken``) for stateless API clients.
Session authentication (already used by the server-rendered site) also
continues to work for the API, so a browser that is logged in via the normal
Django login page can call the API directly too.
"""
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Public endpoint. Creates an Owner or Buyer account (role is required in
    the payload) plus the matching profile row, exactly like the existing
    /accounts/register/owner/ and /accounts/register/buyer/ forms. Passwords
    are validated with Django's AUTH_PASSWORD_VALIDATORS and stored using
    Django's built-in hashing -- never in plain text.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/  {"username": "...", "password": "..."}
    Public endpoint. Verifies credentials via Django's auth backend and
    returns an auth token plus the user's profile. Suspended (inactive)
    accounts are rejected, matching Django's normal login behaviour.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response(
                {'detail': 'username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'detail': 'This account has been suspended.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})


class LogoutView(APIView):
    """POST /api/auth/logout/ - invalidates the caller's current API token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/users/me/  - current authenticated user's profile
    PATCH /api/users/me/ - update own first/last name, email, phone
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
