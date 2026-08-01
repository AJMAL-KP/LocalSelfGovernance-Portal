from django import forms
from lsg.models import Post

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

    class Meta:
        model = Post
        fields = ('title', 'content', 'image')
        widgets = {
            'image': forms.FileInput(attrs={'class': 'lsg-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['image'].required = False

