import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class HotelListing(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending Approval'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'
        CLOSED = 'closed', 'Closed'

    class PropertyType(models.TextChoices):
        BUSINESS_HOTEL = 'business_hotel', 'Business Hotel'
        RESORT = 'resort', 'Resort'
        BOUTIQUE = 'boutique', 'Boutique Hotel'
        BUDGET = 'budget', 'Budget Hotel'
        HERITAGE = 'heritage', 'Heritage Property'
        SERVICED_APARTMENTS = 'serviced_apartments', 'Serviced Apartments'

    reference_number = models.CharField(max_length=20, unique=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings'
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    property_type = models.CharField(max_length=30, choices=PropertyType.choices)

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    rooms = models.PositiveIntegerField()
    property_area_sqft = models.PositiveIntegerField(null=True, blank=True)
    amenities = models.TextField(
        blank=True, help_text="Comma-separated, e.g. Pool, Gym, Restaurant, Parking, Wi-Fi"
    )

    operational_status = models.CharField(
        max_length=20,
        choices=[('operational', 'Operational'), ('under_renovation', 'Under Renovation'), ('closed', 'Closed')],
        default='operational',
    )
    years_in_operation = models.PositiveIntegerField(default=0)

    ownership_type = models.CharField(
        max_length=20,
        choices=[('freehold', 'Freehold'), ('leasehold', 'Leasehold'), ('management_contract', 'Management Contract')],
        default='freehold',
    )
    asking_amount = models.DecimalField(max_digits=14, decimal_places=2, help_text="Expected lease / asking amount")
    security_deposit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    lease_duration_years = models.PositiveIntegerField(null=True, blank=True)
    renewal_terms = models.CharField(max_length=255, blank=True)

    annual_revenue = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                          help_text="Sample/mock financial data")
    annual_occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                 help_text="Percentage, sample data")

    contact_preference = models.CharField(
        max_length=20,
        choices=[('platform_message', 'Platform Messaging Only'), ('phone', 'Phone'), ('email', 'Email')],
        default='platform_message',
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    rejection_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.reference_number})"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"HTL-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('listings:detail', args=[self.pk])

    @property
    def amenity_list(self):
        return [a.strip() for a in self.amenities.split(',') if a.strip()]

    @property
    def cover_image(self):
        img = self.images.first()
        return img.image.url if img else None


class HotelImage(models.Model):
    listing = models.ForeignKey(HotelListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/')
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"Image for {self.listing.title} (#{self.sort_order})"


class Favourite(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favourites')
    listing = models.ForeignKey(HotelListing, on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('buyer', 'listing')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.buyer} saved {self.listing}"
