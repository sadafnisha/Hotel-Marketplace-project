"""
Offers API.

Business rules enforced here mirror offers/views.py exactly:
  * Only authenticated Buyers can submit offers.
  * A listing must be Published to accept new offers (closed/draft/pending
    listings reject new offers).
  * A buyer cannot have more than one active (pending/countered) offer on
    the same listing at a time.
  * Only the offer's Owner may accept / reject / counter a pending offer.
  * Only the offer's Buyer may withdraw a pending offer, or accept/reject a
    counter-offer.
  * Only the buyer, the owner, or an admin may view a given offer.
"""
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from offers.models import Offer
from api.permissions import IsBuyerRole, IsOfferParticipantOrAdmin
from api.serializers import OfferSerializer, OfferCreateSerializer, OfferActionSerializer


class OfferViewSet(viewsets.ModelViewSet):
    """
    /api/offers/               GET (offers where caller is buyer or owner), POST (buyer only)
    /api/offers/{id}/          GET (participant/admin only)
    /api/offers/{id}/respond/  POST {"action": "accept"|"reject"|"counter"|"withdraw"|
                                       "accept_counter"|"reject_counter", "amount", "message"}
    /api/offers/mine/          GET (buyer) - offers the caller submitted
    /api/offers/received/      GET (owner) - offers received on the caller's listings
    """
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsBuyerRole()]
        if self.action in ('retrieve', 'respond'):
            return [permissions.IsAuthenticated(), IsOfferParticipantOrAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return OfferCreateSerializer
        return OfferSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Offer.objects.select_related('listing', 'buyer', 'owner').prefetch_related('history')
        if user.is_platform_admin:
            return qs
        if self.action == 'mine':
            return qs.filter(buyer=user)
        if self.action == 'received':
            return qs.filter(owner=user)
        return qs.filter(Q(buyer=user) | Q(owner=user))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        if not request.user.is_buyer:
            return Response({'detail': 'Only buyers have submitted offers.'}, status=status.HTTP_403_FORBIDDEN)
        return self._list(request)

    @action(detail=False, methods=['get'])
    def received(self, request):
        if not request.user.is_owner:
            return Response({'detail': 'Only owners receive offers.'}, status=status.HTTP_403_FORBIDDEN)
        return self._list(request)

    def _list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page if page is not None else self.get_queryset(), many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        offer = self.get_object()
        action_serializer = OfferActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        act = action_serializer.validated_data['action']
        amount = action_serializer.validated_data.get('amount')
        msg = action_serializer.validated_data.get('message', '')

        user = request.user
        if act == 'accept' and user.id == offer.owner_id:
            offer.status = Offer.Status.ACCEPTED
            offer.save()
            offer.record_history(user, 'accepted', message=msg)
        elif act == 'reject' and user.id == offer.owner_id:
            offer.status = Offer.Status.REJECTED
            offer.save()
            offer.record_history(user, 'rejected', message=msg)
        elif act == 'counter' and user.id == offer.owner_id:
            new_amount = amount or offer.amount
            offer.amount = new_amount
            offer.status = Offer.Status.COUNTERED
            offer.save()
            offer.record_history(user, 'countered', amount=new_amount, message=msg)
        elif act == 'withdraw' and user.id == offer.buyer_id:
            offer.status = Offer.Status.WITHDRAWN
            offer.save()
            offer.record_history(user, 'withdrawn', message=msg)
        elif act == 'accept_counter' and user.id == offer.buyer_id:
            offer.status = Offer.Status.ACCEPTED
            offer.save()
            offer.record_history(user, 'accepted_counter', message=msg)
        elif act == 'reject_counter' and user.id == offer.buyer_id:
            offer.status = Offer.Status.REJECTED
            offer.save()
            offer.record_history(user, 'rejected_counter', message=msg)
        else:
            return Response({'detail': 'Action not permitted.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(OfferSerializer(offer).data)
