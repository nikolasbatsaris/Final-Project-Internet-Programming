from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={**field.field.widget.attrs, 'class': css, 'required': 'required'})

@register.filter
def dict_get(d, k):
    return d.get(k, None) 