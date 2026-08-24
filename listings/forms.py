from django import forms
from .models import HotelListing, HotelImage


class HotelListingForm(forms.ModelForm):
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
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'amenities': forms.TextInput(attrs={'placeholder': 'Pool, Gym, Restaurant, Parking, Wi-Fi'}),
            'renewal_terms': forms.TextInput(attrs={'placeholder': 'e.g. 5-year renewable, 10% escalation'}),
        }


class HotelImageForm(forms.ModelForm):
    class Meta:
        model = HotelImage
        fields = ['image', 'sort_order']


HotelImageFormSet = forms.inlineformset_factory(
    HotelListing, HotelImage, form=HotelImageForm, extra=3, can_delete=True
)


class ListingSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search')
    city = forms.CharField(required=False)
    property_type = forms.ChoiceField(required=False, choices=[('', 'Any type')] + list(HotelListing.PropertyType.choices))
    min_price = forms.DecimalField(required=False, label='Min price')
    max_price = forms.DecimalField(required=False, label='Max price')
    min_rooms = forms.IntegerField(required=False, label='Min rooms')
    sort = forms.ChoiceField(required=False, choices=[
        ('newest', 'Newest'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('rooms', 'Room Count'),
    ])
