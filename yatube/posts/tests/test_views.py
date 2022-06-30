from django.core.cache import cache
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm

from ..models import Follow, Comment, Group, Post
from django import forms


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
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

        post_list = []
        for i in range(14):
            post = Post(
                id=i,
                text=f'Тестовый текст {i}',
                group=cls.group,
                author=cls.user,
                image=uploaded
            )
            post_list.append(post)
        cls.post_list = Post.objects.bulk_create(post_list)
        cls.post = cls.post_list[13]

    def setUp(self) -> None:
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'NoName'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
        }

        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['posts'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.author, self.post.author)
        self.assertTrue(first_object.image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertEqual(first_object.author, self.post.author)
        self.assertTrue(first_object.image, self.post.image)

    def test_profile_list_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'NoName'})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(response.context['author'].username, 'NoName')
        self.assertEqual(first_object.text, self.post.text)
        self.assertTrue(first_object.image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {'text': forms.fields.CharField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_post_detail_list_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        object_post = response.context['post_list']
        self.assertEqual(object_post, self.post)
        self.assertTrue(object_post.image, self.post.image)

    def test_paginator_first_page(self):
        """Тест паджинатора на страницах index, group_list and profile"""
        list_url = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'NoName'}
            ): 'posts/profile.html',
        }
        for test_page in list_url.keys():
            response = self.client.get(test_page)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 10
            )


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание тестовых данных"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.form = CommentForm()

    def test_add_comment_authorized_user_can_leave_comment(self):
        """Авторизованный юзер может оставить комментарий к посту."""
        # Считаем кол-во комментов к новому посту (0 шт.)
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        # Добавляем новый комент к посту (+1 шт.)
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        # Сравниваем кол-во изначальных комментов
        # c кол-вом получившихся
        self.assertNotEqual(Comment.objects.count(), comment_count)

    def test_add_comment_guest_user_cant_leave_comment(self):
        """Не авторизованный юзер не может оставить комментарий к посту."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_index_page_cache(self):
        """Тестирование кеширования галавной страницы"""
        # Запрос к главной странице
        response = self.authorized_client.get(reverse('posts:index'))
        # Создание поста
        Post.objects.create(
            text='Тестовый текст для кэша',
        )
        # Запрос к главной странице после создания поста
        response_1 = self.authorized_client.get(reverse('posts:index'))
        # Сравнение 1го и 2го запроса на соответствие.
        # Если Equal, значит в кеше
        self.assertEqual(response.content, response_1.content)
        # Очистка кеша
        cache.clear()
        # Запрос к главной странице после очистки кеша
        response_2 = self.authorized_client.get(reverse('posts:index'))
        # Сравнение2 и 3го запроса.
        self.assertNotEqual(response_1.content, response_2.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание тестовых данных"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_1 = User.objects.create_user(username='NoName_1')
        cls.user_2 = User.objects.create_user(username='NoName_2')
        cls.guest_client = Client()
        cls.user_1_client = Client()
        cls.user_2_client = Client()
        cls.user_1_client.force_login(cls.user_1)
        cls.user_2_client.force_login(cls.user_2)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.following = Follow.objects.get_or_create(
            user=cls.user_1,
            author=cls.user,
        )

    def test_following_authorized_client(self):
        """Авторизованный пользователь может подписаться"""
        self.assertTrue(Follow.objects.filter(
            user=FollowTest.user_1,
            author=FollowTest.user).exists(),
        )

    def test_unfollowing_authorized_client(self):
        """Авторизованный пользователь может отписаться"""
        Follow.objects.filter(
            user=FollowTest.user_1,
            author=FollowTest.user
        ).delete()
        self.assertFalse(Follow.objects.filter(
            user=FollowTest.user_1,
            author=FollowTest.user).exists()
        )

    def test_new_post_in_following_page(self):
        """Пост появляется в ленте у тех, кто подписан."""
        response = self.user_1_client.get(reverse('posts:follow_index'))
        post_count = len(response.context.get('page_obj').object_list)
        Post.objects.create(
            text='Тестовый текст для нового поста',
            author=FollowTest.user,
        )
        response = self.user_1_client.get(reverse('posts:follow_index'))
        post_count1 = len(response.context.get('page_obj').object_list)
        self.assertEqual(post_count + 1, post_count1)

    def test_new_post_in_following_page(self):
        """Пост не появляется в ленте у тех, кто подписан."""
        response = self.user_2_client.get(reverse('posts:follow_index'))
        post_count = len(response.context.get('page_obj').object_list)
        Post.objects.create(
            text='Тестовый текст для нового поста',
            author=FollowTest.user,
        )
        response = self.user_2_client.get(reverse('posts:follow_index'))
        post_count1 = len(response.context.get('page_obj').object_list)
        self.assertEqual(post_count, post_count1)
