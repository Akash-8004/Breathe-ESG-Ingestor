"""
Auth views — Login (returns token) and Logout (deletes token).
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import LoginSerializer, UserSerializer


class LoginView(APIView):
    """POST /api/auth/login/ — Authenticate and return token + user info."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/logout/ — Delete the user's auth token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response(
            {'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK,
        )
