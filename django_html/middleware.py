
from django.conf import settings
from django_html.enums import html_doctypes
from django_html.utils import clean_html

class HTMLFixMiddleware(object):
    def process_response(self, request, response):
        doctype = getattr(response, 'doctype', None)
        if doctype is None:
            doctype = getattr(settings, 'DOCTYPE', 'xhtml1')
            
        if doctype in html_doctypes:
            response.content = clean_html(response.content, doctype)
            
        return response