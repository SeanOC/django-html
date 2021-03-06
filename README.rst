===========
django_html
===========

This package represents an experimental approach to improving the way Django
outputs form widgets. At the moment, widgets created using `django.forms` are
outputted as XHTML (with self closing `/>` tags) even if the rest of your site
uses HTML. This package solves this problem by introducing two new template
tags: `{% doctype %}` and `{% field %}`.  Alternatively it also provides a middleware which strips out the self closing tags '/>'.  A middleware introduces more overhead than the `{% field %}` tags but it allows for handling of third party apps without modification.

To install, place the `django_html` directory somewhere on your python path,
then add `django_html` to `INSTALLED_APPS` in your `settings.py` file.

To enable the middleware, follow the steps above and then add `'django_html.middleware.HTMLFixMiddleware'` to your `MIDDLEWARE_CLASSES` value in `settings.py`.  Finally add a line similar to `DOCTYPE = "html4"` to your `settings.py` file.  The `DOCTYPE` setting accepts any value which can be used in the `{% doctype %}` tag.

See the following thread on django-developers for further background
information:

    http://groups.google.com/group/django-developers/browse_thread/thread/5f3694b8a19fb9a1/

{% doctype %}
=============
The doctype tag does two things: it outputs the relevant doctype and it stores
your chosen doctype in `context._doctype`. Example usage::

	{% load html %}{% doctype "html4" %}

This will output::

	<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
	    "http://www.w3.org/TR/html4/strict.dtd">

It will also set the context's doctype to "html4". Other template tags can then
take that in to account when deciding how they should render.

If you just want to set the doctype without outputting it to the page you can
use the optional "silent" argument::

	{% doctype "html4" silent %}
	
If you have set the `DOCTYPE` settings variable, you can simply call the doctype tag with no arguement to output the doctype info to the page::

    {% doctype %}

{%_field_%}
===========

The field tag allows you to output `django.forms` widgets taking the current
active doctype in to account. Django outputs XHTML form widgets by default but
this may not be appropriate if your site uses HTML 4. Here's how you output a
form widget with stock Django::

	<label for="id_name">Name:</label> {{ form.name }}

This will always output as XHTML. Here's how you use the new `{% field %}` tag::

	<label for="id_name">Name:</label> {% field form.name %}

Now the current doctype (as set using the {% doctype %} tag) will be used to
decide if XHTML self-closing tags should be used by the widget.

The field tag also lets you specify extra HTML attributes for a form field from
within your template (useful for adding things like extra classes without
having to modify the form definition in your Python code)::

	<label for="id_name">Name:</label> {% field form.name class="myclass" %}

With an HTML doctype, this will render as::

	<input type="text" name="name" id="id_name" class="myclass">

If your doctype is XHTML, you will get::

	<input type="text" name="name" id="id_name" class="myclass" />

