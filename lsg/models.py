from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.TextChoices):
    VILLAGER = 'VILLAGER', 'Villager'
    WARD_MEMBER = 'WARD_MEMBER', 'Ward Member'
    PANCHAYAT_ADMIN = 'PANCHAYAT_ADMIN', 'Panchayat Admin'


class Taluk(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Panchayat(models.Model):
    name = models.CharField(max_length=255)
    taluk = models.ForeignKey(Taluk, on_delete=models.CASCADE, related_name='panchayats')

    class Meta:
        unique_together = ('name', 'taluk')

    def __str__(self):
        return f"{self.name} (Panchayat)"


class Ward(models.Model):
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)
    panchayat = models.ForeignKey(Panchayat, on_delete=models.CASCADE, related_name='wards')

    class Meta:
        unique_together = ('number', 'panchayat')

    def __str__(self):
        name_str = f" - {self.name}" if self.name else ""
        return f"Ward {self.number}{name_str} ({self.panchayat.name})"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VILLAGER
    )
    name = models.CharField(max_length=255, blank=True, verbose_name="Full Name")
    age = models.PositiveIntegerField(null=True, blank=True)
    
    # Set email unique and required
    email = models.EmailField(unique=True)
    
    aadhar_id = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Aadhar ID"
    )
    phone = models.CharField(max_length=15, blank=True, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="Profile Picture")
    
    # Relations for self governance hierarchy
    panchayat = models.ForeignKey(
        Panchayat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    password_changed_at = models.DateTimeField(null=True, blank=True, verbose_name="Password Last Changed At")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class PostScope(models.TextChoices):
    WARD = 'WARD', 'Ward'
    PANCHAYAT = 'PANCHAYAT', 'Panchayat'


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    scope = models.CharField(
        max_length=20,
        choices=PostScope.choices,
        default=PostScope.WARD
    )
    panchayat = models.ForeignKey(
        Panchayat,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='posts'
    )
    image = models.ImageField(upload_to='post_images/', blank=True, null=True, verbose_name="Post Image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.author.username} ({self.get_scope_display()})"

