import re
from django import forms
from django.contrib.auth import authenticate
from lsg.models import User, Panchayat, Ward

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'lsg-input', 'placeholder': 'Password'}),
        label="Password",
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'lsg-input', 'placeholder': 'Confirm Password'}),
        label="Confirm Password",
        required=True
    )

    class Meta:
        model = User
        fields = ('email', 'name', 'age', 'aadhar_id', 'phone', 'panchayat', 'ward')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'lsg-input', 'placeholder': 'Email Address'}),
            'name': forms.TextInput(attrs={'class': 'lsg-input', 'placeholder': 'Full Name'}),
            'age': forms.NumberInput(attrs={'class': 'lsg-input', 'placeholder': 'Age'}),
            'aadhar_id': forms.TextInput(attrs={'class': 'lsg-input', 'placeholder': '12-digit Aadhar ID'}),
            'phone': forms.TextInput(attrs={'class': 'lsg-input', 'placeholder': '10-digit Phone Number'}),
            'panchayat': forms.HiddenInput(),
            'ward': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Email, name, age, panchayat, ward, phone, and aadhar_id are required
        self.fields['email'].required = True
        self.fields['name'].required = True
        self.fields['age'].required = True
        self.fields['panchayat'].required = True
        self.fields['ward'].required = True
        self.fields['aadhar_id'].required = True
        self.fields['phone'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and age < 18:
            raise forms.ValidationError("You must be 18 years or older to register.")
        return age

    def clean_aadhar_id(self):
        aadhar_id = self.cleaned_data.get('aadhar_id')
        if not aadhar_id:
            return aadhar_id
        # Validate that it is numeric and exactly 12 digits
        if not aadhar_id.isdigit() or len(aadhar_id) != 12:
            raise forms.ValidationError("Aadhar ID must be exactly 12 digits.")
        if User.objects.filter(aadhar_id=aadhar_id).exists():
            raise forms.ValidationError("A user with this Aadhar ID already exists.")
        return aadhar_id

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        # Validate phone matches Indian regex: exactly 10 digits starting with 6,7,8,9
        if not re.match(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError("Phone number must be a valid 10-digit Indian number.")
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        panchayat = cleaned_data.get('panchayat')
        ward = cleaned_data.get('ward')

        # Check matching passwords
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
            cleaned_data['password'] = ''
            cleaned_data['confirm_password'] = ''

        # Check ward-panchayat hierarchy consistency
        if panchayat and ward:
            if ward.panchayat != panchayat:
                self.add_error('ward', "The selected Ward does not belong to the selected Panchayat.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'lsg-input', 'placeholder': 'Email Address'}),
        required=True
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'lsg-input', 'placeholder': 'Password'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                # Find user with matching email
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid email or password.")

            # Authenticate using the username (which is the email)
            authenticated_user = authenticate(username=user.username, password=password)
            if authenticated_user is None:
                raise forms.ValidationError("Invalid email or password.")
            elif authenticated_user.is_superuser:
                raise forms.ValidationError("Access Denied: Superusers must log in via the Django Admin Panel.")
            elif not authenticated_user.is_active:
                raise forms.ValidationError("This account is inactive.")

            cleaned_data['user'] = authenticated_user

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'phone', 'age')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'lsg-input', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'lsg-input', 'placeholder': '10-digit Phone Number'}),
            'age': forms.NumberInput(attrs={'class': 'lsg-input', 'placeholder': 'Age'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['phone'].required = True
        self.fields['age'].required = True

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is not None and age < 18:
            raise forms.ValidationError("You must be 18 years or older.")
        return age

    def clean_phone(self):

        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        if not re.match(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError("Phone number must be a valid 10-digit Indian number.")
        if User.objects.exclude(pk=self.instance.pk).filter(phone=phone).exists():
            raise forms.ValidationError("A user with this phone number already exists.")
        return phone


class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'lsg-input', 'placeholder': 'Email Address'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email
