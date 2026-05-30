"""
Signal handlers for payments app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

from .models import Payment, PaymentCollection, PaymentSchedule


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
    NOTE: This signal is kept for backward compatibility but payment schedule
    distribution is primarily handled by distribute_payment() in services.py
    """
    if instance.status == 'completed' and instance.collected_amount > 0:
        try:
            # Find the corresponding payment schedule by due date
            payment_schedule = PaymentSchedule.objects.filter(
                loan=instance.loan,
                due_date=instance.collection_date
            ).first()
            
            # Only mark as paid if the full amount was collected
            # Partial payments are handled by distribute_payment()
            if payment_schedule and not payment_schedule.is_paid:
                if instance.collected_amount >= payment_schedule.total_amount:
                    payment_schedule.is_paid = True
                    payment_schedule.paid_date = instance.collection_date
                    payment_schedule.amount_paid = payment_schedule.total_amount
                    payment_schedule.save()
        except Exception as e:
            print(f"Error updating payment schedule: {e}")


@receiver(post_save, sender=Payment)
def update_payment_collection_from_payment(sender, instance, created, **kwargs):
    """
    Update PaymentCollection when a Payment is completed
    NOTE: Payment schedule distribution is handled by distribute_payment() in services.py
    This signal only updates the PaymentCollection record for tracking purposes
    """
    if instance.status == 'completed':
        try:
            # Find or create PaymentCollection for this payment date
            collection_date = instance.payment_date.date()
            collection, created = PaymentCollection.objects.get_or_create(
                loan=instance.loan,
                collection_date=collection_date,
                defaults={
                    'expected_amount': instance.amount,
                    'collected_amount': Decimal('0'),
                    'status': 'scheduled'
                }
            )
            
            # Update collection with payment details
            collection.collected_amount = instance.amount
            collection.collected_by = instance.processed_by
            collection.actual_collection_date = instance.payment_date
            collection.status = 'completed'
            collection.is_partial = instance.amount < collection.expected_amount
            
            # Update expected amount if this is a new collection
            if created:
                collection.expected_amount = instance.amount
            
            collection.save()
            
            # DO NOT mark payment schedules here - that's handled by distribute_payment()
            # in payments/services.py which correctly distributes payments across schedules
            # in order, handling partial payments and overpayments properly
                
        except Exception as e:
            print(f"Error updating payment collection from payment: {e}")
