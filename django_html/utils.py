import re
from django_html.enums import html_doctypes

xhtml_end_re = re.compile('\s*/>', re.UNICODE )

def clean_html(html, doctype):
    if doctype in html_doctypes:
        html = xhtml_end_re.sub('>', html)
    return html