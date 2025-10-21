from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view, action, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.cache import cache
import re
import logging

# Create your views here.
from .models import User, Transaction, Balance, BalanceSnapshot, FAQ, Testimonial
from .serializers import UserSerializer, TransactionSerializer, BalanceSerializer, BalanceSnapshotSerializer, FAQSerializer, TestimonialSerializer
from .email_utils import send_signup_email, send_deposit_email, send_withdrawal_email
import os
from collections import defaultdict
import datetime

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer


# Simple profile endpoint for the current authenticated user. This accepts
# JSON and multipart/form-data (so the client can PATCH with a FormData
# containing an image) and always returns JSON responses.
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_view(request):
    user = request.user
    logging.getLogger(__name__).debug('profile_view called: method=%s user=%s content_type=%s files=%s data_keys=%s',
                                      request.method, getattr(user, 'id', None), request.META.get('CONTENT_TYPE'),
                                      list(request.FILES.keys()), list(request.data.keys() if hasattr(request, 'data') else []))
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    # PATCH - allow partial updates including file uploads
    # If a file was uploaded (multipart/form-data), assign it directly to
    # the user instance first so ImageField handles the UploadedFile object.
    if request.FILES and 'profile_picture' in request.FILES:
        user.profile_picture = request.FILES['profile_picture']
        # Save early so serializer doesn't try to re-validate the file content
        user.save()

    # For other fields, use the serializer for a partial update
    # Exclude file fields from serializer data to avoid double-processing.
    # If the client sends a 'profile_picture' value as a string (URL/path),
    # treat it as non-file and do not pass it to the ImageField validator.
    data = {k: v for k, v in request.data.items() if k not in request.FILES and k != 'profile_picture'}
    # If client sends an empty string for date_of_birth, drop it so the
    # DateField validator doesn't attempt to parse an empty string and fail.
    dob_key = 'date_of_birth'
    if dob_key in data:
        val = data.get(dob_key)
        if val is None or (isinstance(val, str) and val.strip() == ''):
            data.pop(dob_key, None)
    serializer = UserSerializer(user, data=data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        logging.getLogger(__name__).info('profile updated for user=%s', getattr(user, 'id', None))
        return Response(serializer.data)

    logging.getLogger(__name__).warning('profile update failed for user=%s errors=%s', getattr(user, 'id', None), serializer.errors)
    # Normalize error response to include a human-friendly message and structured errors
    errors = serializer.errors
    parts = []
    try:
        for field, msgs in errors.items():
            if isinstance(msgs, (list, tuple)):
                msg = ', '.join(str(m) for m in msgs)
            else:
                msg = str(msgs)
            parts.append(f"{field}: {msg}")
    except Exception:
        parts = [str(errors)]
    message = '; '.join(parts) if parts else 'Validation error'
    return Response({
        'detail': 'Validation failed',
        'errors': errors,
        'message': message,
    }, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.none()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Transaction.objects.filter(user=user)
        return Transaction.objects.none()
    
    def perform_create(self, serializer):
        transaction = serializer.save(user=self.request.user)
        # Check transaction type and send email accordingly
        if transaction.type.lower() == 'deposit':
            send_deposit_email(self.request.user, transaction)
        elif transaction.type.lower() == 'withdrawal':
            send_withdrawal_email(self.request.user, transaction)
	

class BalanceViewSet(viewsets.ModelViewSet):
    queryset = Balance.objects.none()
    serializer_class = BalanceSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Balance.objects.filter(user=user)
        return Balance.objects.none()


class BalanceSnapshotViewSet(viewsets.ModelViewSet):
    queryset = BalanceSnapshot.objects.all()
    serializer_class = BalanceSnapshotSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def daily(self, request):
        # Cache key per user to avoid recomputing on every request.
        cache_key = f"portfolio_value_daily_user_{request.user.id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        # Example hardcoded rates; replace with live rates as needed
        rates = {
            'USD': 1.0,
            'BTC': 65000.0,      # 1 BTC = 65,000 USD
            'ETH': 3500.0,       # 1 ETH = 3,500 USD
            'USDT': 1.0,         # 1 USDT = 1 USD
            'USDT TRC20': 1.0,   # 1 USDT TRC20 = 1 USD
        }
        
        transactions = Transaction.objects.filter(user=request.user).order_by('created_at')
        
        if not transactions.exists():
            return Response([{'date': datetime.date.today().isoformat(), 'total_balance_usd': 0}])

        daily_balances = defaultdict(float)
        
        for tx in transactions:
            rate = rates.get(tx.currency, 1.0) # Default to 1.0 if currency not in rates
            amount_usd = float(tx.amount) * rate
            
            date_key = tx.created_at.date()

            if tx.type.lower() == 'deposit':
                daily_balances[date_key] += amount_usd
            elif tx.type.lower() == 'withdrawal':
                daily_balances[date_key] -= amount_usd
            
        # Create a sorted list of dates and fill gaps
        sorted_dates = sorted(daily_balances.keys())
        
        all_dates_balances = []
        cumulative_balance = 0
        current_date = sorted_dates[0]
        end_date = datetime.date.today()

        while current_date <= end_date:
            # Add the day's net change to the cumulative balance
            cumulative_balance += daily_balances.get(current_date, 0)
            
            all_dates_balances.append({
                'date': current_date.isoformat(),
                'total_balance_usd': cumulative_balance
            })
            current_date += datetime.timedelta(days=1)

        # Cache computed result for a short time (e.g., 60 seconds)
        cache.set(cache_key, all_dates_balances, timeout=60)
        return Response(all_dates_balances)


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        return FAQ.objects.all()


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        return Testimonial.objects.all()


# Custom login endpoint
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return Response({"detail": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    refresh = RefreshToken.for_user(user)
    return Response({
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
        },
        "token": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    }, status=status.HTTP_200_OK)
    


# Custom signup endpoint
@api_view(["POST"])
@permission_classes([AllowAny])
def signup_view(request):
    data = request.data
    full_name = (data.get("full_name") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password")
    email = (data.get("email") or "").strip()  # Optional but validated if provided
    phone = (data.get("phone") or "").strip()  # Optional; requires model support to persist

    if not full_name or not username or not password:
        return Response({"detail": "Full name, username, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "Username already registered."}, status=status.HTTP_400_BAD_REQUEST)

    # Validate email if provided
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return Response({"detail": "Invalid email address."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

    # Basic phone validation (E.164-like, 7-15 digits, optional leading +)
    if phone:
        if not re.match(r'^\+?[0-9]{7,15}$', phone):
            return Response({"detail": "Invalid phone number format."}, status=status.HTTP_400_BAD_REQUEST)
        # If your User model has a phone field, check uniqueness
        if hasattr(User, 'phone') and User.objects.filter(phone=phone).exists():
            return Response({"detail": "Phone number already registered."}, status=status.HTTP_400_BAD_REQUEST)

    # Build create_user kwargs and only include phone if model supports it
    create_kwargs = {
        "username": username,
        "password": password,
        "full_name": full_name,
        "email": email,
    }
    if phone and hasattr(User, 'phone'):
        create_kwargs['phone'] = phone

    user = User.objects.create_user(**create_kwargs)

    # Send welcome email after user is created; do not block signup if email sending fails
    if user.email:
        try:
            send_signup_email(user)
        except Exception:
            logging.exception("Failed to send signup email to %s", user.email)

    refresh = RefreshToken.for_user(user)
    resp_user = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
    }
    if hasattr(user, 'phone'):
        resp_user['phone'] = getattr(user, 'phone', None)

    return Response({
        "user": resp_user,
        "token": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    }, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deposit_wallets(request):
    """
    Provides a list of company deposit wallet addresses from environment variables.
    """
    wallets = [
        {
            "id": 1,
            "currency": "BTC",
            "address": os.getenv("BTC_DEPOSIT_ADDRESS", "Address not configured"),
        },
        {
            "id": 2,
            "currency": "ETH",
            "address": os.getenv("ETH_DEPOSIT_ADDRESS", "Address not configured"),
        },
        {
            "id": 3,
            "currency": "USDT TRC20",
            "address": os.getenv("USDT_TRC20_DEPOSIT_ADDRESS", "Address not configured"),
        },
    ]
    return Response(wallets)