"""
{% doctype "html4" %}
{% doctype "html4" silent %} # set internal doctype but do NOT output it
{% doctype "html4trans" %}
{% doctype "html5" %}
{% doctype "xhtml1" %}
{% doctype "xhtml1trans" %}

{% field form.name %} # Outputs correct widget based on current doctype
{% field form.name class="my-form-class" %} # Adds an attribute
"""
import re

from django_html.enums import doctypes, html_doctypes
from django_html.utils import clean_html

from django import template
from django.conf import settings

register = template.Library()

def do_doctype(parser, token):
    bits = token.split_contents()
    settings_doctype = getattr(settings, 'DOCTYPE', None)
    if len(bits) not in (1, 2, 3):
        raise template.TemplateSyntaxError, \
            "%r tag requires 1-2 arguments" % bits[0]
    if settings_doctype is None and len(bits) == 1:
        raise template.TemplateSyntaxError, \
            "%r DOCTYPE must be in settings or passed as an argument." \
                % bits[0]
    if len(bits) == 3 and bits[2] != 'silent':
        raise template.TemplateSyntaxError, \
            "If provided, %r tag second argument must be 'silent'" % bits[0]
    # If doctype is wrapped in quotes, they should balance
    if len(bits) == 1:
        doctype = settings_doctype
    else:
        doctype = bits[1]
    if doctype[0] in ('"', "'") and doctype[-1] != doctype[0]:
        raise template.TemplateSyntaxError, \
            "%r tag quotes need to balance" % bits[0]
    return DoctypeNode(doctype, is_silent = (len(bits) == 3))

class DoctypeNode(template.Node):
    def __init__(self, doctype, is_silent=False):
        self.doctype = doctype
        self.is_silent = is_silent
    
    def render(self, context):
        if self.doctype[0] in ('"', "'"):
            doctype = self.doctype[1:-1]
        else:
            try:
                doctype = template.resolve_variable(self.doctype, context)
            except template.VariableDoesNotExist:
                # Cheeky! Assume that they typed a doctype without quotes
                doctype = self.doctype
        # Set doctype in the context
        context._doctype = doctype
        if self.is_silent:
            return ''
        else:
            return doctypes.get(doctype, '')

register.tag('doctype', do_doctype)


class FieldNode(template.Node):
    def __init__(self, field_var, extra_attrs):
        self.field_var = field_var
        self.extra_attrs = extra_attrs
    
    def render(self, context):
        field = template.resolve_variable(self.field_var, context)
        # Caling bound_field.as_widget() returns the HTML, but we need to 
        # intercept this to manipulate the attributes - so we have to 
        # duplicate the logic from as_widget here.
        widget = field.field.widget
        attrs = self.extra_attrs or {}
        auto_id = field.auto_id
        if auto_id and 'id' not in attrs and 'id' not in widget.attrs:
            attrs['id'] = auto_id
        if not field.form.is_bound:
            data = field.form.initial.get(field.name, field.field.initial)
            if callable(data):
                data = data()
        else:
            data = field.data
        html = widget.render(field.html_name, data, attrs=attrs)
        # Finally, if we're NOT in xhtml mode ensure no '/>'
        doctype = getattr(context, '_doctype', 'xhtml1')
        return clean_html(html, doctype)

def do_field(parser, token):
    # Can't use split_contents here as we need to process 'class="foo"' etc
    bits = token.contents.split()
    if len(bits) == 1:
        raise template.TemplateSyntaxError, \
            "%r tag takes arguments" % bits[0]
    field_var = bits[1]
    extra_attrs = {}
    if len(bits) > 1:
        # There are extra name="value" arguments to consume
        extra_attrs = parse_extra_attrs(' '.join(bits[2:]))
    return FieldNode(field_var, extra_attrs)

register.tag('field', do_field)

extra_attrs_re = re.compile(r'''([a-zA-Z][0-9a-zA-Z_-]*)="(.*?)"\s*''')

def parse_extra_attrs(contents):
    """
    Input should be 'foo="bar" baz="bat"' - output is corresponding dict. 
    Raises TemplateSyntaxError if something is wrong with the input.
    """
    unwanted = extra_attrs_re.sub('', contents)
    if unwanted.strip():
        raise template.TemplateSyntaxError, \
            "Invalid field tag arguments: '%s'" % unwanted.strip()
    return dict(extra_attrs_re.findall(contents))
