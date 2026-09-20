from django import template

register = template.Library()


@register.filter(name="addclass")
def addclass(value, arg):
    widget_type = value.field.widget.__class__.__name__
    css_class = "form-check-input" if widget_type == "CheckboxInput" else arg
    if widget_type == "CheckboxInput":
        return value.as_widget(attrs={"class": css_class})
    existing = value.field.widget.attrs.get("class", "")
    return value.as_widget(attrs={"class": f"{existing} {arg}".strip()})
