from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from Apps.accounts.models import User
from .models import Conversation, Message


@login_required
def inbox(request):
    conversations = (
        Conversation.objects.filter(participants=request.user)
        .order_by("-updated_at")
        .distinct()
    )
    return render(request, "inbox.html", {"conversations": conversations})


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Message.objects.create(conversation=conversation, sender=request.user, content=content)
            conversation.save()
            return redirect("conversation_detail", pk=conversation.pk)
        messages.error(request, "Xabar bo‘sh bo‘lmasin.")

    messages_qs = (
        Message.objects.filter(conversation=conversation)
        .select_related("sender")
        .order_by("created_at")
    )
    return render(
        request,
        "conversation.html",
        {"conversation": conversation, "messages": messages_qs},
    )


@login_required
def start_conversation(request, user_pk):
    other = get_object_or_404(User, pk=user_pk)
    if other == request.user:
        return redirect("inbox")

    existing = Conversation.objects.filter(participants=request.user).filter(participants=other).first()
    if existing:
        return redirect("conversation_detail", pk=existing.pk)

    conv = Conversation.objects.create()
    conv.participants.add(request.user, other)
    return redirect("conversation_detail", pk=conv.pk)