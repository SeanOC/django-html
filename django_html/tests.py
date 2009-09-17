from django import template
from django import forms
from django.http import HttpRequest, HttpResponse
from templatetags.html import doctypes, html_doctypes
from middleware import HTMLFixMiddleware
import unittest

class TemplateTestHelper(unittest.TestCase):
    def assertRenders(self, template_string, expected, context = None):
        context = context or {}
        actual = template.Template(template_string).render(
            template.Context(context)
        )
        self.assertEqual(expected, actual)

class DoctypeTest(TemplateTestHelper):
    
    def test_doctype(self):
        'Doctype tag with one argument should output a doctype'
        for doctype in doctypes:
            t = '{% load html %}{% doctype "!!!" %}'.replace('!!!', doctype)
            self.assertRenders(t, doctypes[doctype])
        t = '{% load html %}{% doctype "html5" %}'
        self.assertRenders(t, '<!DOCTYPE html>')
    
    def test_doctype_variable(self):
        'Doctype tag can take a variable as well as a hard-coded string'
        t = '{% load html %}{% doctype foo %}'
        self.assertRenders(t, '<!DOCTYPE html>', {'foo': 'html5'})
        self.assertRenders(t, doctypes['xhtml1'], {'foo': 'xhtml1'})
    
    def test_doctype_silent(self):
        "Optional 'silent' argument should NOT output doctype"
        context = template.Context({})
        self.assert_(not hasattr(context, '_doctype'))
        actual = template.Template(
            '{% load html %}{% doctype "html5" silent %}'
        ).render(context)
        self.assertEqual(actual, '')
        self.assert_(hasattr(context, '_doctype'))
        self.assertEqual(context._doctype, 'html5')

class MyForm(forms.Form):
    name = forms.CharField()
    happy = forms.BooleanField()
    select = forms.ChoiceField(choices=(
        ('a', 'Ape'),
        ('b', 'Bun'),
        ('c', 'Cog')
    ))

expected_select = """<select name="select" id="id_select">
<option value="a">Ape</option>
<option value="b">Bun</option>
<option value="c">Cog</option>
</select>"""

class FieldTest(TemplateTestHelper):
    
    def test_field_no_doctype(self):
        'Field tag should output in XHTML if no doctype'
        self.assertRenders(
            '{% load html %}{% field form.name %}',
            '<input type="text" name="name" id="id_name" />',
            {'form': MyForm()}
        )
    
    def test_field_xhtml1(self):
        'Field tag should output in XHTML if XHTML doctype'
        self.assertRenders(
            '{%load html%}{% doctype "xhtml1" silent %}{% field form.name %}',
            '<input type="text" name="name" id="id_name" />',
            {'form': MyForm()}
        )
        self.assertRenders(
            '{%load html%}{%doctype "xhtml1" silent %}{% field form.happy %}',
            '<input type="checkbox" name="happy" id="id_happy" />',
            {'form': MyForm()}
        )
    
    def test_field_html4(self):
        'No XHTML trailing slash in HTML4 mode'
        self.assertRenders(
            '{%load html%}{% doctype "html4" silent %}{% field form.name %}',
            '<input type="text" name="name" id="id_name">',
            {'form': MyForm()}
        )
        self.assertRenders(
            '{%load html %}{% doctype "html4" silent%}{% field form.happy %}',
            '<input type="checkbox" name="happy" id="id_happy">',
            {'form': MyForm()}
        )
        self.assertRenders(
            '{%load html%}{%doctype "html4" silent %}{% field form.select %}',
            expected_select,
            {'form': MyForm()}
        )
    
    def assertHasAttrs(self, template_string, context, expected_attrs):
        'Order of attributes is not garuanteed, so use this instead'
        actual = template.Template(template_string).render(
            template.Context(context)
        )
        for (attr, value) in expected_attrs.items():
            attrstring = '%s="%s"' % (attr, value)
            self.assert_(
                (attrstring in actual),
                'Did not find %s in %s' % (attrstring, actual)
            )

    def test_field_extra_attrs(self):
        self.assertHasAttrs(
            '{% load html %}{% doctype "html4" silent %}' +
            '{% field form.name class="hello" %}',
            {'form': MyForm()},
            {'class': 'hello', 'id': 'id_name'}
        )
        self.assertHasAttrs(
            '{% load html %}{% doctype "html4" silent %}' +
            '{% field form.happy class="foo" %}',
            {'form': MyForm()},
            {'type': 'checkbox', 'class': 'foo', 'id': 'id_happy'}
        )
        self.assertHasAttrs(
            '{% load html %}{% doctype "html4" silent %}' +
            '{% field form.select class="foo" %}',
            {'form': MyForm()},
            {'name': 'select', 'class': 'foo', 'id': 'id_select'}
        )
        self.assertHasAttrs(
            '{% load html %}{% doctype "html4" silent %}' +
            '{% field form.select class="foo" id="hi" %}',
            {'form': MyForm()},
            {'name': 'select', 'class': 'foo', 'id': 'hi'}
        )

xhtml_output = '''
<html>
    <body>
        <form>
            <input type="text" name="name" />
            <input type="hidden" name="other" />
        </form>
    </body>
</html>
'''

html_output = '''
<html>
    <body>
        <form>
            <input type="text" name="name">
            <input type="hidden" name="other">
        </form>
    </body>
</html>
'''
      
class MiddlewareTest(unittest.TestCase):
    def _get_request(self):
        return HttpRequest()
        
    def _get_xhtml_response(TestCase):
        return HttpResponse(content=xhtml_output)

    def test_simple_xhtml2xhtml(self):
        from django.conf import settings
        settings.DOCTYPE = 'xhtml1'
        request = self._get_request()
        orig_response = self._get_xhtml_response()
        processed_response = HTMLFixMiddleware().process_response(request, orig_response)
        self.assertEqual(processed_response.content, xhtml_output)
        
    def test_simple_xhtml2html4(self):
        from django.conf import settings
        settings.DOCTYPE = 'html4'
        request = self._get_request()
        orig_response = self._get_xhtml_response()
        processed_response = HTMLFixMiddleware().process_response(request, orig_response)
        self.assertEqual(processed_response.content, html_output)
        