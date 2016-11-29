from django import forms

class NameForm(forms.Form):
    full_name = forms.CharField(label='Full name', max_length=200)

#test