from django import template

register = template.Library()


@register.inclusion_tag('parts/product_list_item.html')
def render_product(prod):
    return {'prod': prod}