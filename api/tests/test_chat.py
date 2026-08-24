from rest_framework import status

from chat.models import Conversation, Message
from .base import ApiTestBase


class ConversationTests(ApiTestBase):
    def test_owner_cannot_start_conversation(self):
        self.auth_as(self.owner)
        resp = self.client.post('/api/conversations/', {'listing': self.published_listing.pk})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_buyer_can_start_conversation(self):
        self.auth_as(self.buyer)
        resp = self.client.post('/api/conversations/', {'listing': self.published_listing.pk})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertTrue(
            Conversation.objects.filter(
                listing=self.published_listing, buyer=self.buyer, owner=self.owner
            ).exists()
        )

    def test_starting_conversation_twice_reuses_existing_thread(self):
        self.auth_as(self.buyer)
        first = self.client.post('/api/conversations/', {'listing': self.published_listing.pk})
        second = self.client.post('/api/conversations/', {'listing': self.published_listing.pk})
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(Conversation.objects.count(), 1)

    def test_only_participants_can_view_conversation(self):
        convo = Conversation.objects.create(
            listing=self.published_listing, buyer=self.buyer, owner=self.owner
        )
        # Non-participants get a 404 rather than a 403: the queryset itself is
        # scoped to the caller's own conversations, so a stranger's thread
        # isn't even visible to look up -- this avoids leaking its existence.
        self.auth_as(self.other_buyer)
        resp = self.client.get(f'/api/conversations/{convo.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        self.auth_as(self.other_owner)
        resp = self.client.get(f'/api/conversations/{convo.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        self.auth_as(self.buyer)
        resp = self.client.get(f'/api/conversations/{convo.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.auth_as(self.owner)
        resp = self.client.get(f'/api/conversations/{convo.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_participant_can_send_message(self):
        convo = Conversation.objects.create(
            listing=self.published_listing, buyer=self.buyer, owner=self.owner
        )
        self.auth_as(self.buyer)
        resp = self.client.post(f'/api/conversations/{convo.pk}/messages/', {'body': 'Hello, is this available?'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(Message.objects.filter(conversation=convo, sender=self.buyer).count(), 1)

    def test_non_participant_cannot_send_message(self):
        convo = Conversation.objects.create(
            listing=self.published_listing, buyer=self.buyer, owner=self.owner
        )
        self.auth_as(self.other_buyer)
        resp = self.client.post(f'/api/conversations/{convo.pk}/messages/', {'body': 'Sneaky message'})
        # Not visible to this user at all -> 404, same reasoning as above.
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Message.objects.filter(conversation=convo).count(), 0)

    def test_viewing_conversation_marks_other_partys_messages_read(self):
        convo = Conversation.objects.create(
            listing=self.published_listing, buyer=self.buyer, owner=self.owner
        )
        Message.objects.create(conversation=convo, sender=self.buyer, body='Hi there')

        self.auth_as(self.owner)
        self.client.get(f'/api/conversations/{convo.pk}/')
        msg = Message.objects.get(conversation=convo, sender=self.buyer)
        self.assertIsNotNone(msg.read_at)

    def test_inbox_only_shows_own_conversations(self):
        Conversation.objects.create(listing=self.published_listing, buyer=self.buyer, owner=self.owner)
        self.auth_as(self.other_buyer)
        resp = self.client.get('/api/conversations/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 0)
