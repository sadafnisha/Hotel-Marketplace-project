from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .forms import OwnerRegisterForm, BuyerRegisterForm, OwnerProfileForm, BuyerProfileForm, UserBasicForm
from .models import User


def register_choice(request):
    return render(request, 'accounts/register_choice.html')


def register_owner(request):
    if request.method == 'POST':
        form = OwnerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your hotel owner account is ready.')
            return redirect('dashboard:redirect')
    else:
        form = OwnerRegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'role': 'Hotel Owner'})


def register_buyer(request):
    if request.method == 'POST':
        form = BuyerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your buyer/investor account is ready.')
            return redirect('dashboard:redirect')
    else:
        form = BuyerRegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'role': 'Buyer / Investor'})


class RoleAwareLoginView(LoginView):
    template_name = 'accounts/login.html'


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('listings:marketplace')


class AppPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


@login_required
def profile_settings(request):
    user = request.user
    profile_form = None
    if user.is_owner:
        from .models import OwnerProfile
        owner_profile, _ = OwnerProfile.objects.get_or_create(user=user)
        profile_form_class = OwnerProfileForm
        profile_instance = owner_profile
    elif user.is_buyer:
        from .models import BuyerProfile
        buyer_profile, _ = BuyerProfile.objects.get_or_create(user=user)
        profile_form_class = BuyerProfileForm
        profile_instance = buyer_profile
    else:
        profile_form_class = None
        profile_instance = None

    if request.method == 'POST':
        user_form = UserBasicForm(request.POST, instance=user)
        valid = user_form.is_valid()
        if profile_form_class:
            profile_form = profile_form_class(request.POST, request.FILES, instance=profile_instance)
            valid = valid and profile_form.is_valid()
        if valid:
            user_form.save()
            if profile_form_class:
                profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        user_form = UserBasicForm(instance=user)
        if profile_form_class:
            profile_form = profile_form_class(instance=profile_instance)

    return render(request, 'accounts/profile.html', {
        'user_form': user_form, 'profile_form': profile_form
    })
