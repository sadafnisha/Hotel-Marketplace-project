from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from listings.models import HotelListing
from .forms import MessageForm
from .models import Conversation, Message


@login_required
def start_conversation(request, pk):
    listing = get_object_or_404(HotelListing, pk=pk)

    if not request.user.is_buyer:
        messages.error(
            request,
            'Only buyers can start a conversation with owners.'
        )
        return redirect('listings:detail', pk=pk)

    conversation, _ = Conversation.objects.get_or_create(
        listing=listing,
        buyer=request.user,
        owner=listing.owner
    )

    return redirect('chat:conversation', pk=conversation.pk)


@login_required
def inbox(request):
    conversations = Conversation.objects.filter(
        buyer=request.user
    ) | Conversation.objects.filter(
        owner=request.user
    )

    conversations = conversations.distinct().order_by('-updated_at')

    for conversation in conversations:
        conversation.unread_count = conversation.unread_count_for(
            request.user
        )

    return render(
        request,
        'chat/inbox.html',
        {'conversations': conversations}
    )


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    if request.user.id not in (
        conversation.buyer_id,
        conversation.owner_id
    ):
        messages.error(
            request,
            'Not authorized to view this conversation.'
        )
        return redirect('chat:inbox')

    conversation.messages.exclude(
        sender=request.user
    ).filter(
        read_at__isnull=True
    ).update(
        read_at=timezone.now()
    )

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversation = conversation
            msg.sender = request.user
            msg.save()

            conversation.save()

            return redirect(
                'chat:conversation',
                pk=conversation.pk
            )
    else:
        form = MessageForm()

    return render(
        request,
        'chat/conversation.html',
        {
            'conversation': conversation,
            'form': form,
            'other_party': conversation.other_party(request.user),
        }
    )