"""
Signal handlers for loans app
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal

from .models import Loan, SecurityDeposit


@receiver(post_save, sender=Loan)
def create_security_deposit(sender, instance, created, **kwargs):
    """
    Automatically create SecurityDeposit record when a loan is approved
    """
    # Only create if loan is approved and doesn't have a security deposit yet
    if instance.status == 'approved':
        # Check if security deposit already exists
        if not hasattr(instance, 'security_deposit'):
            try:
                # Calculate 10% of principal
                required_amount = instance.principal_amount * Decimal('0.10')
                
                SecurityDeposit.objects.create(
                    loan=instance,
                    required_amount=required_amount,
                    paid_amount=instance.upfront_payment_paid or Decimal('0'),
                    payment_date=instance.upfront_payment_date,
                    is_verified=instance.upfront_payment_verified
                )
            except Exception as e:
                # Don't fail loan approval if deposit creation fails
                print(f"Error creating security deposit: {e}")


@receiver(pre_save, sender=Loan)
def calculate_upfront_payment(sender, instance, **kwargs):
    """
    Automatically calculate upfront payment requirement (10% of principal)
    """
    if instance.principal_amount and not instance.upfront_payment_required:
        instance.upfront_payment_required = instance.principal_amount * Decimal('0.10')
