from rest_framework import serializers

from listings.models import HotelListing
from offers.models import Offer, OfferHistory
from .accounts import PublicUserSerializer
from .listings import HotelListingListSerializer


class OfferHistorySerializer(serializers.ModelSerializer):
    actor = PublicUserSerializer(read_only=True)

    class Meta:
        model = OfferHistory
        fields = ['id', 'actor', 'action', 'amount', 'message', 'timestamp']


class OfferSerializer(serializers.ModelSerializer):
    buyer = PublicUserSerializer(read_only=True)
    owner = PublicUserSerializer(read_only=True)
    listing_detail = HotelListingListSerializer(source='listing', read_only=True)
    history = OfferHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'listing', 'listing_detail', 'buyer', 'owner',
            'amount', 'proposed_terms', 'message', 'status',
            'history', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'buyer', 'owner', 'status', 'created_at', 'updated_at']


class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Creates an offer as the currently authenticated Buyer.
    Mirrors offers.views.make_offer: listing must be published, and a buyer
    cannot have more than one active (pending/countered) offer per listing.
    """

    class Meta:
        model = Offer
        fields = ['listing', 'amount', 'proposed_terms', 'message']

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Offer amount must be greater than zero.')
        return value

    def validate_listing(self, listing):
        if listing.status != HotelListing.Status.PUBLISHED:
            raise serializers.ValidationError('This listing is not accepting offers.')
        return listing

    def validate(self, attrs):
        request = self.context['request']
        listing = attrs['listing']
        if Offer.objects.filter(
            listing=listing,
            buyer=request.user,
            status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED],
        ).exists():
            raise serializers.ValidationError(
                'You already have an active offer on this listing.'
            )
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        listing = validated_data['listing']
        offer = Offer.objects.create(
            listing=listing,
            buyer=request.user,
            owner=listing.owner,
            amount=validated_data['amount'],
            proposed_terms=validated_data.get('proposed_terms', ''),
            message=validated_data.get('message', ''),
        )
        offer.record_history(request.user, 'submitted', message=offer.message)
        return offer


class OfferActionSerializer(serializers.Serializer):
    """
    Validates the payload for POST /api/offers/{id}/respond/.
    The actual authorization (who may perform which action) is enforced in
    the view, matching offers.views.offer_detail's action handling exactly.
    """
    ACTION_CHOICES = [
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('counter', 'Counter'),
        ('withdraw', 'Withdraw'),
        ('accept_counter', 'Accept Counter'),
        ('reject_counter', 'Reject Counter'),
    ]
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True)
    message = serializers.CharField(required=False, allow_blank=True)
