from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import OwnerProfile, BuyerProfile

User = get_user_model()


class OwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerProfile
        fields = ['business_name', 'profile_image', 'description', 'is_verified', 'created_at']
        read_only_fields = ['is_verified', 'created_at']


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = ['company_name', 'profile_image', 'investment_preferences', 'created_at']
        read_only_fields = ['created_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes the current user, including their role-specific profile.
    Used for GET /api/users/me/ and as a nested representation elsewhere
    (e.g. inside listings, offers, conversations).
    """
    owner_profile = OwnerProfileSerializer(read_only=True)
    buyer_profile = BuyerProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'status', 'is_active', 'date_joined',
            'owner_profile', 'buyer_profile',
        ]
        read_only_fields = ['id', 'role', 'status', 'is_active', 'date_joined']


class PublicUserSerializer(serializers.ModelSerializer):
    """A trimmed-down, non-sensitive representation used for nesting (e.g. listing owner, offer buyer)."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'role']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles self-registration for Owners and Buyers via the API.
    Mirrors accounts.forms.OwnerRegisterForm / BuyerRegisterForm, including
    automatic creation of the matching profile row.
    Admin accounts cannot be created through this endpoint.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=[(User.Role.OWNER, 'Owner'), (User.Role.BUYER, 'Buyer')])
    business_name = serializers.CharField(required=False, allow_blank=True, max_length=150, write_only=True)
    company_name = serializers.CharField(required=False, allow_blank=True, max_length=150, write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'password', 'role', 'business_name', 'company_name',
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        business_name = validated_data.pop('business_name', '')
        company_name = validated_data.pop('company_name', '')
        password = validated_data.pop('password')
        role = validated_data.pop('role')

        user = User(role=role, **validated_data)
        user.set_password(password)  # Django's built-in hashing (PBKDF2 by default)
        user.save()

        if role == User.Role.OWNER:
            OwnerProfile.objects.create(user=user, business_name=business_name)
        else:
            BuyerProfile.objects.create(user=user, company_name=company_name)
        return user
