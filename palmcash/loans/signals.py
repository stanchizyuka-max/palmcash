"""
Signal handlers for loans app
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal

from .models import Loan, SecurityDeposit
from payments.models import PaymentCollection, PaymentSchedule


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


@receiver(post_save, sender=PaymentSchedule)
def create_payment_collection(sender, instance, created, **kwargs):
    """
    Automatically create PaymentCollection record when a payment schedule is created
    """
    if created:
        try:
            # Check if PaymentCollection already exists for this loan and date
            existing_collection = PaymentCollection.objects.filter(
                loan=instance.loan,
                collection_date=instance.due_date
            ).first()
            
            if not existing_collection:
                PaymentCollection.objects.create(
                    loan=instance.loan,
                    collection_date=instance.due_date,
                    expected_amount=instance.total_amount,
                    collected_amount=Decimal('0'),
                    status='scheduled'
                )
        except Exception as e:
            print(f"Error creating payment collection: {e}")


@receiver(post_save, sender=PaymentCollection)
def update_payment_schedule(sender, instance, **kwargs):
    """
    Update PaymentSchedule when PaymentCollection is marked as completed
    """
    if instance.status == 'completed' and instance.collected_amount > 0:
        try:
            # Find the corresponding payment schedule
            payment_schedule = PaymentSchedule.objects.filter(
                loan=instance.loan,
                due_date=instance.collection_date
            ).first()
            
            if payment_schedule and not payment_schedule.is_paid:
                # Mark the payment schedule as paid
                payment_schedule.is_paid = True
                payment_schedule.paid_date = instance.collection_date
                payment_schedule.save()
        except Exception as e:
            print(f"Error updating payment schedule: {e}")
