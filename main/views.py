from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.
from .models import User, Transaction, Wallet, Balance, BalanceSnapshot, FAQ, Testimonial
from .serializers import UserSerializer, TransactionSerializer, WalletSerializer, BalanceSerializer, BalanceSnapshotSerializer, FAQSerializer, TestimonialSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.none()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Transaction.objects.filter(user=user)
        return Transaction.objects.none()


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.none()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Wallet.objects.filter(user=user)
        return Wallet.objects.none()
	

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
    queryset = FAQ.objects.none()
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return FAQ.objects.all()  # Or filter by user if needed
        return FAQ.objects.none()


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.none()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Testimonial.objects.all()  # Or filter by user if needed
        return Testimonial.objects.none()



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
    full_name = data.get("full_name")
    username = data.get("username")
    password = data.get("password")
    email = data.get("email", "")  # Optional
    if not full_name or not username or not password:
        return Response({"detail": "Full name, username, and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({"detail": "Username already registered."}, status=status.HTTP_400_BAD_REQUEST)
    if email and User.objects.filter(email=email).exists():
        return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(
        username=username,
        password=password,
        full_name=full_name,
        email=email
    )
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
    }, status=status.HTTP_201_CREATED)
