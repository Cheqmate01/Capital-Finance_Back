from django.db import models

# Create your models here.
class User(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    full_name = models.CharField(max_length=255)
    username = models.CharField(max_length=150, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    category = models.CharField(max_length=50, default='Regular User')
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.username


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("in", "In"),
        ("out", "Out"),
        ("Deposit", "Deposit"),
        ("Withdraw", "Withdraw"),
        ("Income", "Income"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    CURRENCY_CHOICES = [
        ("USD", "USD"),
        ("BTC", "BTC"),
        ("ETH", "ETH"),
        ("USDT", "USDT"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount} {self.currency}"
    

class Wallet(models.Model):
    CURRENCY_CHOICES = [
        ("BTC", "BTC"),
        ("ETH", "ETH"),
        ("USDT TRC20", "USDT TRC20"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.currency}"
    

class Balance(models.Model):
    CURRENCY_CHOICES = [
        ("USD", "USD"),
        ("BTC", "BTC"),
        ("ETH", "ETH"),
        ("USDT", "USDT"),
        ("USDT TRC20", "USDT TRC20"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="balances")
    currency = models.CharField(max_length=20, choices=CURRENCY_CHOICES)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.currency}: {self.balance}"
    

# Daily balance snapshot for historical graphing
class BalanceSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="balance_snapshots")
    currency = models.CharField(max_length=20)
    date = models.DateField()
    balance = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = ("user", "currency", "date")
        ordering = ["user", "currency", "date"]

    def __str__(self):
        return f"{self.user.username} {self.currency} {self.date}: {self.balance}"


class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    quote = models.TextField()
    client = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.client}: {self.quote[:50]}..."
