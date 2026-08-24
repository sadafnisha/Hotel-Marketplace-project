from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.utils import timezone

from listings.models import HotelListing, Favourite
from offers.models import Offer
from chat.models import Conversation, Message
from accounts.models import User


@login_required
def redirect_dashboard(request):
    user = request.user
    if user.is_platform_admin:
        return redirect('dashboard:admin')
    if user.is_owner:
        return redirect('dashboard:owner')
    return redirect('dashboard:buyer')


@login_required
def owner_dashboard(request):
    if not request.user.is_owner:
        return redirect('dashboard:redirect')
    listings = HotelListing.objects.filter(owner=request.user)
    offers = Offer.objects.filter(owner=request.user).select_related('listing', 'buyer')
    recent_messages = Message.objects.filter(
        conversation__owner=request.user
    ).exclude(sender=request.user).order_by('-created_at')[:5]

    stats = {
        'total_listings': listings.count(),
        'published': listings.filter(status=HotelListing.Status.PUBLISHED).count(),
        'draft_pending': listings.filter(
            status__in=[HotelListing.Status.DRAFT, HotelListing.Status.PENDING]
        ).count(),
        'total_inquiries': Conversation.objects.filter(owner=request.user).count(),
        'active_offers': offers.filter(status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]).count(),
        'accepted_offers': offers.filter(status=Offer.Status.ACCEPTED).count(),
        'rejected_offers': offers.filter(status=Offer.Status.REJECTED).count(),
        'countered_offers': offers.filter(status=Offer.Status.COUNTERED).count(),
    }

    return render(request, 'dashboard/owner_dashboard.html', {
        'stats': stats,
        'listings': listings[:5],
        'offers': offers[:5],
        'recent_messages': recent_messages,
    })


@login_required
def buyer_dashboard(request):
    if not request.user.is_buyer:
        return redirect('dashboard:redirect')
    favourites = Favourite.objects.filter(buyer=request.user).select_related('listing')
    offers = Offer.objects.filter(buyer=request.user).select_related('listing')
    conversations = Conversation.objects.filter(buyer=request.user).select_related('listing', 'owner')

    stats = {
        'saved': favourites.count(),
        'submitted_offers': offers.count(),
        'active_offers': offers.filter(status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]).count(),
        'accepted_offers': offers.filter(status=Offer.Status.ACCEPTED).count(),
    }

    return render(request, 'dashboard/buyer_dashboard.html', {
        'stats': stats,
        'favourites': favourites[:5],
        'offers': offers[:5],
        'conversations': conversations[:5],
    })


def _is_admin(user):
    return user.is_authenticated and user.is_platform_admin


@user_passes_test(_is_admin, login_url='accounts:login')
def admin_dashboard(request):
    stats = {
        'total_owners': User.objects.filter(role=User.Role.OWNER).count(),
        'total_buyers': User.objects.filter(role=User.Role.BUYER).count(),
        'total_listings': HotelListing.objects.count(),
        'published': HotelListing.objects.filter(status=HotelListing.Status.PUBLISHED).count(),
        'pending': HotelListing.objects.filter(status=HotelListing.Status.PENDING).count(),
        'rejected': HotelListing.objects.filter(status=HotelListing.Status.REJECTED).count(),
        'closed': HotelListing.objects.filter(status=HotelListing.Status.CLOSED).count(),
        'total_offers': Offer.objects.count(),
    }
    recent_users = User.objects.order_by('-date_joined')[:8]
    recent_offers = Offer.objects.select_related('listing', 'buyer').order_by('-created_at')[:8]
    pending_listings = HotelListing.objects.filter(status=HotelListing.Status.PENDING).select_related('owner')[:10]

    return render(request, 'dashboard/admin_dashboard.html', {
        'stats': stats, 'recent_users': recent_users,
        'recent_offers': recent_offers, 'pending_listings': pending_listings,
    })


@user_passes_test(_is_admin, login_url='accounts:login')
def admin_listings(request):
    listings = HotelListing.objects.select_related('owner').order_by('-created_at')
    status = request.GET.get('status')
    if status:
        listings = listings.filter(status=status)
    return render(request, 'dashboard/admin_listings.html', {
        'listings': listings, 'statuses': HotelListing.Status.choices, 'current_status': status,
    })


@user_passes_test(_is_admin, login_url='accounts:login')
def admin_moderate_listing(request, pk, action):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages as dj_messages
    listing = get_object_or_404(HotelListing, pk=pk)
    if action == 'approve':
        listing.status = HotelListing.Status.PUBLISHED
        listing.published_at = timezone.now()
        listing.save()
        dj_messages.success(request, f'"{listing.title}" approved and published.')
    elif action == 'reject':
        listing.status = HotelListing.Status.REJECTED
        listing.save()
        dj_messages.success(request, f'"{listing.title}" rejected.')
    elif action == 'suspend':
        listing.status = HotelListing.Status.CLOSED
        listing.save()
        dj_messages.success(request, f'"{listing.title}" suspended/closed.')
    return redirect('dashboard:admin_listings')


@user_passes_test(_is_admin, login_url='accounts:login')
def admin_users(request):
    users = User.objects.exclude(is_superuser=True).order_by('-date_joined')
    role = request.GET.get('role')
    if role:
        users = users.filter(role=role)
    return render(request, 'dashboard/admin_users.html', {'users': users, 'current_role': role})


@user_passes_test(_is_admin, login_url='accounts:login')
def admin_toggle_user_status(request, pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages as dj_messages
    user = get_object_or_404(User, pk=pk)
    user.status = User.Status.SUSPENDED if user.status == User.Status.ACTIVE else User.Status.ACTIVE
    user.is_active = user.status == User.Status.ACTIVE
    user.save()
    dj_messages.success(request, f'{user.username} is now {user.status}.')
    return redirect('dashboard:admin_users')
