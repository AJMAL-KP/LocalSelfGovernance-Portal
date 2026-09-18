from django import forms
from lsg.models import Post, Role, PostScope

class PostForm(forms.ModelForm):
    title = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'lsg-input',
            'placeholder': 'Enter post title...',
            'maxlength': '150'
        }),
        label="Title"
    )
    content = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'lsg-input',
            'placeholder': 'Write your post content here (max 1000 characters)...',
            'rows': 5,
            'maxlength': '1000'
        }),
        label="Description"
    )
    scope = forms.ChoiceField(
        choices=PostScope.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Post Scope",
        required=False
    )

    class Meta:
        model = Post
        fields = ('title', 'content', 'scope', 'image')
        widgets = {
            'image': forms.FileInput(attrs={'class': 'lsg-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['image'].required = False

        if user and user.role == Role.PANCHAYAT_PRESIDENT:
            self.fields['scope'].required = True
            if not self.instance.pk and not self.data:
                self.fields['scope'].initial = PostScope.PANCHAYAT
        else:
            if 'scope' in self.fields:
                del self.fields['scope']


from lsg.models import Alert, AlertCategory

class AlertForm(forms.ModelForm):
    title = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'lsg-input',
            'placeholder': 'Enter alert title (max 150 characters)...',
            'maxlength': '150'
        }),
        label="Title"
    )
    category = forms.ChoiceField(
        choices=AlertCategory.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Category"
    )
    scope = forms.ChoiceField(
        choices=PostScope.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Alert Scope",
        required=False
    )

    class Meta:
        model = Alert
        fields = ('title', 'category', 'scope')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['category'].required = True

        if user and user.role == Role.PANCHAYAT_PRESIDENT:
            self.fields['scope'].required = True
            if not self.instance.pk and not self.data:
                self.fields['scope'].initial = PostScope.PANCHAYAT
        else:
            if 'scope' in self.fields:
                del self.fields['scope']


from lsg.models import Document, DocumentCategory

class DocumentForm(forms.ModelForm):
    title = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'lsg-input',
            'placeholder': 'Enter document title (max 150 characters)...',
            'maxlength': '150'
        }),
        label="Title"
    )
    category = forms.ChoiceField(
        choices=DocumentCategory.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Category"
    )
    scope = forms.ChoiceField(
        choices=PostScope.choices,
        widget=forms.Select(attrs={'class': 'lsg-input'}),
        label="Document Scope",
        required=False
    )
    is_pinned = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-indigo-600 focus:ring-indigo-500 h-4 w-4 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900',
        }),
        label="Pin Document to top",
        required=False
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'lsg-input'}),
        label="Document File"
    )

    class Meta:
        model = Document
        fields = ('title', 'category', 'scope', 'is_pinned', 'file')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['category'].required = True

        if self.instance and self.instance.pk:
            self.fields['file'].required = False
        else:
            self.fields['file'].required = True

        if user and user.role == Role.PANCHAYAT_PRESIDENT:
            self.fields['scope'].required = True
            if not self.instance.pk and not self.data:
                self.fields['scope'].initial = PostScope.PANCHAYAT
        else:
            if 'scope' in self.fields:
                del self.fields['scope']


