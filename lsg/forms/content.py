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


