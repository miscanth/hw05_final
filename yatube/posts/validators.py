from django import forms


def validate_not_empty(value):
    if value == '':
        raise forms.ValidationError(
            'А кто поле будет заполнять, Пушкин что ли?',
            params={'value': value},
        )
