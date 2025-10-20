from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TransactionViewSet, BalanceViewSet, BalanceSnapshotViewSet, FAQViewSet, TestimonialViewSet, login_view, signup_view, deposit_wallets, profile_view

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'balances', BalanceViewSet)
router.register(r'faqs', FAQViewSet)
router.register(r'testimonials', TestimonialViewSet)

urlpatterns = [
    path('portfolio-value-daily/', BalanceSnapshotViewSet.as_view({'get': 'daily'}), name='portfolio-value-daily'),
    path('', include(router.urls)),
    path('auth/login', login_view, name='login'),
    path('auth/signup', signup_view, name='signup'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('deposit-wallets/', deposit_wallets, name='deposit-wallets'),
    path('profile/', profile_view, name='profile'),
]
