import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, OwnerProfile, BuyerProfile
from listings.models import HotelListing
from offers.models import Offer
from chat.models import Conversation, Message


CITIES = [
    ('Lucknow', 'Uttar Pradesh'), ('Jaipur', 'Rajasthan'), ('Goa', 'Goa'),
    ('Manali', 'Himachal Pradesh'), ('Udaipur', 'Rajasthan'), ('Mumbai', 'Maharashtra'),
    ('Bengaluru', 'Karnataka'), ('Rishikesh', 'Uttarakhand'), ('Kochi', 'Kerala'),
    ('Shimla', 'Himachal Pradesh'), ('Varanasi', 'Uttar Pradesh'), ('Pune', 'Maharashtra'),
]

HOTEL_NAMES = [
    'Grand Heritage Palace', 'Riverside Business Inn', 'Emerald Hills Resort',
    'Sunrise Boutique Hotel', 'Royal Orchid Suites', 'Blue Lagoon Resort',
    'The Metropolitan Hotel', 'Green Valley Retreat', 'Golden Sands Resort',
    'City Central Business Hotel', 'Lakeview Heritage Inn', 'Mountain Pearl Resort',
]

AMENITIES = ['Pool', 'Gym', 'Restaurant', 'Parking', 'Wi-Fi', 'Spa', 'Conference Hall', 'Bar', 'Room Service']


class Command(BaseCommand):
    help = 'Seed demo data for the hotel leasing marketplace'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@hotellease.demo', 'AdminPass123')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / AdminPass123'))

        owners = []
        for i in range(1, 6):
            username = f'owner{i}'
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
            else:
                user = User.objects.create_user(
                    username=username, email=f'{username}@hotellease.demo',
                    password='Password123', role=User.Role.OWNER,
                    first_name=f'Owner{i}', last_name='Demo', phone=f'98765{i:05d}',
                )
                OwnerProfile.objects.create(
                    user=user, business_name=f'{username.capitalize()} Hospitality Group',
                    description='Demo hotel ownership group for the marketplace assignment.',
                    is_verified=True,
                )
            owners.append(user)

        buyers = []
        for i in range(1, 6):
            username = f'buyer{i}'
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
            else:
                user = User.objects.create_user(
                    username=username, email=f'{username}@hotellease.demo',
                    password='Password123', role=User.Role.BUYER,
                    first_name=f'Buyer{i}', last_name='Demo', phone=f'91234{i:05d}',
                )
                BuyerProfile.objects.create(
                    user=user, company_name=f'{username.capitalize()} Capital Partners',
                    investment_preferences='Mid-market hotels, 20-100 rooms, tier 2 cities preferred.',
                )
            buyers.append(user)

        if HotelListing.objects.count() < 10:
            property_types = list(HotelListing.PropertyType.values)
            for i in range(10):
                city, state = random.choice(CITIES)
                owner = random.choice(owners)
                title = f"{random.choice(HOTEL_NAMES)} - {city}"
                if HotelListing.objects.filter(title=title).exists():
                    continue
                listing = HotelListing.objects.create(
                    owner=owner,
                    title=title,
                    description=(
                        f"A well-established {random.choice(['business', 'leisure', 'boutique'])} hotel "
                        f"located in {city}, offering a strong lease opportunity for investors seeking "
                        f"stable returns in a growing hospitality market."
                    ),
                    property_type=random.choice(property_types),
                    address=f"{random.randint(1,200)} Main Road",
                    city=city, state=state, country='India',
                    rooms=random.choice([20, 35, 45, 60, 80, 100, 150]),
                    property_area_sqft=random.randint(8000, 60000),
                    amenities=', '.join(random.sample(AMENITIES, k=5)),
                    operational_status='operational',
                    years_in_operation=random.randint(2, 25),
                    ownership_type=random.choice(['freehold', 'leasehold', 'management_contract']),
                    asking_amount=Decimal(random.choice([2500000, 4500000, 6000000, 8500000, 12000000, 18000000])),
                    security_deposit=Decimal(random.choice([200000, 500000, 750000, 1000000])),
                    lease_duration_years=random.choice([5, 9, 10, 15]),
                    renewal_terms='Renewable with 10% escalation every term',
                    annual_revenue=Decimal(random.choice([8000000, 15000000, 22000000, 35000000])),
                    annual_occupancy_rate=Decimal(random.choice([55, 62, 68, 74, 80])),
                    contact_preference='platform_message',
                    status=HotelListing.Status.PUBLISHED,
                    published_at=timezone.now(),
                )
                self.stdout.write(f'Created listing: {listing.title}')

            # A couple in draft/pending for realism
            for status in [HotelListing.Status.DRAFT, HotelListing.Status.PENDING]:
                city, state = random.choice(CITIES)
                owner = random.choice(owners)
                HotelListing.objects.create(
                    owner=owner,
                    title=f"{random.choice(HOTEL_NAMES)} - {city} ({status})",
                    description='Sample listing awaiting completion/approval.',
                    property_type=random.choice(property_types),
                    address=f"{random.randint(1,200)} Market Street",
                    city=city, state=state, country='India',
                    rooms=random.choice([25, 40, 55]),
                    amenities=', '.join(random.sample(AMENITIES, k=3)),
                    asking_amount=Decimal(random.choice([3000000, 5000000])),
                    status=status,
                )

        published = list(HotelListing.objects.filter(status=HotelListing.Status.PUBLISHED))
        if Offer.objects.count() < 8 and published:
            for _ in range(8):
                listing = random.choice(published)
                buyer = random.choice(buyers)
                if Offer.objects.filter(listing=listing, buyer=buyer).exists():
                    continue
                amount = listing.asking_amount * Decimal(random.choice(['0.85', '0.9', '0.95', '1.0']))
                offer = Offer.objects.create(
                    listing=listing, buyer=buyer, owner=listing.owner,
                    amount=amount.quantize(Decimal('1')),
                    proposed_terms='7-year lease, 5% annual escalation proposed.',
                    message='Interested in discussing terms further.',
                    status=random.choice([Offer.Status.PENDING, Offer.Status.ACCEPTED, Offer.Status.COUNTERED]),
                )
                offer.record_history(buyer, 'submitted', message=offer.message)

                conversation, _ = Conversation.objects.get_or_create(
                    listing=listing, buyer=buyer, owner=listing.owner
                )
                Message.objects.get_or_create(
                    conversation=conversation, sender=buyer,
                    body=f"Hi, I'm interested in {listing.title}. Could you share more details on the lease terms?"
                )
                Message.objects.get_or_create(
                    conversation=conversation, sender=listing.owner,
                    body="Thanks for reaching out! Happy to discuss - what's your target lease duration?"
                )

        self.stdout.write(self.style.SUCCESS('Demo data seeding complete.'))
        self.stdout.write(self.style.SUCCESS(
            'Login as: admin/AdminPass123 (superuser), owner1-owner5 / Password123, buyer1-buyer5 / Password123'
        ))
