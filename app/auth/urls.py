from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from auth import views

# URL patterns for authentication endpoints.
# - signup: create a new user account
# - login: custom login view that issues JWTs and may cache user data
# - logout: view that blacklists refresh tokens (Simple JWT)
# - api/token/: built-in Simple JWT view to obtain access and refresh tokens
# - api/token/refresh/: built-in Simple JWT view to refresh access tokens
urlpatterns = [
    path('signup/', views.signup),      # POST: register new user
    path('login/', views.login),        # POST: authenticate & return JWTs
    path('logout/', views.LogoutView.as_view()), # POST: blacklist refresh token (logout)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # POST: obtain tokens
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # POST: refresh access token
]