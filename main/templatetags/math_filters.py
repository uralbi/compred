from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    return int(value) * arg


@register.filter(name='discount')
def multiply(value, arg):
    return round(value * (100-arg)/100,-1)

@register.filter(name='str_strip')
def urlencode(value):
    val = value.replace('\r\n', ' ')
    return  val


@register.filter(name='no_spaces')
def no_spaces(value):
    val = value.replace(' ', '-')
    return  val