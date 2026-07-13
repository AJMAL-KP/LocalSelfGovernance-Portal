from django.test import TestCase
from django.urls import reverse
from .models import Taluk, Panchayat, Ward, User, Role
from lsg.forms.auth import RegistrationForm, LoginForm

class AuthenticationTests(TestCase):

    def setUp(self):
        # Set up a Taluk, Panchayats, and Wards
        self.taluk = Taluk.objects.create(name="Central Taluk")
        
        self.panchayat_a = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.panchayat_b = Panchayat.objects.create(name="Panchayat B", taluk=self.taluk)
        
        self.ward_a1 = Ward.objects.create(number=1, name="Ward A1", panchayat=self.panchayat_a)
        self.ward_a2 = Ward.objects.create(number=2, name="Ward A2", panchayat=self.panchayat_a)
        self.ward_b1 = Ward.objects.create(number=1, name="Ward B1", panchayat=self.panchayat_b)

    def test_registration_form_valid(self):
        # Test registering with valid data
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 30,
            'phone': '9876543210',
            'aadhar_id': '123456789012',
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_a1.id,
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        
        # Verify saved user attributes
        user = form.save()
        self.assertEqual(user.username, 'villager@example.com')
        self.assertEqual(user.email, 'villager@example.com')
        self.assertEqual(user.role, Role.VILLAGER)
        self.assertEqual(user.panchayat, self.panchayat_a)
        self.assertEqual(user.ward, self.ward_a1)

    def test_registration_form_invalid_aadhar(self):
        # Aadhar must be exactly 12 digits
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 30,
            'phone': '9876543210',
            'aadhar_id': '12345',  # Invalid length
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_a1.id,
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('aadhar_id', form.errors)

    def test_registration_form_invalid_phone(self):
        # Phone must be a valid 10-digit Indian number
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 30,
            'phone': '1234567890',  # Invalid start digit for Indian numbers (must be 6-9)
            'aadhar_id': '123456789012',
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_a1.id,
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_registration_form_invalid_age(self):
        # Age must be >= 18
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 17,  # Under 18
            'phone': '9876543210',
            'aadhar_id': '123456789012',
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_a1.id,
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('age', form.errors)

    def test_registration_form_short_password(self):
        # Password must be >= 8 chars
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 25,
            'phone': '9876543210',
            'aadhar_id': '123456789012',
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_a1.id,
            'password': 'pass',  # Too short
            'confirm_password': 'pass',
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_registration_form_mismatched_passwords(self):
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 30,
            'phone': '9876543210',
            'aadhar_id': '123456789012',
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_a1.id,
            'password': 'password123',
            'confirm_password': 'different_password',
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_registration_form_invalid_ward_panchayat_hierarchy(self):
        # Ward B1 does not belong to Panchayat A
        form_data = {
            'email': 'villager@example.com',
            'name': 'Villager Test',
            'age': 30,
            'phone': '9876543210',
            'aadhar_id': '123456789012',
            'panchayat': self.panchayat_a.id,
            'ward': self.ward_b1.id,  # Invalid ward choice for Panchayat A
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ward', form.errors)

    def test_superuser_login_denied_on_frontend(self):
        # Create a superuser
        User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='superuserpass'
        )
        
        # Attempt frontend login
        login_data = {
            'email': 'admin@example.com',
            'password': 'superuserpass'
        }
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Superusers must log in via the Django Admin Panel')

    def test_superuser_frontend_access_redirects(self):
        # Create and log in a superuser
        admin_user = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='superuserpass'
        )
        self.client.force_login(admin_user)
        
        # Verify dashboard access redirects to Django Admin site index
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('admin:index'))
        
        # Verify profile access redirects to Django Admin site index
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, reverse('admin:index'))

    def test_login_and_logout_flow(self):
        # First, register a user
        User.objects.create_user(
            username='villager@example.com',
            email='villager@example.com',
            password='password123',
            name='Villager User',
            aadhar_id='123456789012',
            phone='9876543210',
            panchayat=self.panchayat_a,
            ward=self.ward_a1,
            age=25,
            role=Role.VILLAGER
        )
        
        # Test rendering login
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
        # Test login POST
        login_data = {
            'email': 'villager@example.com',
            'password': 'password123'
        }
        response = self.client.post(reverse('login'), data=login_data)
        self.assertRedirects(response, reverse('profile'))
        
        # Test profile is accessible
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Villager User')
        
        # Test logout
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        
        # Test profile redirects to login now
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, '/login/?next=/profile/')


class AuthorizationAndDashboardTests(TestCase):

    def setUp(self):
        # Set up a Taluk, Panchayat, and Ward
        self.taluk = Taluk.objects.create(name="Central Taluk")
        self.panchayat = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.ward = Ward.objects.create(number=1, name="Ward 1", panchayat=self.panchayat)

        # Create user accounts for each role
        self.villager = User.objects.create_user(
            username='villager@example.com',
            email='villager@example.com',
            password='password123',
            name='Villager User',
            aadhar_id='111111111111',
            phone='9876543210',
            panchayat=self.panchayat,
            ward=self.ward,
            age=25,
            role=Role.VILLAGER
        )
        self.ward_member = User.objects.create_user(
            username='member@example.com',
            email='member@example.com',
            password='password123',
            name='Ward Member User',
            aadhar_id='222222222222',
            phone='9876543211',
            panchayat=self.panchayat,
            ward=self.ward,
            age=30,
            role=Role.WARD_MEMBER
        )
        self.panchayat_admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='password123',
            name='Panchayat Admin User',
            aadhar_id='333333333333',
            phone='9876543212',
            panchayat=self.panchayat,
            ward=self.ward,
            age=35,
            role=Role.PANCHAYAT_ADMIN
        )

    def test_root_dashboard_redirects_to_posts(self):
        self.client.force_login(self.villager)
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('posts'))

    def test_unauthenticated_users_redirected(self):
        protected_urls = ['posts', 'alerts', 'documents', 'complaints', 'manage_users', 'profile']
        for name in protected_urls:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f'/login/?next={reverse(name)}')

    def test_manage_users_access_control(self):
        # Villager should be redirected to posts with a message
        self.client.force_login(self.villager)
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('posts'))
        
        # Ward Member should be redirected to posts with a message
        self.client.force_login(self.ward_member)
        response = self.client.get(reverse('manage_users'))
        self.assertRedirects(response, reverse('posts'))

        # Panchayat Admin should be allowed
        self.client.force_login(self.panchayat_admin)
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panchayat User Management')

    def test_sidebar_role_based_menu_rendering(self):
        # 1. Villager Sidebar Verification
        self.client.force_login(self.villager)
        response = self.client.get(reverse('posts'))
        self.assertContains(response, 'Posts')
        self.assertContains(response, 'Announcements')
        self.assertContains(response, 'Complaints')
        self.assertContains(response, 'Documents')
        self.assertContains(response, 'Profile')
        self.assertNotContains(response, 'Manage Users')

        # 2. Panchayat Admin Sidebar Verification
        self.client.force_login(self.panchayat_admin)
        response = self.client.get(reverse('posts'))
        self.assertContains(response, 'Posts')
        self.assertContains(response, 'Announcements')
        self.assertContains(response, 'Complaints')
        self.assertContains(response, 'Documents')
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'Manage Users')
