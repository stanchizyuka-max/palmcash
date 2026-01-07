"""
Signal handlers for payments app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

from .models import Payment, PaymentCollection
from loans.models import PaymentSchedule


@receiver(post_save, sender=Payment)
def update_payment_collection_from_payment(sender, instance, created, **kwargs):
    """
    Update PaymentCollection when a Payment is completed
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
            
            # Update corresponding payment schedule
            payment_schedule = PaymentSchedule.objects.filter(
                loan=instance.loan,
                due_date=collection_date
            ).first()
            
            if payment_schedule and not payment_schedule.is_paid:
                payment_schedule.is_paid = True
                payment_schedule.paid_date = collection_date
                payment_schedule.save()
                
        except Exception as e:
            print(f"Error updating payment collection from payment: {e}")
