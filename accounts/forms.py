from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, OwnerProfile, BuyerProfile


class OwnerRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False, max_length=20)
    business_name = forms.CharField(required=False, max_length=150)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.OWNER
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            OwnerProfile.objects.create(
                user=user, business_name=self.cleaned_data.get('business_name', '')
            )
        return user


class BuyerRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False, max_length=20)
    company_name = forms.CharField(required=False, max_length=150)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.BUYER
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            BuyerProfile.objects.create(
                user=user, company_name=self.cleaned_data.get('company_name', '')
            )
        return user


class OwnerProfileForm(forms.ModelForm):
    class Meta:
        model = OwnerProfile
        fields = ['business_name', 'profile_image', 'description']


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ['company_name', 'profile_image', 'investment_preferences']


class UserBasicForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
