from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TransactionViewSet, WalletViewSet, BalanceViewSet, BalanceSnapshotViewSet, FAQViewSet, TestimonialViewSet, login_view, signup_view

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'wallets', WalletViewSet)
router.register(r'balances', BalanceViewSet)
router.register(r'faqs', FAQViewSet)
router.register(r'testimonials', TestimonialViewSet)
router.register(r'balance-snapshots', BalanceSnapshotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login', login_view, name='login'),
    path('auth/signup', signup_view, name='signup'),
]
