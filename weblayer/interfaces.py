#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" :py:mod:`weblayer.interfaces` provides `Interface`_ definitions that show
  the contracts that :ref:`weblayer`'s :ref:`components` implement and are
  registered against and looked up by through the :py:mod:`weblayer.component`
  :py:obj:`registry`.
  
  .. _`Interface`: http://pypi.python.org/pypi/zope.interface
"""

__all__ = [
    'IAuthenticationManager',
    'IMethodSelector',
    'IPathRouter',
    'IRequest',
    'IRequestHandler',
    'IResponse',
    'IResponseNormaliser',
    'ISecureCookieWrapper',
    'ISettings',
    'IStaticURLGenerator',
    'ITemplateRenderer',
    'IWSGIApplication'
]

from zope.interface import Attribute, Interface

class IAuthenticationManager(Interface):
    """ Authentication manager.  Default implementation is 
      :py:class:`~weblayer.auth.TrivialAuthenticationManager`. 
    """
    
    is_authenticated = Attribute(u'Boolean -- is there an authenticated user?')
    current_user = Attribute(u'The authenticated user, or `None`')
    

class IMethodSelector(Interface):
    """ Selects request handler methods by name.  Default implementation is 
      :py:class:`~weblayer.method.ExposedMethodSelector`.
    """
    
    def select_method(method_name):
        """ Return a method using :py:obj:`method_name`.
        """
        
    
    

class IPathRouter(Interface):
    """ Maps incoming requests to request handlers using the request path.
      Default implementation is :py:class:`~weblayer.route.RegExpPathRouter`.
    """
    
    def match(path):
        """ Return ``handler, args, kwargs`` from ``path``.
        """
        
    

class IRequest(Interface):
    """ A Request object, based on `webob.Request`_.  Default implementation
      is :py:class:`~weblayer.base.Request`.
      
      This interface details only the attributes of `webob.Request`_ that 
      :ref:`weblayer` uses by default, not the full interface `webob.Request`_
      actually provides.
      
      .. _`webob.Request`: http://pythonpaste.org/webob/reference.html#id1
    """
    
    url = Attribute(u'Full request URL, including QUERY_STRING')
    host = Attribute(u'HOST provided in HTTP_HOST w. fall-back to SERVER_NAME')
    host_url = Attribute(u'The URL through the HOST (no path)')
    application_url = Attribute(u'URL w. SCRIPT_NAME no PATH_INFO or QUERY_STRING')
    path_url = Attribute(u'URL w. SCRIPT_NAME & PATH_INFO no QUERY_STRING')
    path = Attribute(u'Path of the request, without HOST or QUERY_STRING')
    path_qs = Attribute(u'Path without HOST but with QUERY_STRING')
    
    headers = Attribute(u'Headers as case-insensitive dictionary-like object')
    params = Attribute(u'Dictionary-like obj of params from POST and QUERY_STRING')
    body = Attribute(u'Content of the request body.')
    
    cookies = Attribute(u'Dictionary of cookies found in the request')
    

class IRequestHandler(Interface):
    """ A request handler.  Default implementation is 
      :py:class:`~weblayer.request.RequestHandler`.
    """
    
    request = Attribute(u'Request instance')
    response = Attribute(u'Response instance')
    settings = Attribute(u'Settings instance')
    
    auth = Attribute(u'Authentication manager')
    cookies = Attribute(u'Cookie wrapper')
    static = Attribute(u'Static url generator')
    
    xsrf_token = Attribute(u'XSRF prevention token')
    xsrf_input = Attribute(u'``<input/>`` element to be included in forms.')
    def xsrf_validate():
        """ Validate against XSRF.
        """
        
    
    
    def render(tmpl_name, **kwargs):
        """ Render the template called ``tmpl_name``.
        """
        
    
    def redirect(url, status=302, content_type=None):
        """ Redirect to ``url``.
        """
        
    
    def error(status=500, body=u'System Error'):
        """ Clear response and return an error.
        """
        
    
    
    def __call__(method_name, *args, **kwargs):
        """ Call the appropriate method to return a response.
        """
        
    
    

class IResponse(Interface):
    """ A Response object, based on `webob.Response`_.  Default implementation
      is :py:class:`~weblayer.base.Response`.
      
      This interface details only the attributes of `webob.Response`_ that 
      :ref:`weblayer` uses by default, not the full interface `webob.Response`_
      actually provides.
      
      .. _`webob.Response`: http://pythonpaste.org/webob/reference.html#id2
    """
    
    headers = Attribute(u'The headers in a dictionary-like object')
    headerlist = Attribute(u'The list of response headers')
    
    body = Attribute(u'The body of the response, as a ``str``.')
    unicode_body = Attribute(u'The body of the response, as a ``unicode``.')
    
    content_type = Attribute(u'The `Content-Type` header')
    status = Attribute(u'The `status` string')
    
    def set_cookie(key, value='', **kwargs):
        """ Set ``value`` for cookie called ``key``.
        """
        
    
    

class IResponseNormaliser(Interface):
    """ Normalise the response provided by a request handler method.  Default
      implementation is 
      :py:class:`~weblayer.normalise.DefaultToJSONResponseNormaliser`.
    """
    
    def normalise(handler_response):
        """ Normalise ``handler_response``.
        """
        
    
    

class ISecureCookieWrapper(Interface):
    """ Get and set cookies that can't be forged.  Default implementation is
      :py:class:`~weblayer.cookie.SignedSecureCookieWrapper`.
    """
    
    def set(name, value, expires_days=30, **kwargs):
        """ Set cookie.
        """
        
    
    def get(name, include_name=True, value=None):
        """ Get cookie.
        """
        
    
    def delete(self, name, path="/", domain=None):
        """ Clear cookie.
        """
        
    
    

class ISettings(Interface):
    """ Provides dictionary-like access to global application settings.
      Default implementation is 
      :py:class:`~weblayer.settings.RequirableSettings`.
    """
    
    def __call__(items):
        """ Update with items.
        """
        
    
    
    def __getitem__(key):
        """ Get item.
        """
        
    
    def __setitem__(key, value):
        """ Set item.
        """
        
    
    def __delitem__(key):
        """ Delete item.
        """
        
    
    def __contains__(key):
        """ Return whether contains item.
        """
        
    
    def __iter__():
        """ Iterate through items.
        """
        
    
    def __repr__():
        """ Represent as a string.
        """
        
    
    def __cmp__(self, other):
        """ Compare against other.
        """
        
    
    def __len__(self):
        """ Return number of items.
        """
        
    
    def has_key(key):
        """ Has key.
        """
        
    
    def iteritems():
        """ Iter items.
        """
        
    
    def iterkeys():
        """ Iter keys.
        """
        
    
    def itervalues():
        """ Iter values.
        """
        
    
    def items():
        """ Items.
        """
        
    
    def keys():
        """ Keys.
        """
        
    
    def values():
        """ Values.
        """
    
    def clear():
        """ Clear items.
        """
        
    
    def setdefault(key, default=None):
        """ Set default.
        """
        
    
    def pop(key, *args):
        """ Pop.
        """
        
    
    def popitem():
        """ Pop item.
        """
        
    
    def update(other=None, **kwargs):
        """ Update.
        """
        
    
    def get(key, default=None):
        """ Get item if exists, or return ``default``.
        """
        
    
    


    
class IStaticURLGenerator(Interface):
    """ Static url generator.  Default implementation is 
      :py:class:`~weblayer.static.MemoryCachedStaticURLGenerator`.
    """
    
    def get_url(path):
        """ Get a fully expanded url for the given static resource ``path``.
        """
        
    
    

class ITemplateRenderer(Interface):
    """ A template renderer.  Default implementation is 
      :py:class:`~weblayer.template.MakoTemplateRenderer`.
    """
    
    def render(tmpl_name, **kwargs):
        """ Render the template called ``tmpl_name``.
        """
        
    
    

class IWSGIApplication(Interface):
    """ A callable WSGI application.  Default implementation is 
      :py:class:`~weblayer.wsgi.WSGIApplication`.
    """
    
    def __call__(environ, start_response):
        """ Handle a new request.
        """
        
    
    

