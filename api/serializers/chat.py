from rest_framework import serializers

from chat.models import Conversation, Message
from .accounts import PublicUserSerializer
from .listings import HotelListingListSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'body', 'read_at', 'created_at']
        read_only_fields = ['id', 'conversation', 'sender', 'read_at', 'created_at']

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('Message body cannot be empty.')
        return value


class ConversationSerializer(serializers.ModelSerializer):
    """Lightweight representation used for the inbox list endpoint."""
    buyer = PublicUserSerializer(read_only=True)
    owner = PublicUserSerializer(read_only=True)
    listing_detail = HotelListingListSerializer(source='listing', read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'listing', 'listing_detail', 'buyer', 'owner',
            'unread_count', 'last_message', 'created_at', 'updated_at',
        ]

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.unread_count_for(user)

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return MessageSerializer(last).data if last else None


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Starts (or reuses) a conversation between the authenticated Buyer and
    a listing's Owner, mirroring chat.views.start_conversation.
    """

    class Meta:
        model = Conversation
        fields = ['listing']

    def create(self, validated_data):
        request = self.context['request']
        listing = validated_data['listing']
        conversation, _ = Conversation.objects.get_or_create(
            listing=listing, buyer=request.user, owner=listing.owner,
        )
        return conversation
