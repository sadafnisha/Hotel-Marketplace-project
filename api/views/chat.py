"""
Conversations & Messages API.

Business rules enforced here mirror chat/views.py exactly:
  * Only Buyers can start a conversation with a listing's Owner.
  * A conversation is unique per (listing, buyer, owner) -- starting it again
    just returns the existing thread (get_or_create).
  * Only the two participants (or an admin) may view a conversation or post
    messages into it.
  * Opening a conversation marks the other party's messages as read, exactly
    like chat.views.conversation_detail.
"""
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from chat.models import Conversation
from api.permissions import IsBuyerRole, IsConversationParticipantOrAdmin
from api.serializers import (
    ConversationSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    /api/conversations/               GET (inbox: conversations where caller is buyer or owner)
                                       POST {"listing": <id>} (buyer only) - start/reuse a conversation
    /api/conversations/{id}/          GET (participant/admin) - thread + messages, marks unread as read
    /api/conversations/{id}/messages/ POST {"body": "..."} - send a message into the thread
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsBuyerRole()]
        if self.action in ('retrieve', 'send_message'):
            return [permissions.IsAuthenticated(), IsConversationParticipantOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Conversation.objects.select_related('listing', 'buyer', 'owner').prefetch_related('messages')
        if user.is_platform_admin:
            return qs
        return qs.filter(Q(buyer=user) | Q(owner=user)).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        out = ConversationDetailSerializer(conversation, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        conversation = self.get_object()
        # Mark the other party's messages as read, exactly like chat.views.conversation_detail.
        conversation.messages.exclude(sender=request.user).filter(read_at__isnull=True).update(
            read_at=timezone.now()
        )
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='messages')
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation, sender=request.user)
        conversation.save()  # bumps `updated_at` so the inbox re-sorts, matching the template view
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
