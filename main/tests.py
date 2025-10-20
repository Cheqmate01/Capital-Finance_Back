from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
import base64
from rest_framework.test import APIClient

User = get_user_model()


class ProfileEndpointTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(username='tester', password='testpass', full_name='Test User')
		# Authenticate the APIClient for DRF requests
		self.client.force_authenticate(user=self.user)

	def test_get_profile(self):
		url = reverse('profile')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertIn('username', resp.json())

	def test_patch_profile_json(self):
		url = reverse('profile')
		resp = self.client.patch(url, data={'full_name': 'New Name'}, format='json')
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertEqual(data.get('full_name'), 'New Name')

	def test_patch_profile_multipart(self):
		url = reverse('profile')
		# create a small valid PNG (1x1 transparent) via base64
		png_b64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
		png_bytes = base64.b64decode(png_b64)
		upload = SimpleUploadedFile('avatar.png', png_bytes, content_type='image/png')
		resp = self.client.patch(url, data={'profile_picture': upload}, format='multipart')
		# If it failed, print response content to help debug
		if resp.status_code != 200:
			print('\nDEBUG MULTIPART RESP STATUS:', resp.status_code)
			print('DEBUG MULTIPART RESP CONTENT:', resp.content)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIsInstance(data, dict)
