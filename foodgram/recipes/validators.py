from django import forms


def validate_not_empty(value):
    if value == '':
        raise forms.ValidationError(
            'Укажите название рецепта.',
            params={'value': value},
        )
