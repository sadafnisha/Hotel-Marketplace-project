from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import HotelListingForm, HotelImageFormSet, ListingSearchForm
from .models import HotelListing, Favourite


def marketplace(request):
    form = ListingSearchForm(request.GET or None)
    listings = HotelListing.objects.filter(status=HotelListing.Status.PUBLISHED)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        city = form.cleaned_data.get('city')
        property_type = form.cleaned_data.get('property_type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        min_rooms = form.cleaned_data.get('min_rooms')
        sort = form.cleaned_data.get('sort') or 'newest'

        if q:
            listings = listings.filter(
                Q(title__icontains=q) | Q(city__icontains=q) | Q(address__icontains=q)
            )
        if city:
            listings = listings.filter(city__icontains=city)
        if property_type:
            listings = listings.filter(property_type=property_type)
        if min_price is not None:
            listings = listings.filter(asking_amount__gte=min_price)
        if max_price is not None:
            listings = listings.filter(asking_amount__lte=max_price)
        if min_rooms is not None:
            listings = listings.filter(rooms__gte=min_rooms)

        sort_map = {
            'newest': '-created_at',
            'price_low': 'asking_amount',
            'price_high': '-asking_amount',
            'rooms': '-rooms',
        }
        listings = listings.order_by(sort_map.get(sort, '-created_at'))

    paginator = Paginator(listings, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    favourite_ids = set()
    if request.user.is_authenticated and request.user.is_buyer:
        favourite_ids = set(
            Favourite.objects.filter(buyer=request.user).values_list('listing_id', flat=True)
        )

    return render(request, 'listings/marketplace.html', {
        'form': form, 'page_obj': page_obj, 'favourite_ids': favourite_ids,
    })


def listing_detail(request, pk):
    listing = get_object_or_404(HotelListing, pk=pk)
    is_owner = request.user.is_authenticated and listing.owner_id == request.user.id
    if listing.status != HotelListing.Status.PUBLISHED and not is_owner and not (
        request.user.is_authenticated and request.user.is_platform_admin
    ):
        messages.error(request, 'This listing is not currently available.')
        return redirect('listings:marketplace')

    is_favourited = False
    if request.user.is_authenticated and request.user.is_buyer:
        is_favourited = Favourite.objects.filter(buyer=request.user, listing=listing).exists()

    return render(request, 'listings/detail.html', {
        'listing': listing, 'is_owner': is_owner, 'is_favourited': is_favourited,
    })


def _owner_required(user):
    return user.is_authenticated and user.is_owner


@login_required
def my_listings(request):
    if not request.user.is_owner:
        messages.error(request, 'Only hotel owners can access this page.')
        return redirect('listings:marketplace')
    listings = HotelListing.objects.filter(owner=request.user)
    return render(request, 'listings/my_listings.html', {'listings': listings})


@login_required
def create_listing(request):
    if not request.user.is_owner:
        messages.error(request, 'Only hotel owners can create listings.')
        return redirect('listings:marketplace')

    if request.method == 'POST':
        form = HotelListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.status = HotelListing.Status.DRAFT
            listing.save()
            formset = HotelImageFormSet(request.POST, request.FILES, instance=listing)
            if formset.is_valid():
                formset.save()
            action = request.POST.get('action')
            if action == 'publish':
                listing.status = HotelListing.Status.PENDING
                listing.save()
                messages.success(request, 'Listing submitted for approval.')
            else:
                messages.success(request, 'Listing saved as draft.')
            return redirect('listings:my_listings')
    else:
        form = HotelListingForm()

    formset = HotelImageFormSet()
    return render(request, 'listings/listing_form.html', {
        'form': form, 'formset': formset, 'title': 'Create Hotel Listing'
    })


@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(HotelListing, pk=pk)
    if listing.owner_id != request.user.id:
        messages.error(request, 'You can only edit your own listings.')
        return redirect('listings:my_listings')

    if request.method == 'POST':
        form = HotelListingForm(request.POST, instance=listing)
        formset = HotelImageFormSet(request.POST, request.FILES, instance=listing)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            action = request.POST.get('action')
            if action == 'publish':
                listing.status = HotelListing.Status.PENDING
                listing.save()
                messages.success(request, 'Listing submitted for approval.')
            elif action == 'draft':
                listing.status = HotelListing.Status.DRAFT
                listing.save()
                messages.success(request, 'Listing saved as draft.')
            else:
                messages.success(request, 'Listing updated.')
            return redirect('listings:my_listings')
    else:
        form = HotelListingForm(instance=listing)
        formset = HotelImageFormSet(instance=listing)

    return render(request, 'listings/listing_form.html', {
        'form': form, 'formset': formset, 'title': 'Edit Hotel Listing', 'listing': listing
    })


@login_required
def update_listing_status(request, pk, new_status):
    listing = get_object_or_404(HotelListing, pk=pk)
    if listing.owner_id != request.user.id:
        messages.error(request, 'Not authorized.')
        return redirect('listings:my_listings')

    valid_transitions = {
        'publish': HotelListing.Status.PENDING,
        'unpublish': HotelListing.Status.DRAFT,
        'close': HotelListing.Status.CLOSED,
    }
    if new_status in valid_transitions:
        listing.status = valid_transitions[new_status]
        if new_status == 'publish':
            listing.published_at = timezone.now()
        listing.save()
        messages.success(request, f'Listing status updated to {listing.get_status_display()}.')
    return redirect('listings:my_listings')


@login_required
def toggle_favourite(request, pk):
    listing = get_object_or_404(HotelListing, pk=pk)
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers can save listings.')
        return redirect('listings:detail', pk=pk)

    fav, created = Favourite.objects.get_or_create(buyer=request.user, listing=listing)
    if not created:
        fav.delete()
        messages.info(request, 'Removed from saved hotels.')
    else:
        messages.success(request, 'Added to saved hotels.')
    return redirect(request.META.get('HTTP_REFERER', 'listings:detail'))


@login_required
def saved_listings(request):
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers have saved listings.')
        return redirect('listings:marketplace')
    favourites = Favourite.objects.filter(buyer=request.user).select_related('listing')
    return render(request, 'listings/saved.html', {'favourites': favourites})
