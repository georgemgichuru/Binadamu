from django.urls import path
from . import views


urlpatterns = [
    path('stkpush/', views.MpesaSTKPushView.as_view(), name='stkpush'),
    path("mpesa/callback/", views.mpesa_callback, name="mpesa_callback"),
]