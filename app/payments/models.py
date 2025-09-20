from django.db import models
from django.contrib.auth.models import User

class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    # allow transactions without a Django user (callbacks or reconciliation)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='mpesa_transactions', null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    business_short_code = models.CharField(max_length=10)  # Till/Paybill
    account_reference = models.CharField(max_length=50)
    transaction_desc = models.CharField(max_length=100)

    # Safaricom request/response IDs
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    result_code = models.IntegerField(blank=True, null=True)  # from callback
    result_desc = models.TextField(blank=True, null=True)     # from callback

    # Payment confirmation
    mpesa_receipt_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)

    # Optional: store raw callback for debugging
    raw_callback = models.JSONField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} | {self.phone_number} | {self.amount} | {self.status}"