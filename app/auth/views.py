from django.contrib.auth.models import User
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
import json

""" signup view"""
@csrf_exempt
def signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')
        email = data.get('email')
        if not password or not email:
            return JsonResponse({'error': 'All fields required.'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists.'}, status=409)
        # ensure username is set (Django default User requires username)
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        return JsonResponse({'message': 'Signup successful.'}, status=201)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

"""Logout view that blacklists the refresh token"""
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
"""
IMPLEMENT A LOGIN VIEW THAT USES JWT AND CACHES USER DATA

Retrieve cached user data using ->  user_data = cache.get(f"user_login_{user.id}")
"""
@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        if user:
            # Issue JWT tokens
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)
            # Cache user data for 1 hour
            cache.set(f"user_login_{user.id}", {
                "email": user.email,
                "last_login": str(user.last_login),
            }, timeout=3600)
            return JsonResponse({
                'access': access,
                'refresh': str(refresh),
                'message': 'Login successful.'
            }, status=200)
        return JsonResponse({'error': 'Invalid credentials.'}, status=401)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)