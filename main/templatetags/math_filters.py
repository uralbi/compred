from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    return int(value) * arg


@register.filter(name='discount')
def multiply(value, arg):
    return round(value * (100-arg)/100,-1)
