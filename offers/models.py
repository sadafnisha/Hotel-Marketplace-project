from django.conf import settings
from django.db import models

from listings.models import HotelListing


class Offer(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COUNTERED = 'countered', 'Countered'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        CLOSED = 'closed', 'Closed'

    listing = models.ForeignKey(HotelListing, on_delete=models.CASCADE, related_name='offers')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers_made')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers_received')

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    proposed_terms = models.TextField(blank=True)
    message = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Offer #{self.pk} on {self.listing.title} by {self.buyer}"

    def record_history(self, actor, action, amount=None, message=''):
        OfferHistory.objects.create(
            offer=self, actor=actor, action=action,
            amount=amount if amount is not None else self.amount,
            message=message,
        )


class OfferHistory(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.action} on Offer #{self.offer_id} by {self.actor}"
