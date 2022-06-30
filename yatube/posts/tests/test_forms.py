import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Post

from ..models import Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание тестовых записей в таблицах Group, Post and User"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание тестовой группы',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
        )
        cls.form = PostForm()

        def setUp(self) -> None:
            cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в моделе Post."""
        # Подсчитаем количество записей в Post
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data, follow=True
        )
        # Проверяем, что создалась запись
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.id
            ).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'NoName'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Редактирование поста с последующим изменением записи в БД"""
        form_data = {
            'text': 'Отедактированный текст',
            'group': self.group.id
        }
        post = Post.objects.get(id=self.post.id)
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post.id]),
            data=form_data, follow=True
        )
        post_edit = Post.objects.get(id=self.post.id)
        self.assertEqual(post_edit.author, self.user)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, 'Отедактированный текст')
