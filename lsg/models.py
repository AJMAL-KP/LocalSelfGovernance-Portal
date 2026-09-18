from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class Role(models.TextChoices):
    VILLAGER = 'VILLAGER', 'Villager'
    WARD_MEMBER = 'WARD_MEMBER', 'Ward Member'
    PANCHAYAT_PRESIDENT = 'PANCHAYAT_PRESIDENT', 'Panchayat President'

Role.PANCHAYAT_ADMIN = Role.PANCHAYAT_PRESIDENT


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

    def clean(self):
        super().clean()

        # 1. Single Panchayat President per Panchayat
        if self.role == Role.PANCHAYAT_PRESIDENT and self.panchayat:
            existing_president = User.objects.filter(
                panchayat=self.panchayat,
                role=Role.PANCHAYAT_PRESIDENT
            ).exclude(pk=self.pk)
            if existing_president.exists():
                raise ValidationError({
                    'role': f"This Panchayat already has a Panchayat President ({existing_president.first().name or existing_president.first().username})."
                })

        # 2. Single Ward Representative (Ward Member) per Ward
        if self.role == Role.WARD_MEMBER and self.ward:
            existing_member = User.objects.filter(
                ward=self.ward,
                role=Role.WARD_MEMBER
            ).exclude(pk=self.pk)
            if existing_member.exists():
                raise ValidationError({
                    'role': f"This Ward already has a Ward Representative ({existing_member.first().name or existing_member.first().username})."
                })

        # 3. Ensure no Ward Representative for the Ward of a Panchayat President
        if self.role == Role.WARD_MEMBER and self.ward:
            president_in_ward = User.objects.filter(
                ward=self.ward,
                role=Role.PANCHAYAT_PRESIDENT
            ).exclude(pk=self.pk)
            if president_in_ward.exists():
                raise ValidationError({
                    'ward': f"This Ward belongs to a Panchayat President ({president_in_ward.first().name or president_in_ward.first().username}) and cannot have a separate Ward Representative."
                })

        if self.role == Role.PANCHAYAT_PRESIDENT and self.ward:
            member_in_ward = User.objects.filter(
                ward=self.ward,
                role=Role.WARD_MEMBER
            ).exclude(pk=self.pk)
            if member_in_ward.exists():
                raise ValidationError({
                    'ward': f"This Ward already has a Ward Representative ({member_in_ward.first().name or member_in_ward.first().username}). A Panchayat President's Ward cannot have a separate Ward Representative."
                })

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


class AlertCategory(models.TextChoices):
    EMERGENCY = 'EMERGENCY', 'Emergency'
    HEALTH = 'HEALTH', 'Health & Sanitation'
    DEVELOPMENT = 'DEVELOPMENT', 'Development Work'
    GENERAL = 'GENERAL', 'General Announcement'


class Alert(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')
    category = models.CharField(
        max_length=50,
        choices=AlertCategory.choices,
        default=AlertCategory.GENERAL
    )
    scope = models.CharField(
        max_length=20,
        choices=PostScope.choices,
        default=PostScope.WARD
    )
    panchayat = models.ForeignKey(
        Panchayat,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.title and len(self.title) > 150:
            raise ValidationError({'title': "Title cannot exceed 150 characters."})
            
        # Duplication check
        if self.panchayat_id:
            duplicate = Alert.objects.filter(
                title=self.title,
                panchayat_id=self.panchayat_id,
                category=self.category,
                scope=self.scope
            )
            if self.pk:
                duplicate = duplicate.exclude(pk=self.pk)
            if duplicate.exists():
                raise ValidationError("A duplicate alert with this title already exists in your Panchayat.")

    def __str__(self):
        return f"{self.title} - {self.author.username} ({self.category})"


class DocumentCategory(models.TextChoices):
    CIRCULAR = 'CIRCULAR', 'Official Circular'
    NOTICE = 'NOTICE', 'Public Notice'
    FORM = 'FORM', 'Application Form'
    REPORT = 'REPORT', 'Report & Minutes'


class Document(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/', verbose_name="Document File")
    category = models.CharField(
        max_length=50,
        choices=DocumentCategory.choices,
        default=DocumentCategory.CIRCULAR
    )
    scope = models.CharField(
        max_length=20,
        choices=PostScope.choices,
        default=PostScope.WARD
    )
    panchayat = models.ForeignKey(
        Panchayat,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents'
    )
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.title and len(self.title) > 150:
            raise ValidationError({'title': "Title cannot exceed 150 characters."})

    def __str__(self):
        return f"{self.title} - {self.author.username} ({self.category})"


class ComplaintStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    SOLVED = 'SOLVED', 'Solved'
    REJECTED = 'REJECTED', 'Rejected'


class ComplaintCategory(models.TextChoices):
    ROADS = 'ROADS', 'Roads & Infrastructure'
    WATER = 'WATER', 'Water Supply'
    ELECTRICITY = 'ELECTRICITY', 'Electricity & Streetlights'
    SANITATION = 'SANITATION', 'Sanitation & Waste'
    DRAINAGE = 'DRAINAGE', 'Drainage & Sewage'
    GENERAL = 'GENERAL', 'General Grievance'


class Complaint(models.Model):
    villager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_complaints'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_complaints'
    )
    subject = models.CharField(max_length=150)
    category = models.CharField(
        max_length=50,
        choices=ComplaintCategory.choices,
        default=ComplaintCategory.GENERAL
    )
    description = models.TextField()
    attachment = models.FileField(
        upload_to='complaints/',
        blank=True,
        null=True,
        verbose_name="Attachment File"
    )
    status = models.CharField(
        max_length=20,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.PENDING
    )
    panchayat = models.ForeignKey(
        Panchayat,
        on_delete=models.CASCADE,
        related_name='complaints'
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name='complaints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.subject and len(self.subject) > 150:
            raise ValidationError({'subject': "Subject cannot exceed 150 characters."})

    def __str__(self):
        return f"{self.subject} - {self.villager.username} ({self.get_status_display()})"


