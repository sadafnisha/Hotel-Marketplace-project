from rest_framework import serializers

from listings.models import HotelListing, HotelImage, Favourite
from .accounts import PublicUserSerializer


class HotelImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelImage
        fields = ['id', 'image', 'sort_order']


class HotelListingListSerializer(serializers.ModelSerializer):
    """Lightweight representation used for the marketplace list endpoint."""
    owner = PublicUserSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()
    is_favourited = serializers.SerializerMethodField()

    class Meta:
        model = HotelListing
        fields = [
            'id', 'reference_number', 'title', 'property_type', 'city', 'state',
            'country', 'rooms', 'asking_amount', 'status', 'owner',
            'cover_image', 'is_favourited', 'created_at',
        ]

    def get_cover_image(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image)
        return obj.cover_image

    def get_is_favourited(self, obj):
        user = self.context.get('request') and self.context['request'].user
        if not user or not user.is_authenticated or not getattr(user, 'is_buyer', False):
            return False
        # `favourite_ids` may be pre-computed by the view for efficiency (avoids N+1 queries).
        favourite_ids = self.context.get('favourite_ids')
        if favourite_ids is not None:
            return obj.id in favourite_ids
        return Favourite.objects.filter(buyer=user, listing=obj).exists()


class HotelListingDetailSerializer(HotelListingListSerializer):
    """Full representation used for retrieve, including images and financial/lease detail."""
    images = HotelImageSerializer(many=True, read_only=True)
    amenity_list = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta(HotelListingListSerializer.Meta):
        fields = HotelListingListSerializer.Meta.fields + [
            'description', 'address', 'latitude', 'longitude',
            'property_area_sqft', 'amenities', 'amenity_list',
            'operational_status', 'years_in_operation', 'ownership_type',
            'security_deposit', 'lease_duration_years', 'renewal_terms',
            'annual_revenue', 'annual_occupancy_rate', 'contact_preference',
            'rejection_reason', 'images', 'updated_at', 'published_at',
        ]


class HotelListingWriteSerializer(serializers.ModelSerializer):
    """
    Used for create/update by the owning Owner.
    `owner` and `status` are never client-settable directly here -- the view
    assigns `owner = request.user` and manages status transitions explicitly,
    matching the behaviour of listings.views.create_listing/edit_listing.
    """

    class Meta:
        model = HotelListing
        fields = [
            'title', 'description', 'property_type',
            'address', 'city', 'state', 'country', 'latitude', 'longitude',
            'rooms', 'property_area_sqft', 'amenities',
            'operational_status', 'years_in_operation',
            'ownership_type', 'asking_amount', 'security_deposit',
            'lease_duration_years', 'renewal_terms',
            'annual_revenue', 'annual_occupancy_rate',
            'contact_preference',
        ]

    def validate_asking_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Asking amount must be greater than zero.')
        return value

    def validate_rooms(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('Rooms must be a positive number.')
        return value


class FavouriteSerializer(serializers.ModelSerializer):
    listing_detail = HotelListingListSerializer(source='listing', read_only=True)

    class Meta:
        model = Favourite
        fields = ['id', 'listing', 'listing_detail', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_listing(self, listing):
        if listing.status != HotelListing.Status.PUBLISHED:
            raise serializers.ValidationError('Only published listings can be saved as favourites.')
        return listing

    def create(self, validated_data):
        buyer = self.context['request'].user
        favourite, _ = Favourite.objects.get_or_create(buyer=buyer, listing=validated_data['listing'])
        return favourite
