from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status, viewsets

# Create your views here.
from .models import User, Transaction, Wallet, Balance, BalanceSnapshot, FAQ, Testimonial
from .serializers import UserSerializer, TransactionSerializer, WalletSerializer, BalanceSerializer, BalanceSnapshotSerializer, FAQSerializer, TestimonialSerializer

class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer


class TransactionViewSet(viewsets.ModelViewSet):
	queryset = Transaction.objects.all()
	serializer_class = TransactionSerializer


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
	

class BalanceViewSet(viewsets.ModelViewSet):
    queryset = Balance.objects.all()
    serializer_class = BalanceSerializer


from rest_framework.permissions import IsAuthenticated

class BalanceSnapshotViewSet(viewsets.ModelViewSet):
    queryset = BalanceSnapshot.objects.all()
    serializer_class = BalanceSnapshotSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def daily(self, request):
        # Example hardcoded rates; replace with live rates as needed
        rates = {
            'USD': 1.0,
            'BTC': 65000.0,      # 1 BTC = 65,000 USD
            'ETH': 3500.0,       # 1 ETH = 3,500 USD
            'USDT': 1.0,         # 1 USDT = 1 USD
            'USDT TRC20': 1.0,   # 1 USDT TRC20 = 1 USD
        }
        qs = self.get_queryset().filter(user=request.user).order_by('date')
        from collections import defaultdict
        date_totals = defaultdict(float)
        for s in qs:
            rate = rates.get(s.currency, 1.0)
            usd_value = float(s.balance) * rate
            date_totals[s.date] += usd_value
        data = [
            {'date': str(date), 'balance': total}
            for date, total in sorted(date_totals.items())
        ]
        return Response(data)


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer


# Custom login endpoint
@api_view(["POST"])
def login_view(request):
    data = request.data
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return Response({"detail": "Email and password required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    # Compare password (assuming password_hash stores a hashed password)
    if check_password(password, user.password_hash):
        # You can return user info or a token here
        return Response({"detail": "Login successful", "user_id": user.id, "email": user.email, "username": user.username})
    else:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    

# Custom signup endpoint
@api_view(["POST"])

def signup_view(request):
    data = request.data
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    if not full_name or not email or not password:
        return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)
    # Generate a unique username
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    # Hash the password
    hashed_password = make_password(password)
    user = User.objects.create(
        full_name=full_name,
        email=email,
        password_hash=hashed_password,
        username=username
    )
    # Optionally, generate a token here if you want to return one
    return Response({
        "detail": "Signup successful",
        "user_id": user.id,
        "email": user.email,
        "username": user.username
    }, status=status.HTTP_201_CREATED)
