from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from listings.models import HotelListing
from .forms import MakeOfferForm, OfferResponseForm
from .models import Offer


@login_required
def make_offer(request, pk):
    listing = get_object_or_404(HotelListing, pk=pk)
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers can submit offers.')
        return redirect('listings:detail', pk=pk)
    if listing.status != HotelListing.Status.PUBLISHED:
        messages.error(request, 'This listing is not accepting offers.')
        return redirect('listings:detail', pk=pk)
    if Offer.objects.filter(listing=listing, buyer=request.user,
                             status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]).exists():
        messages.error(request, 'You already have an active offer on this listing.')
        return redirect('listings:detail', pk=pk)

    if request.method == 'POST':
        form = MakeOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.listing = listing
            offer.buyer = request.user
            offer.owner = listing.owner
            offer.save()
            offer.record_history(request.user, 'submitted', message=offer.message)
            messages.success(request, 'Your offer has been submitted.')
            return redirect('offers:detail', pk=offer.pk)
    else:
        form = MakeOfferForm()

    return render(request, 'offers/make_offer.html', {'form': form, 'listing': listing})


@login_required
def offer_detail(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.id not in (offer.buyer_id, offer.owner_id) and not request.user.is_platform_admin:
        messages.error(request, 'Not authorized to view this offer.')
        return redirect('listings:marketplace')

    if request.method == 'POST':
        form = OfferResponseForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            msg = form.cleaned_data.get('message', '')
            if action == 'accept' and request.user.id == offer.owner_id:
                offer.status = Offer.Status.ACCEPTED
                offer.save()
                offer.record_history(request.user, 'accepted', message=msg)
                messages.success(request, 'Offer accepted.')
            elif action == 'reject' and request.user.id == offer.owner_id:
                offer.status = Offer.Status.REJECTED
                offer.save()
                offer.record_history(request.user, 'rejected', message=msg)
                messages.success(request, 'Offer rejected.')
            elif action == 'counter' and request.user.id == offer.owner_id:
                new_amount = form.cleaned_data.get('amount') or offer.amount
                offer.amount = new_amount
                offer.status = Offer.Status.COUNTERED
                offer.save()
                offer.record_history(request.user, 'countered', amount=new_amount, message=msg)
                messages.success(request, 'Counter offer sent.')
            elif action == 'withdraw' and request.user.id == offer.buyer_id:
                offer.status = Offer.Status.WITHDRAWN
                offer.save()
                offer.record_history(request.user, 'withdrawn', message=msg)
                messages.success(request, 'Offer withdrawn.')
            elif action == 'accept_counter' and request.user.id == offer.buyer_id:
                offer.status = Offer.Status.ACCEPTED
                offer.save()
                offer.record_history(request.user, 'accepted_counter', message=msg)
                messages.success(request, 'Counter offer accepted.')
            elif action == 'reject_counter' and request.user.id == offer.buyer_id:
                offer.status = Offer.Status.REJECTED
                offer.save()
                offer.record_history(request.user, 'rejected_counter', message=msg)
                messages.success(request, 'Counter offer rejected.')
            else:
                messages.error(request, 'Action not permitted.')
            return redirect('offers:detail', pk=offer.pk)
    form = OfferResponseForm()

    return render(request, 'offers/detail.html', {'offer': offer, 'form': form})


@login_required
def my_offers(request):
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers have submitted offers.')
        return redirect('listings:marketplace')
    offers = Offer.objects.filter(buyer=request.user).select_related('listing')
    return render(request, 'offers/my_offers.html', {'offers': offers})


@login_required
def received_offers(request):
    if not request.user.is_owner:
        messages.error(request, 'Only owners receive offers.')
        return redirect('listings:marketplace')
    offers = Offer.objects.filter(owner=request.user).select_related('listing', 'buyer')
    return render(request, 'offers/received_offers.html', {'offers': offers})
