from django import forms
from lsg.models import Complaint, ComplaintCategory, ComplaintStatus

class ComplaintForm(forms.ModelForm):
    subject = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'lsg-input',
            'placeholder': 'Brief summary of the issue (e.g. Broken streetlight near Ward 3 shop)...',
            'maxlength': '150'
        }),
        label="Subject / Title"
    )
    category = forms.ChoiceField(
        choices=ComplaintCategory.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Category / Tag"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'lsg-input',
            'placeholder': 'Provide details about your complaint, precise location, and any relevant details...',
            'rows': 5,
            'maxlength': '1500'
        }),
        label="Detailed Description"
    )
    attachment = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'lsg-input'}),
        label="Attach Image or Document (Optional)",
        required=False
    )

    class Meta:
        model = Complaint
        fields = ('subject', 'category', 'description', 'attachment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].required = True
        self.fields['category'].required = True
        self.fields['description'].required = True
        self.fields['attachment'].required = False


class ComplaintStatusForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=ComplaintStatus.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Update Complaint Status"
    )

    class Meta:
        model = Complaint
        fields = ('status',)
