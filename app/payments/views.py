from rest_framework import generics
from .models import MpesaTransaction
from .serializers import MpesaTransactionSerializer
from django.http import HttpResponse, JsonResponse
from django_daraja.mpesa.core import MpesaClient
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
from rest_framework.views import APIView
from rest_framework import permissions

# List and create Mpesa STK Push transactions
class MpesaTransactionListCreateView(generics.ListCreateAPIView):
    queryset = MpesaTransaction.objects.all()
    serializer_class = MpesaTransactionSerializer

# Retrieve and update a specific Mpesa STK Push transaction by id
class MpesaTransactionDetailView(generics.RetrieveUpdateAPIView):
    queryset = MpesaTransaction.objects.all()
    serializer_class = MpesaTransactionSerializer
    lookup_field = 'id'

# New: API view to initiate STK Push requests
class MpesaSTKPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Expects JSON: { "phone_number": "2547...", "amount": 100, "account_reference": "Ref", "transaction_desc": "Desc" }
        Creates a pending MpesaTransaction and triggers an STK push via MpesaClient.
        """
        data = request.data
        phone_number = data.get("phone_number", "254712345678")
        amount = data.get("amount", 1)
        account_reference = data.get("account_reference", "Test123")
        transaction_desc = data.get("transaction_desc", "Payment")
        callback_url = data.get("callback_url", "https://yourdomain.com/callback")

        # create initial transaction record (status Pending)
        txn = MpesaTransaction.objects.create(
            user=request.user,
            phone_number=phone_number,
            amount=amount,
            business_short_code='',  # optional: fill if available
            account_reference=account_reference,
            transaction_desc=transaction_desc,
            status='Pending',
            raw_callback=None
        )

        cl = MpesaClient()
        try:
            response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
            # return JSON-compatible response to caller
            if isinstance(response, (dict, list)):
                return JsonResponse(response, safe=False)
            # if it's an object/stringify
            return HttpResponse(json.dumps(response), content_type="application/json")
        except Exception as e:
            # minimal error handling
            return JsonResponse({"error": str(e)}, status=500)


def MpesaTransactionView(request):
    cl = MpesaClient()
    phone_number = '254712345678'
    amount = 1
    account_reference = 'Test123'
    transaction_desc = 'Payment for X'
    callback_url = 'https://yourdomain.com/callback'
    
    response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
    # ensure response is returned as JSON
    if isinstance(response, (dict, list)):
        return JsonResponse(response, safe=False)
    return HttpResponse(json.dumps(response), content_type="application/json")


@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body.decode('utf-8'))

    # Navigate to the "Body.stkCallback" section
    stk_callback = data.get("Body", {}).get("stkCallback", {})

    merchant_request_id = stk_callback.get("MerchantRequestID")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    # Save raw callback for debugging
    raw_payload = data

    # Only process if we have callback details
    if checkout_request_id is None and merchant_request_id is None:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Missing identifiers"}, status=400)

    # Extract metadata
    callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", []) if result_code == 0 else []
    mpesa_data = {item.get("Name"): item.get("Value") for item in callback_metadata if "Name" in item}

    # Parse transaction date safely
    txn_date_val = mpesa_data.get("TransactionDate")
    txn_date = None
    if txn_date_val:
        try:
            txn_date = datetime.strptime(str(txn_date_val), "%Y%m%d%H%M%S")
        except Exception:
            txn_date = None

    # Try to find an existing transaction by checkout_request_id first
    txn = None
    if checkout_request_id:
        txn = MpesaTransaction.objects.filter(checkout_request_id=checkout_request_id).first()

    # If not found, try to match by phone_number + amount + Pending status (best effort)
    if not txn and mpesa_data:
        phone = mpesa_data.get("PhoneNumber")
        amount = mpesa_data.get("Amount")
        if phone and amount is not None:
            txn = MpesaTransaction.objects.filter(
                phone_number=str(phone),
                amount=amount,
                status='Pending'
            ).order_by('-created_at').first()

    # If we have a matching transaction update it
    if txn:
        txn.merchant_request_id = merchant_request_id or txn.merchant_request_id
        txn.checkout_request_id = checkout_request_id or txn.checkout_request_id
        txn.result_code = result_code
        txn.result_desc = result_desc
        txn.amount = mpesa_data.get("Amount") or txn.amount
        txn.mpesa_receipt_number = mpesa_data.get("MpesaReceiptNumber") or txn.mpesa_receipt_number
        txn.transaction_date = txn_date or txn.transaction_date
        txn.phone_number = mpesa_data.get("PhoneNumber") or txn.phone_number
        txn.raw_callback = raw_payload
        txn.status = "Success" if result_code == 0 else "Failed"
        txn.save()
    else:
        # No matching transaction found; create one now that 'user' can be null.
        try:
            MpesaTransaction.objects.create(
                user=None,
                phone_number=mpesa_data.get("PhoneNumber") or '',
                amount=mpesa_data.get("Amount") or 0,
                business_short_code='',
                account_reference='',
                transaction_desc='Callback created',
                merchant_request_id=merchant_request_id,
                checkout_request_id=checkout_request_id,
                result_code=result_code,
                result_desc=result_desc,
                mpesa_receipt_number=mpesa_data.get("MpesaReceiptNumber"),
                transaction_date=txn_date,
                raw_callback=raw_payload,
                status="Success" if result_code == 0 else "Failed",
            )
        except Exception:
            # keep silent; optionally add logging here
            pass

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


