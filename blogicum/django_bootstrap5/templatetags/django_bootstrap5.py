from django import template
from django.utils.html import format_html


register = template.Library()


@register.simple_tag
def bootstrap_button(button_type='submit', content=''):
    return format_html(
        '<button type="{}" class="btn btn-primary">{}</button>',
        button_type,
        content,
    )


@register.simple_tag
def bootstrap_form(form):
    return format_html('{}', form.as_p())


@register.simple_tag
def bootstrap_css():
    """Stub for django_bootstrap5 bootstrap_css tag."""
    return ''
