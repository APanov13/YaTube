from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание тестовых записей в таблицах Group, Post and User"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName2')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_slug_url_exists_at_desired_location(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test_slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_username_url_exists_at_desired_location(self):
        """Страница /profile/<username>/ доступна любому пользователю."""
        response = self.guest_client.get('/profile/NoName2/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/ доступна любому пользователю."""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_url_exists_at_desired_location(self):
        """Страница /posts/create/ доступна авторизированному пользователю."""
        response = self.authorized_client.get('/posts/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/edit/ доступна автору."""
        response = self.guest_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexsiting_page_url_exists_at_desired_location(self):
        """Не существующая страница."""
        response = self.guest_client.get('/unexsiting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/': 'posts/post_detail.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/NoName2/': 'posts/profile.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
