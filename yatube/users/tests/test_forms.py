from django.test import TestCase
from users.forms import CreationForm
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-username')
        # Создаем форму, если нужна проверка атрибутов
        cls.form = CreationForm()

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_create_user_correct_form(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'test_first_name',
            'last_name': 'test_last_name',
            'username': 'test_form_username',
            'email': 'example@mail.com',
            'password1': 'tre1875ju30',
            'password2': 'tre1875ju30',
        }
        response = self.client.post(
            reverse('users:signup'), data=form_data, follow=True
        )
        users = User.objects.all()
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:index'))
        # Проверяем, увеличилось ли число пользователей
        self.assertEqual(users.count(), users_count + 1)
        # Проверяем, что создался пользователь с заданными данными
        self.assertTrue(User.objects.filter(
            first_name='test_first_name',
            last_name='test_last_name',
            username='test_form_username',
            email='example@mail.com'
        ).exists()
        )
