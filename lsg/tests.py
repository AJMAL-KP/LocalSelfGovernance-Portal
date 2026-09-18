from django.test import TestCase
from django.urls import reverse
from .models import Taluk, Panchayat, Ward, User, Role, Post, PostScope, Alert, AlertCategory, Complaint, ComplaintStatus, ComplaintCategory
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
        self.assertRedirects(response, reverse('posts'))
        
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
        protected_urls = ['posts', 'alerts', 'documents', 'complaints', 'manage_members', 'profile']
        for name in protected_urls:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f'/login/?next={reverse(name)}')

    def test_manage_members_access_control(self):
        # Villager should be redirected to posts with a message
        self.client.force_login(self.villager)
        response = self.client.get(reverse('manage_members'))
        self.assertRedirects(response, reverse('posts'))
        
        # Ward Member should be redirected to posts with a message
        self.client.force_login(self.ward_member)
        response = self.client.get(reverse('manage_members'))
        self.assertRedirects(response, reverse('posts'))

        # Panchayat Admin should be allowed
        self.client.force_login(self.panchayat_admin)
        response = self.client.get(reverse('manage_members'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panchayat Member Management')

    def test_sidebar_role_based_menu_rendering(self):
        # 1. Villager Sidebar Verification
        self.client.force_login(self.villager)
        response = self.client.get(reverse('posts'))
        self.assertContains(response, 'Posts')
        self.assertContains(response, 'Alerts')
        self.assertContains(response, 'Complaints')
        self.assertContains(response, 'Documents')
        self.assertContains(response, 'Profile')
        self.assertNotContains(response, 'Manage Members')

        # 2. Panchayat Admin Sidebar Verification
        self.client.force_login(self.panchayat_admin)
        response = self.client.get(reverse('posts'))
        self.assertContains(response, 'Posts')
        self.assertContains(response, 'Alerts')
        self.assertContains(response, 'Complaints')
        self.assertContains(response, 'Documents')
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'Manage Members')


class ProfileAndSettingsTests(TestCase):

    def setUp(self):
        # Set up a Taluk, Panchayat, and Ward
        self.taluk = Taluk.objects.create(name="Central Taluk")
        self.panchayat = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.ward = Ward.objects.create(number=1, name="Ward 1", panchayat=self.panchayat)

        # Create user
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='password123',
            name='Original Name',
            aadhar_id='111111111111',
            phone='9876543210',
            panchayat=self.panchayat,
            ward=self.ward,
            age=25,
            role=Role.VILLAGER
        )
        # Create second user to test uniqueness validations
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='password123',
            name='Other Name',
            aadhar_id='222222222222',
            phone='9876543211',
            panchayat=self.panchayat,
            ward=self.ward,
            age=30,
            role=Role.VILLAGER
        )

    def test_profile_view_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f'/login/?next={reverse("profile")}')

    def test_settings_view_requires_login(self):
        response = self.client.get(reverse('settings'))
        self.assertRedirects(response, f'/login/?next={reverse("settings")}')

    def test_profile_update_success(self):
        self.client.force_login(self.user)
        # Verify initial state
        self.assertEqual(self.user.name, 'Original Name')
        self.assertEqual(self.user.phone, '9876543210')
        self.assertEqual(self.user.age, 25)

        # Perform update via POST
        update_data = {
            'action': 'update_profile',
            'name': 'Updated Name',
            'phone': '9876543212',
            'age': 28,
        }
        response = self.client.post(reverse('profile'), data=update_data)
        self.assertRedirects(response, reverse('profile'))

        # Fetch updated user from DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated Name')
        self.assertEqual(self.user.phone, '9876543212')
        self.assertEqual(self.user.age, 28)

    def test_profile_update_invalid_phone(self):
        self.client.force_login(self.user)
        # Attempt update with invalid phone
        update_data = {
            'action': 'update_profile',
            'name': 'Updated Name',
            'phone': '1234567890', # Must start with 6-9
            'age': 25,
        }
        response = self.client.post(reverse('profile'), data=update_data)
        self.assertEqual(response.status_code, 200)
        # Should render form errors and keep show_edit_modal as True
        self.assertTrue(response.context['show_edit_modal'])
        self.assertFormError(response, 'profile_form', 'phone', 'Phone number must be a valid 10-digit Indian number.')

        # Database should not change
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Original Name')

    def test_profile_update_duplicate_phone(self):
        self.client.force_login(self.user)
        # Attempt update using other_user's phone
        update_data = {
            'action': 'update_profile',
            'name': 'Updated Name',
            'phone': '9876543211', # other_user's phone
            'age': 25,
        }
        response = self.client.post(reverse('profile'), data=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_edit_modal'])
        self.assertFormError(response, 'profile_form', 'phone', 'A user with this phone number already exists.')

    def test_profile_update_invalid_age(self):
        self.client.force_login(self.user)
        # Attempt update with age under 18
        update_data = {
            'action': 'update_profile',
            'name': 'Updated Name',
            'phone': '9876543212',
            'age': 17,
        }
        response = self.client.post(reverse('profile'), data=update_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_edit_modal'])
        self.assertFormError(response, 'profile_form', 'age', 'You must be 18 years or older.')


    def test_email_change_success(self):
        self.client.force_login(self.user)
        # Change email
        email_data = {
            'action': 'change_email',
            'email': 'newemail@example.com'
        }
        response = self.client.post(reverse('settings'), data=email_data)
        self.assertRedirects(response, reverse('settings'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        # Username must update too so they can log in
        self.assertEqual(self.user.username, 'newemail@example.com')

    def test_email_change_duplicate(self):
        self.client.force_login(self.user)
        # Try to use other_user's email
        email_data = {
            'action': 'change_email',
            'email': 'other@example.com'
        }
        response = self.client.post(reverse('settings'), data=email_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'email_form', 'email', 'A user with this email address already exists.')

    def test_password_change_success(self):
        self.client.force_login(self.user)
        # Change password
        password_data = {
            'action': 'change_password',
            'old_password': 'password123',
            'new_password1': 'newsecurepassword123',
            'new_password2': 'newsecurepassword123',
        }
        response = self.client.post(reverse('settings'), data=password_data)
        self.assertRedirects(response, reverse('settings'))

        # Verify password has changed by trying to authenticate
        from django.contrib.auth import authenticate
        authenticated_user = authenticate(username=self.user.username, password='newsecurepassword123')
        self.assertIsNotNone(authenticated_user)

    def test_profile_posts_pagination(self):
        # Change user's role to WARD_MEMBER so profile shows their recent uploaded posts
        self.user.role = Role.WARD_MEMBER
        self.user.save()
        
        self.client.force_login(self.user)
        
        # Create 25 posts authored by self.user
        posts_to_create = []
        for i in range(25):
            posts_to_create.append(
                Post(
                    author=self.user,
                    title=f"My Post {i}",
                    content=f"Content {i}",
                    scope=PostScope.PANCHAYAT,
                    panchayat=self.panchayat
                )
            )
        Post.objects.bulk_create(posts_to_create)
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        
        # Verify pagination limit of 20
        self.assertEqual(len(response.context['user_posts']), 20)
        
        page_obj = response.context['page_obj']
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())


class PostManagementTests(TestCase):

    def setUp(self):
        # Setup Taluk, Panchayat A & B
        self.taluk = Taluk.objects.create(name="Central Taluk")
        
        self.panchayat_a = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.panchayat_b = Panchayat.objects.create(name="Panchayat B", taluk=self.taluk)
        
        # Setup Wards under Panchayat A
        self.ward_a1 = Ward.objects.create(number=1, name="Ward A1", panchayat=self.panchayat_a)
        self.ward_a2 = Ward.objects.create(number=2, name="Ward A2", panchayat=self.panchayat_a)
        
        # Setup Users
        self.villager_a1 = User.objects.create_user(
            username='villager_a1@example.com',
            email='villager_a1@example.com',
            password='password123',
            name='Villager A1',
            role=Role.VILLAGER,
            panchayat=self.panchayat_a,
            ward=self.ward_a1,
            phone='9876543210',
            aadhar_id='111111111111',
            age=25
        )
        self.ward_member_a1 = User.objects.create_user(
            username='member_a1@example.com',
            email='member_a1@example.com',
            password='password123',
            name='Ward Member A1',
            role=Role.WARD_MEMBER,
            panchayat=self.panchayat_a,
            ward=self.ward_a1,
            phone='9876543211',
            aadhar_id='222222222222',
            age=30
        )
        self.ward_member_a2 = User.objects.create_user(
            username='member_a2@example.com',
            email='member_a2@example.com',
            password='password123',
            name='Ward Member A2',
            role=Role.WARD_MEMBER,
            panchayat=self.panchayat_a,
            ward=self.ward_a2,
            phone='9876543212',
            aadhar_id='333333333333',
            age=35
        )
        self.panchayat_admin_a = User.objects.create_user(
            username='admin_a@example.com',
            email='admin_a@example.com',
            password='password123',
            name='Admin A',
            role=Role.PANCHAYAT_ADMIN,
            panchayat=self.panchayat_a,
            phone='9876543213',
            aadhar_id='444444444444',
            age=40
        )
        self.panchayat_admin_a_other = User.objects.create_user(
            username='admin_a_other@example.com',
            email='admin_a_other@example.com',
            password='password123',
            name='Admin A Other',
            role=Role.PANCHAYAT_ADMIN,
            panchayat=self.panchayat_a,
            phone='9876543214',
            aadhar_id='555555555555',
            age=45
        )
        
        # Create Scoped Posts
        self.post_panchayat_a = Post.objects.create(
            author=self.panchayat_admin_a,
            title="Panchayat A Update",
            content="General announcement for Panchayat A",
            scope=PostScope.PANCHAYAT,
            panchayat=self.panchayat_a
        )
        self.post_ward_a1 = Post.objects.create(
            author=self.ward_member_a1,
            title="Ward A1 Update",
            content="Local news for Ward A1",
            scope=PostScope.WARD,
            panchayat=self.panchayat_a,
            ward=self.ward_a1
        )
        self.post_ward_a2 = Post.objects.create(
            author=self.ward_member_a2,
            title="Ward A2 Update",
            content="Local news for Ward A2",
            scope=PostScope.WARD,
            panchayat=self.panchayat_a,
            ward=self.ward_a2
        )
        self.post_panchayat_b = Post.objects.create(
            author=self.panchayat_admin_a,
            title="Panchayat B Update",
            content="General announcement for Panchayat B",
            scope=PostScope.PANCHAYAT,
            panchayat=self.panchayat_b
        )

    def test_post_feed_visibility(self):
        # 1. Villager of Panchayat A Ward 1 should see:
        # - Panchayat A Update
        # - Ward A1 Update
        # But NOT:
        # - Ward A2 Update
        # - Panchayat B Update
        self.client.force_login(self.villager_a1)
        response = self.client.get(reverse('posts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post_panchayat_a.title)
        self.assertContains(response, self.post_ward_a1.title)
        self.assertNotContains(response, self.post_ward_a2.title)
        self.assertNotContains(response, self.post_panchayat_b.title)

    def test_villager_cannot_create_or_manage_posts(self):
        self.client.force_login(self.villager_a1)
        
        # Cannot access create view
        response = self.client.get(reverse('create_post'))
        self.assertRedirects(response, reverse('posts'))
        
        # Cannot POST to create view
        create_data = {'title': 'Villager Post', 'content': 'Hello'}
        response = self.client.post(reverse('create_post'), data=create_data)
        self.assertRedirects(response, reverse('posts'))
        self.assertEqual(Post.objects.filter(title='Villager Post').count(), 0)

        # Cannot edit posts
        edit_data = {'title': 'Hacked Title', 'content': 'Hacked content'}
        response = self.client.post(reverse('edit_post', args=[self.post_panchayat_a.id]), data=edit_data)
        self.assertRedirects(response, reverse('posts'))
        self.post_panchayat_a.refresh_from_db()
        self.assertNotEqual(self.post_panchayat_a.title, 'Hacked Title')

        # Cannot delete posts
        response = self.client.post(reverse('delete_post', args=[self.post_panchayat_a.id]))
        self.assertRedirects(response, reverse('posts'))
        self.assertTrue(Post.objects.filter(id=self.post_panchayat_a.id).exists())

    def test_ward_member_crud(self):
        self.client.force_login(self.ward_member_a1)
        
        # Can access create view
        response = self.client.get(reverse('create_post'))
        self.assertEqual(response.status_code, 200)
        
        # Can create Ward-level post successfully
        create_data = {'title': 'New Ward Post', 'content': 'Important ward announcement'}
        response = self.client.post(reverse('create_post'), data=create_data)
        self.assertRedirects(response, reverse('posts'))
        
        new_post = Post.objects.get(title='New Ward Post')
        self.assertEqual(new_post.scope, PostScope.WARD)
        self.assertEqual(new_post.ward, self.ward_a1)
        self.assertEqual(new_post.panchayat, self.panchayat_a)
        
        # Can edit own post
        edit_data = {'title': 'Updated Ward Post', 'content': 'Important ward announcement (updated)'}
        response = self.client.post(reverse('edit_post', args=[new_post.id]), data=edit_data)
        self.assertRedirects(response, reverse('posts'))
        new_post.refresh_from_db()
        self.assertEqual(new_post.title, 'Updated Ward Post')
        
        # Cannot edit other Ward Member's post
        response = self.client.post(reverse('edit_post', args=[self.post_ward_a2.id]), data={'title': 'Hacked'})
        self.assertRedirects(response, reverse('posts'))
        self.post_ward_a2.refresh_from_db()
        self.assertNotEqual(self.post_ward_a2.title, 'Hacked')

        # Cannot delete other Ward Member's post
        response = self.client.post(reverse('delete_post', args=[self.post_ward_a2.id]))
        self.assertRedirects(response, reverse('posts'))
        self.assertTrue(Post.objects.filter(id=self.post_ward_a2.id).exists())
        
        # Can delete own post
        response = self.client.post(reverse('delete_post', args=[new_post.id]))
        self.assertRedirects(response, reverse('posts'))
        self.assertFalse(Post.objects.filter(id=new_post.id).exists())

    def test_panchayat_admin_crud(self):
        self.client.force_login(self.panchayat_admin_a)
        
        # Can create Panchayat-level post successfully
        create_data = {
            'title': 'New Panchayat Post',
            'content': 'Important panchayat announcement',
            'scope': PostScope.PANCHAYAT
        }
        response = self.client.post(reverse('create_post'), data=create_data)
        self.assertRedirects(response, reverse('posts'))
        
        new_post = Post.objects.get(title='New Panchayat Post')
        self.assertEqual(new_post.scope, PostScope.PANCHAYAT)
        self.assertIsNone(new_post.ward)
        self.assertEqual(new_post.panchayat, self.panchayat_a)
        
        # Can edit own post
        edit_data = {
            'title': 'Updated Panchayat Post',
            'content': 'Announcement content',
            'scope': PostScope.PANCHAYAT
        }
        response = self.client.post(reverse('edit_post', args=[new_post.id]), data=edit_data)
        self.assertRedirects(response, reverse('posts'))
        new_post.refresh_from_db()
        self.assertEqual(new_post.title, 'Updated Panchayat Post')
        
        # Can edit another Admin's Panchayat post in same Panchayat
        other_admin_post = self.post_panchayat_a # created by panchayat_admin_a
        self.client.force_login(self.panchayat_admin_a_other)
        edit_data_other = {
            'title': 'Admin override',
            'content': 'Overriding',
            'scope': PostScope.PANCHAYAT
        }
        response = self.client.post(reverse('edit_post', args=[other_admin_post.id]), data=edit_data_other)
        self.assertRedirects(response, reverse('posts'))
        other_admin_post.refresh_from_db()
        self.assertEqual(other_admin_post.title, 'Admin override')

        # Cannot edit Ward-level posts
        response = self.client.post(reverse('edit_post', args=[self.post_ward_a1.id]), data={'title': 'Hacked'})
        self.assertRedirects(response, reverse('posts'))
        self.post_ward_a1.refresh_from_db()
        self.assertNotEqual(self.post_ward_a1.title, 'Hacked')

    def test_post_creation_with_image(self):
        self.client.force_login(self.panchayat_admin_a)
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
        )
        mock_image = SimpleUploadedFile('test_image.gif', small_gif, content_type='image/gif')
        
        create_data = {
            'title': 'Post with Image',
            'content': 'Check out this cool image',
            'scope': PostScope.PANCHAYAT,
            'image': mock_image
        }
        response = self.client.post(reverse('create_post'), data=create_data)
        self.assertRedirects(response, reverse('posts'))
        
        new_post = Post.objects.get(title='Post with Image')
        self.assertTrue(new_post.image.name.startswith('post_images/test_image'))
        
        import os
        if new_post.image and os.path.exists(new_post.image.path):
            os.remove(new_post.image.path)

    def test_posts_list_pagination_limit(self):
        self.client.force_login(self.villager_a1)
        
        # Delete existing posts to start fresh
        Post.objects.all().delete()
        
        # Create 25 posts in Panchayat A
        posts_to_create = []
        for i in range(25):
            posts_to_create.append(
                Post(
                    author=self.ward_member_a1,
                    title=f"Post {i}",
                    content=f"Content {i}",
                    scope=PostScope.PANCHAYAT,
                    panchayat=self.panchayat_a
                )
            )
        Post.objects.bulk_create(posts_to_create)
        
        response = self.client.get(reverse('posts'))
        self.assertEqual(response.status_code, 200)
        
        # Check that page 1 has exactly 20 posts
        self.assertEqual(len(response.context['posts']), 20)
        
        page_obj = response.context['page_obj']
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())


class ManageMembersTests(TestCase):

    def setUp(self):
        self.taluk = Taluk.objects.create(name="Central Taluk")
        self.panchayat = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.ward_1 = Ward.objects.create(number=1, name="Ward 1", panchayat=self.panchayat)
        self.ward_2 = Ward.objects.create(number=2, name="Ward 2", panchayat=self.panchayat)
        
        # Panchayat Admin
        self.admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='password123',
            name='President A',
            role=Role.PANCHAYAT_PRESIDENT,
            panchayat=self.panchayat,
            phone='9876543210',
            aadhar_id='111111111111',
            age=45
        )
        
        # Villager
        self.villager = User.objects.create_user(
            username='villager@example.com',
            email='villager@example.com',
            password='password123',
            name='Villager A',
            role=Role.VILLAGER,
            panchayat=self.panchayat,
            ward=self.ward_1,
            phone='9876543211',
            aadhar_id='222222222222',
            age=25
        )

    def test_manage_members_search(self):
        self.client.force_login(self.admin)
        
        # 1-character query matching villager
        response = self.client.get(reverse('manage_members') + '?q=V')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Villager A')
        
        # Suffix wildcard matching
        response = self.client.get(reverse('manage_members') + '?q=Vill%')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Villager A')
        
        # Search query matching and filtered by Ward 1
        response = self.client.get(reverse('manage_members') + f'?q=Villager&search_ward_id={self.ward_1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Villager A')

        # Search query matching but filtered by Ward 2 (no match)
        response = self.client.get(reverse('manage_members') + f'?q=Villager&search_ward_id={self.ward_2.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Villager A')

    def test_manage_members_promote_success(self):
        self.client.force_login(self.admin)
        
        # Promote Villager A to Ward Representative (ward is automatically profile ward)
        response = self.client.post(reverse('manage_members'), {
            'action': 'promote',
            'user_id': self.villager.id
        })
        self.assertRedirects(response, reverse('manage_members'))
        
        # Verify db changes
        self.villager.refresh_from_db()
        self.assertEqual(self.villager.role, Role.WARD_MEMBER)
        self.assertEqual(self.villager.ward, self.ward_1)

    def test_manage_members_promote_validation_error(self):
        # Assign a representative to Ward 1 first
        User.objects.create_user(
            username='other_member@example.com',
            email='other_member@example.com',
            password='password123',
            name='Other Representative',
            role=Role.WARD_MEMBER,
            panchayat=self.panchayat,
            ward=self.ward_1,
            phone='9876543212',
            aadhar_id='333333333333',
            age=35
        )
        
        self.client.force_login(self.admin)
        
        # Promote self.villager (who is also registered in Ward 1) to Ward Member.
        # Since Ward 1 already has a representative, this should fail.
        response = self.client.post(reverse('manage_members'), {
            'action': 'promote',
            'user_id': self.villager.id
        }, follow=True)
        
        # Page should redirect/render with error message
        self.assertContains(response, 'Error: This Ward already has a Ward Representative')
        
        # Verify db state remains unchanged
        self.villager.refresh_from_db()
        self.assertEqual(self.villager.role, Role.VILLAGER)

    def test_manage_members_demote(self):
        # Promote first
        self.villager.role = Role.WARD_MEMBER
        self.villager.ward = self.ward_1
        self.villager.save()
        
        self.client.force_login(self.admin)
        
        # Demote back to villager
        response = self.client.post(reverse('manage_members'), {
            'action': 'demote',
            'user_id': self.villager.id
        })
        self.assertRedirects(response, reverse('manage_members'))
        
        # Verify db changes
        self.villager.refresh_from_db()
        self.assertEqual(self.villager.role, Role.VILLAGER)

    def test_manage_members_pagination(self):
        self.client.force_login(self.admin)
        
        # Create 15 ward members to verify pagination after 10
        # Wards must be created first since each ward can only have 1 representative
        wards_to_create = []
        for i in range(3, 18):
            wards_to_create.append(Ward(number=i, panchayat=self.panchayat))
        Ward.objects.bulk_create(wards_to_create)
        
        created_wards = Ward.objects.filter(panchayat=self.panchayat).exclude(number__in=[1, 2]).order_by('number')
        
        users_to_create = []
        for i, ward in enumerate(created_wards):
            users_to_create.append(
                User(
                    username=f"member_{i}@example.com",
                    email=f"member_{i}@example.com",
                    name=f"Member {i}",
                    role=Role.WARD_MEMBER,
                    panchayat=self.panchayat,
                    ward=ward,
                    phone=f"98765432{i+20}",
                    aadhar_id=f"9999999999{i:02d}",
                    age=30
                )
            )
        User.objects.bulk_create(users_to_create)
        
        # Get manage_members view
        response = self.client.get(reverse('manage_members'))
        self.assertEqual(response.status_code, 200)
        
        # Verify page 1 shows exactly 10 members
        self.assertEqual(len(response.context['members']), 10)
        
        # Verify pagination elements
        page_obj = response.context['page_obj']
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())

    def test_member_suggestions(self):
        self.client.force_login(self.admin)
        
        # 1-character suggest matching "V"
        response = self.client.get(reverse('member_suggestions') + '?q=V')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('suggestions', data)
        self.assertEqual(len(data['suggestions']), 1)
        self.assertEqual(data['suggestions'][0]['name'], 'Villager A')
        
        # Suffix wildcard matching suggest "Vi%"
        response = self.client.get(reverse('member_suggestions') + '?q=Vi%')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['suggestions']), 1)

        # Suggestion filtered by Ward 1 (matches)
        response = self.client.get(reverse('member_suggestions') + f'?q=V&search_ward_id={self.ward_1.id}')
        data = response.json()
        self.assertEqual(len(data['suggestions']), 1)
        
        # Suggestion filtered by Ward 2 (no match)
        response = self.client.get(reverse('member_suggestions') + f'?q=V&search_ward_id={self.ward_2.id}')
        data = response.json()
        self.assertEqual(len(data['suggestions']), 0)

    def test_admin_form_validation(self):
        from lsg.admin import CustomUserCreationForm, CustomUserChangeForm
        
        # 1. Test duplicate Panchayat President
        form_data = {
            'username': 'admin2@example.com',
            'email': 'admin2@example.com',
            'role': Role.PANCHAYAT_PRESIDENT,
            'name': 'President 2',
            'aadhar_id': '999999999999',
            'phone': '9876543999',
            'panchayat': self.panchayat.id,
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertTrue(any("already has a Panchayat President" in err for err in form.errors["__all__"]))

        # 2. Test duplicate Ward Member
        self.villager.role = Role.WARD_MEMBER
        self.villager.ward = self.ward_1
        self.villager.save()
        
        form_data = {
            'username': 'member2@example.com',
            'email': 'member2@example.com',
            'role': Role.WARD_MEMBER,
            'name': 'Member 2',
            'aadhar_id': '888888888888',
            'phone': '9876543888',
            'panchayat': self.panchayat.id,
            'ward': self.ward_1.id,
            'password': 'password123',
            'confirm_password': 'password123',
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertTrue(any("already has a Ward Representative" in err for err in form.errors["__all__"]))


class AlertManagementTests(TestCase):

    def setUp(self):
        # Set up geography
        self.taluk = Taluk.objects.create(name="Central Taluk")
        self.panchayat_a = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.panchayat_b = Panchayat.objects.create(name="Panchayat B", taluk=self.taluk)
        self.ward_a1 = Ward.objects.create(number=1, name="Ward A1", panchayat=self.panchayat_a)
        self.ward_a2 = Ward.objects.create(number=2, name="Ward A2", panchayat=self.panchayat_a)

        # Users
        self.president = User.objects.create_user(
            username='pres@example.com', email='pres@example.com', password='password123',
            name='President A', role=Role.PANCHAYAT_PRESIDENT, panchayat=self.panchayat_a,
            phone='9876543000', aadhar_id='999999000000', age=45
        )
        self.ward_member = User.objects.create_user(
            username='wm@example.com', email='wm@example.com', password='password123',
            name='Member A1', role=Role.WARD_MEMBER, panchayat=self.panchayat_a, ward=self.ward_a1,
            phone='9876543001', aadhar_id='999999000001', age=30
        )
        self.villager = User.objects.create_user(
            username='vil@example.com', email='vil@example.com', password='password123',
            name='Villager A1', role=Role.VILLAGER, panchayat=self.panchayat_a, ward=self.ward_a1,
            phone='9876543002', aadhar_id='999999000002', age=25
        )

        # Alerts
        self.alert_panchayat = Alert.objects.create(
            author=self.president, title="Panchayat Alert", content="Panchayat critical update",
            category=AlertCategory.EMERGENCY, scope=PostScope.PANCHAYAT, panchayat=self.panchayat_a
        )
        self.alert_ward_a1 = Alert.objects.create(
            author=self.ward_member, title="Ward 1 Alert", content="Ward 1 announcement",
            category=AlertCategory.GENERAL, scope=PostScope.WARD, panchayat=self.panchayat_a, ward=self.ward_a1
        )
        self.alert_ward_a2 = Alert.objects.create(
            author=self.president, title="Ward 2 Alert", content="Ward 2 announcement",
            category=AlertCategory.HEALTH, scope=PostScope.WARD, panchayat=self.panchayat_a, ward=self.ward_a2
        )

    def test_alert_visibility(self):
        # Villager in Ward A1 should see:
        # - Panchayat Alert
        # - Ward 1 Alert
        # But not Ward 2 Alert
        self.client.force_login(self.villager)
        response = self.client.get(reverse('alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alert_panchayat.title)
        self.assertContains(response, self.alert_ward_a1.title)
        self.assertNotContains(response, self.alert_ward_a2.title)

    def test_villager_cannot_manage_alerts(self):
        self.client.force_login(self.villager)
        
        # Cannot access create view
        response = self.client.get(reverse('create_alert'))
        self.assertRedirects(response, reverse('alerts'))
        
        # Cannot post to create view
        create_data = {'title': 'Villager Alert', 'category': AlertCategory.GENERAL}
        response = self.client.post(reverse('create_alert'), data=create_data)
        self.assertRedirects(response, reverse('alerts'))
        self.assertEqual(Alert.objects.filter(title='Villager Alert').count(), 0)

    def test_alert_crud_flows(self):
        self.client.force_login(self.ward_member)
        
        # 1. Create alert
        create_data = {
            'title': 'New WM Alert',
            'category': AlertCategory.EMERGENCY
        }
        response = self.client.post(reverse('create_alert'), data=create_data)
        self.assertRedirects(response, reverse('alerts'))
        new_alert = Alert.objects.get(title='New WM Alert')
        self.assertEqual(new_alert.scope, PostScope.WARD)
        self.assertEqual(new_alert.ward, self.ward_a1)

        # 2. Edit own alert
        edit_data = {
            'title': 'New WM Alert Updated',
            'category': AlertCategory.EMERGENCY
        }
        response = self.client.post(reverse('edit_alert', args=[new_alert.id]), data=edit_data)
        self.assertRedirects(response, reverse('alerts'))
        new_alert.refresh_from_db()
        self.assertEqual(new_alert.title, 'New WM Alert Updated')

        # 3. Cannot edit other member's alert
        response = self.client.post(reverse('edit_alert', args=[self.alert_panchayat.id]), data={'title': 'Hacked'})
        self.assertRedirects(response, reverse('alerts'))
        self.alert_panchayat.refresh_from_db()
        self.assertNotEqual(self.alert_panchayat.title, 'Hacked')

        # 4. Delete own alert
        response = self.client.post(reverse('delete_alert', args=[new_alert.id]))
        self.assertRedirects(response, reverse('alerts'))
        self.assertFalse(Alert.objects.filter(id=new_alert.id).exists())

    def test_panchayat_president_management(self):
        self.client.force_login(self.president)
        
        # Create Panchayat alert
        create_data = {
            'title': 'New Pres Alert',
            'category': AlertCategory.EMERGENCY,
            'scope': PostScope.PANCHAYAT
        }
        response = self.client.post(reverse('create_alert'), data=create_data)
        self.assertRedirects(response, reverse('alerts'))
        new_alert = Alert.objects.get(title='New Pres Alert')
        self.assertEqual(new_alert.scope, PostScope.PANCHAYAT)

        # President can delete ward member's alert in their Panchayat
        response = self.client.post(reverse('delete_alert', args=[self.alert_ward_a1.id]))
        self.assertRedirects(response, reverse('alerts'))
        self.assertFalse(Alert.objects.filter(id=self.alert_ward_a1.id).exists())

    def test_alert_filtering_and_pagination(self):
        self.client.force_login(self.president)
        
        # Clear database alerts for precise pagination testing
        Alert.objects.all().delete()
        
        # Create 15 alerts (5 health, 5 emergency, 5 development) spanning different scopes
        alerts_to_create = []
        for i in range(15):
            category = AlertCategory.HEALTH if i % 3 == 0 else (AlertCategory.EMERGENCY if i % 3 == 1 else AlertCategory.DEVELOPMENT)
            scope = PostScope.PANCHAYAT if i % 2 == 0 else PostScope.WARD
            alerts_to_create.append(
                Alert(
                    author=self.president,
                    title=f"Alert {i}",
                    category=category,
                    scope=scope,
                    panchayat=self.panchayat_a
                )
            )
        Alert.objects.bulk_create(alerts_to_create)
        
        # Verify pagination after 10
        response = self.client.get(reverse('alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['alerts']), 10)
        
        # Filter by category HEALTH
        response = self.client.get(reverse('alerts') + '?category=HEALTH')
        self.assertEqual(len(response.context['alerts']), 5)
        
        # Filter by scope WARD
        response = self.client.get(reverse('alerts') + '?scope=WARD')
        self.assertEqual(len(response.context['alerts']), 7)

    def test_duplicate_alert_validation(self):
        # Clean setup alert
        self.client.force_login(self.president)
        Alert.objects.all().delete()
        
        # Initial Alert
        Alert.objects.create(
            author=self.president, title="Duplicated Alert",
            category=AlertCategory.EMERGENCY, scope=PostScope.PANCHAYAT, panchayat=self.panchayat_a
        )
        
        # Try to post duplicate alert (expect error messages rendered or validation error)
        create_data = {
            'title': 'Duplicated Alert',
            'category': AlertCategory.EMERGENCY,
            'scope': PostScope.PANCHAYAT
        }
        response = self.client.post(reverse('create_alert'), data=create_data)
        # Should re-render form with error message (does not redirect) or return validation fail logs
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Alert.objects.filter(title='Duplicated Alert').count(), 1)

    def test_title_length_limit(self):
        self.client.force_login(self.president)
        
        long_title = "A" * 151
        create_data = {
            'title': long_title,
            'category': AlertCategory.GENERAL,
            'scope': PostScope.PANCHAYAT
        }
        response = self.client.post(reverse('create_alert'), data=create_data)
        # Should not redirect, stays on form page indicating failure
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Alert.objects.filter(title=long_title).count(), 0)


from django.core.files.uploadedfile import SimpleUploadedFile

class DocumentManagementTests(TestCase):

    def setUp(self):
        # Set up geography
        self.taluk = Taluk.objects.create(name="Central Taluk")
        self.panchayat_a = Panchayat.objects.create(name="Panchayat A", taluk=self.taluk)
        self.panchayat_b = Panchayat.objects.create(name="Panchayat B", taluk=self.taluk)
        self.ward_a1 = Ward.objects.create(number=1, name="Ward A1", panchayat=self.panchayat_a)
        self.ward_a2 = Ward.objects.create(number=2, name="Ward A2", panchayat=self.panchayat_a)

        # Users
        self.president = User.objects.create_user(
            username='pres@example.com', email='pres@example.com', password='password123',
            name='President A', role=Role.PANCHAYAT_PRESIDENT, panchayat=self.panchayat_a,
            phone='9876543000', aadhar_id='999999000000', age=45
        )
        self.ward_member = User.objects.create_user(
            username='wm@example.com', email='wm@example.com', password='password123',
            name='Member A1', role=Role.WARD_MEMBER, panchayat=self.panchayat_a, ward=self.ward_a1,
            phone='9876543001', aadhar_id='999999000001', age=30
        )
        self.villager = User.objects.create_user(
            username='vil@example.com', email='vil@example.com', password='password123',
            name='Villager A1', role=Role.VILLAGER, panchayat=self.panchayat_a, ward=self.ward_a1,
            phone='9876543002', aadhar_id='999999000002', age=25
        )

        from .models import Document, DocumentCategory
        self.test_file_1 = SimpleUploadedFile("test_doc.pdf", b"file_content_1", content_type="application/pdf")
        self.test_file_2 = SimpleUploadedFile("test_doc_2.pdf", b"file_content_2", content_type="application/pdf")

        # Documents
        self.doc_panchayat = Document.objects.create(
            author=self.president, title="Panchayat Circular", file=self.test_file_1,
            category=DocumentCategory.CIRCULAR, scope=PostScope.PANCHAYAT, panchayat=self.panchayat_a
        )
        self.doc_ward_a1 = Document.objects.create(
            author=self.ward_member, title="Ward 1 Notice", file=self.test_file_1,
            category=DocumentCategory.NOTICE, scope=PostScope.WARD, panchayat=self.panchayat_a, ward=self.ward_a1
        )
        self.doc_ward_a2 = Document.objects.create(
            author=self.president, title="Ward 2 Form", file=self.test_file_1,
            category=DocumentCategory.FORM, scope=PostScope.WARD, panchayat=self.panchayat_a, ward=self.ward_a2
        )

    def test_document_visibility(self):
        # Villager in Ward A1 should see Panchayat Circular and Ward 1 Notice, but not Ward 2 Form
        self.client.force_login(self.villager)
        response = self.client.get(reverse('documents'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doc_panchayat.title)
        self.assertContains(response, self.doc_ward_a1.title)
        self.assertNotContains(response, self.doc_ward_a2.title)

    def test_villager_cannot_manage_documents(self):
        self.client.force_login(self.villager)
        
        # Cannot access upload view
        response = self.client.get(reverse('upload_document'))
        self.assertRedirects(response, reverse('documents'))
        
        # Cannot post to upload view
        upload_data = {'title': 'Villager Doc', 'category': 'CIRCULAR'}
        response = self.client.post(reverse('upload_document'), data=upload_data)
        self.assertRedirects(response, reverse('documents'))
        from .models import Document
        self.assertEqual(Document.objects.filter(title='Villager Doc').count(), 0)

    def test_document_crud_flows(self):
        self.client.force_login(self.ward_member)
        from .models import Document, DocumentCategory

        # 1. Upload document
        upload_data = {
            'title': 'Elected Member Doc',
            'category': DocumentCategory.CIRCULAR,
            'file': self.test_file_2
        }
        response = self.client.post(reverse('upload_document'), data=upload_data)
        self.assertRedirects(response, reverse('documents'))
        
        new_doc = Document.objects.get(title='Elected Member Doc')
        self.assertEqual(new_doc.author, self.ward_member)
        self.assertEqual(new_doc.scope, PostScope.WARD) # Automatically WARD for ward member

        # 2. Edit document
        edit_data = {
            'title': 'Updated Member Doc',
            'category': DocumentCategory.FORM
        }
        response = self.client.post(reverse('edit_document', args=[new_doc.id]), data=edit_data)
        self.assertRedirects(response, reverse('documents'))
        
        new_doc.refresh_from_db()
        self.assertEqual(new_doc.title, 'Updated Member Doc')
        self.assertEqual(new_doc.category, DocumentCategory.FORM)

        # 3. Toggle pin document
        self.client.force_login(self.president)
        response = self.client.post(reverse('toggle_pin_document', args=[new_doc.id]))
        self.assertRedirects(response, reverse('documents'))
        new_doc.refresh_from_db()
        self.assertTrue(new_doc.is_pinned)

        # 4. Delete document
        response = self.client.post(reverse('delete_document', args=[new_doc.id]))
        self.assertRedirects(response, reverse('documents'))
        self.assertEqual(Document.objects.filter(id=new_doc.id).count(), 0)


class ComplaintTests(TestCase):

    def setUp(self):
        self.taluk = Taluk.objects.create(name="Central Taluk")
        self.panchayat = Panchayat.objects.create(name="Test Panchayat", taluk=self.taluk)
        self.ward_1 = Ward.objects.create(number=1, name="Ward 1", panchayat=self.panchayat)
        self.ward_2 = Ward.objects.create(number=2, name="Ward 2", panchayat=self.panchayat)

        self.villager = User.objects.create_user(
            username="villager@example.com",
            email="villager@example.com",
            password="password123",
            phone="9876543210",
            aadhar_id="111122223333",
            role=Role.VILLAGER,
            panchayat=self.panchayat,
            ward=self.ward_1
        )

        self.ward_member = User.objects.create_user(
            username="member1@example.com",
            email="member1@example.com",
            password="password123",
            phone="9876543211",
            aadhar_id="111122223334",
            role=Role.WARD_MEMBER,
            panchayat=self.panchayat,
            ward=self.ward_1
        )

        self.president = User.objects.create_user(
            username="president@example.com",
            email="president@example.com",
            password="password123",
            phone="9876543212",
            aadhar_id="111122223335",
            role=Role.PANCHAYAT_PRESIDENT,
            panchayat=self.panchayat,
            ward=self.ward_2
        )


    def test_lodge_complaint_and_recipient_resolution(self):
        self.client.force_login(self.villager)

        response = self.client.post(reverse('create_complaint'), {
            'subject': 'Water Leakage in Ward 1',
            'category': ComplaintCategory.WATER,
            'description': 'Main pipeline leaking near the water tank.',
        })

        self.assertRedirects(response, reverse('complaints'))
        self.assertEqual(Complaint.objects.count(), 1)

        complaint = Complaint.objects.first()
        self.assertEqual(complaint.subject, 'Water Leakage in Ward 1')
        self.assertEqual(complaint.villager, self.villager)
        self.assertEqual(complaint.recipient, self.ward_member)
        self.assertEqual(complaint.status, ComplaintStatus.PENDING)

    def test_update_complaint_status_by_ward_member(self):
        complaint = Complaint.objects.create(
            villager=self.villager,
            recipient=self.ward_member,
            subject='Broken Street Light',
            category=ComplaintCategory.ELECTRICITY,
            description='Streetlight #4 is flicking and off.',
            status=ComplaintStatus.PENDING,
            panchayat=self.panchayat,
            ward=self.ward_1
        )

        self.client.force_login(self.ward_member)

        # Access detail page
        response = self.client.get(reverse('complaint_detail', args=[complaint.id]))
        self.assertEqual(response.status_code, 200)

        # Update status to SOLVED
        update_response = self.client.post(reverse('update_complaint_status', args=[complaint.id]), {
            'status': ComplaintStatus.SOLVED
        })
        self.assertRedirects(update_response, reverse('complaint_detail', args=[complaint.id]))

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, ComplaintStatus.SOLVED)





