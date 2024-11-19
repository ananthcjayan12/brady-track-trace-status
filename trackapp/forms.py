# forms.py

from django import forms
from .models import Item, QRCode, Transaction

class UploadCSVForm(forms.Form):
    file = forms.FileField()

class CreateQRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        fields = ['item', 'mcode']

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ['timestamp']
