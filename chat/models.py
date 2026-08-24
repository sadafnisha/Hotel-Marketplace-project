from django.conf import settings
from django.db import models

from listings.models import HotelListing


class Conversation(models.Model):
    listing = models.ForeignKey(HotelListing, on_delete=models.CASCADE, related_name='conversations')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_buyer')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations_as_owner')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('listing', 'buyer', 'owner')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation on {self.listing.title} ({self.buyer} <-> {self.owner})"

    def other_party(self, user):
        return self.owner if user == self.buyer else self.buyer

    def unread_count_for(self, user):
        return self.messages.exclude(sender=user).filter(read_at__isnull=True).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} in conversation #{self.conversation_id}"
