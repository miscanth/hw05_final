from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post
from django.urls import reverse
from django.conf import settings

User = get_user_model()


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности
        # адресов со slug, username и post_id
        cls.user = User.objects.create_user(
            username='test-username',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([
            Post(
                text=f'Пост номер {i}',
                author=cls.user,
                group=cls.group,
                pk=i
            ) for i in range(13)
        ])

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='uncle_Motya')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    # Проверка: количество постов на первой странице равно 10.
    def test_paginator_first_page(self):
        """Проверка работы паджинатора на
        страницах index, group_list и profile.
        """
        paginator_names = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.username}
            )
        }
        for reverse_name in paginator_names.values():
            response = self.client.get(reverse_name)
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(len(
                    response.context['page_obj']
                ), settings.QUANTITY_PAGINATE
                )

    # Проверка: на второй странице должно быть три поста.
    def test_paginator_second_page(self):
        """Проверка работы паджинатора на
        страницах index, group_list и profile.
        """
        paginator_names = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.username}
            )
        }
        for reverse_name in paginator_names.values():
            response = self.client.get(reverse_name + '?page=2')
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(len(
                    response.context['page_obj']
                ), (13 - settings.QUANTITY_PAGINATE)
                )
