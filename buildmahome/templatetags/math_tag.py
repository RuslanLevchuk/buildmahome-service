from django import template

register = template.Library()


@register.filter
def add(value, argument):
    return value + argument


@register.filter
def subtract(value, argument):
    return value - argument
