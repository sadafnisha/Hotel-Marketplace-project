from django import forms
from .models import Offer


class MakeOfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['amount', 'proposed_terms', 'message']
        widgets = {
            'proposed_terms': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional proposed lease terms'}),
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message to the owner'}),
        }


class OfferResponseForm(forms.Form):
    ACTION_CHOICES = [('accept', 'Accept'), ('reject', 'Reject'), ('counter', 'Counter')]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.HiddenInput)
    amount = forms.DecimalField(required=False, label='Counter amount')
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
