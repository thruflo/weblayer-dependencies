#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" :py:mod:`weblayer.request` provides :py:class:`RequestHandler`, an
  implementation of :py:class:`~weblayer.interfaces.IRequestHandler`.
  
  :py:class:`RequestHandler` is designed to be used as a base class in which
  you can write code that handles incoming requests to a web application, as
  per::
  
      class Hello(RequestHandler):
          def get(self, world):
              return u'hello %s' % world
              
          
      
  
  The main point being to take advantage of the :ref:`request handler api`
  that the class provides.
"""

__all__ = [
    'RequestHandler'
]

import logging
from os.path import dirname, join as join_path

import webob.exc as webob_exceptions

from zope.component import adapts
from zope.interface import implements

from component import registry

from interfaces import IRequest, IResponse, IRequestHandler
from interfaces import ISettings
from interfaces import ITemplateRenderer, IStaticURLGenerator
from interfaces import IAuthenticationManager, ISecureCookieWrapper
from interfaces import IMethodSelector, IResponseNormaliser

from settings import require_setting
from utils import encode_to_utf8, generate_hash, xhtml_escape

require_setting('check_xsrf', default=True)

class XSRFError(ValueError):
    """ Raised when xsrf validation fails.
    """
    

class BaseHandler(object):
    """ A request handler (aka view class) implementation.
    """
    
    adapts(IRequest, IResponse, ISettings)
    implements(IRequestHandler)
    
    check_xsrf = True
    
    def __init__(
            self, 
            request,
            response,
            settings,
            template_renderer_adapter=None,
            static_url_generator_adapter=None,
            authentication_manager_adapter=None,
            secure_cookie_wrapper_adapter=None,
            method_selector_adapter=None,
            response_normaliser_adapter=None
        ):
        """
        """
        
        self.request = request
        self.response = response
        self.settings = settings
        
        if template_renderer_adapter is None:
            self.template_renderer = registry.getAdapter(
                self.settings, 
                ITemplateRenderer
            )
        else:
            self.template_renderer = template_renderer_adapter(self.settings)
        
        if static_url_generator_adapter is None:
            self.static = registry.getMultiAdapter((
                    self.request, 
                    self.settings
                ),
                IStaticURLGenerator
            )
        else:
            self.static = static_url_generator_adapter(
                self.request, 
                self.settings
            )
        
        if authentication_manager_adapter is None:
            self.auth = registry.getAdapter(
                self.request, 
                IAuthenticationManager
            )
        else:
            self.auth = authentication_manager_adapter(self.request)
        
        if secure_cookie_wrapper_adapter is None:
            self.cookies = registry.getMultiAdapter((
                    self.request,
                    self.response,
                    self.settings
                ),
                ISecureCookieWrapper
            )
        else:
            self.cookies = secure_cookie_wrapper_adapter(
                self.request,
                self.response,
                self.settings
            )
        
        if method_selector_adapter is None:
            self._method_selector = registry.getAdapter(self, IMethodSelector)
        else:
            self._method_selector = method_selector_adapter(self)
        
        self._response_normaliser_adapter = response_normaliser_adapter
        
    
    def __call__(self, method_name, *args, **kwargs):
        """
        """
        
        method = self._method_selector.select_method(method_name)
        
        if method is None:
            handler_response = self.handle_method_not_found(method_name)
        else:
            try:
                if self.check_xsrf and self.settings["check_xsrf"]:
                    self.xsrf_validate()
            except XSRFError, err:
                handler_response = self.handle_xsrf_error(err)
            else:
                try:
                    handler_response = method(*args, **kwargs)
                except webob_exceptions.HTTPException, err:
                    handler_response = self.error(exception=err)
                except Exception, err:
                    if self.request.environ.get('paste.throw_errors', False):
                        raise
                    handler_response = self.handle_system_error(err)
            
        if self._response_normaliser_adapter is None:
            response_normaliser = registry.getAdapter(
                self.response, 
                IResponseNormaliser
            )
        else:
            response_normaliser = self._response_normaliser_adapter(
                self.response
            )
        
        return response_normaliser.normalise(handler_response)
        
    
    
    @property
    def xsrf_token(self):
        """ A token we can check to prevent `XSRF`_ attacks.
          
          .. _`xsrf`: http://en.wikipedia.org/wiki/Cross-site_request_forgery
        """
        
        if not hasattr(self, '_xsrf_token'):
            token = self.cookies.get('_xsrf')
            if not token:
                token = generate_hash()
                self.cookies.set('_xsrf', token, expires_days=None)
            self._xsrf_token = token
        return self._xsrf_token
        
    
    @property
    def xsrf_input(self):
        """ An HTML ``<input />`` element to be included with all POST forms.
        """
        
        if not hasattr(self, '_xsrf_input'):
            escaped = xhtml_escape(self.xsrf_token)
            tag = u'<input type="hidden" name="_xsrf" value="%s" />'
            self._xsrf_input = tag % escaped
        return self._xsrf_input
        
    
    def xsrf_validate(self):
        """ Raise an ``XSRFError`` if the ``_xsrf`` argument isn't present
          or if it doesn't match ``self.xsrf_token``.
        """
        
        if self.request.method.lower() != 'post':
            return None
        
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return None
        
        request_token = self.request.params.get('_xsrf', None)
        if request_token is None:
            raise XSRFError(u'`_xsrf` argument missing from POST')
            
        if request_token != self.xsrf_token:
            raise XSRFError(u'XSRF cookie does not match POST argument')
            
        
    
    
    def render(self, tmpl_name, **kwargs):
        """ Render the template called ``tmpl_name``, passing through the
          ``params`` and ``kwargs``.
        """
        
        params = dict(
            request=self.request,
            current_user=self.auth.current_user,
            get_static_url=self.static.get_url,
            xsrf_input=self.xsrf_input
        )
        params.update(kwargs)
        return self.template_renderer.render(tmpl_name, **params)
        
    
    def redirect(self, location, permanent=False, **kwargs):
        """ Redirect to ``location``.  The response status defaults to ``302``
          unless ``permanent`` is ``True``.
          
          ``kwargs`` (with ``kwargs['location']`` set to ``location`` are
          passed to the appropriate `webob_exception`_ class constructor.
          
          .. _`webob_exception`: http://pythonpaste.org/webob/module-webob.exc.html
        """
        
        status = permanent is True and 301 or 302
        kwargs['location'] = location
        
        ExceptionClass = webob_exceptions.status_map[status]
        exc = ExceptionClass(**kwargs)
        
        return self.request.get_response(exc)
        
    
    def error(self, exception=None, status=500, **kwargs):
        """ Return a response corresponding to either ``exception`` or (if 
          ``exception`` is ``None``) ``status``.  
          
          ``kwargs`` are passed to the appropriate `webob_exception_` 
          class constructor.
          
          .. note::
          
              Override this method to generate error messages that are more
              user friendly.
          
          .. _`webob_exception`: http://pythonpaste.org/webob/module-webob.exc.html
        """
        
        status = int(status)
        
        if exception is None:
            ExceptionClass = webob_exceptions.status_map[status]
            exception = ExceptionClass(**kwargs)
        
        return self.request.get_response(exception)
        
    
    
    def handle_method_not_found(self, method_name):
        """ Log a warning and return "405 Method Not Allowed".
        """
        
        logging.warning(u'%s method not found' % method_name)
        return self.error(status=405)
        
    
    def handle_xsrf_error(self, err):
        """ Log a warning and return "403 Forbidden".
        """
        
        logging.warning(err)
        return self.error(status=403)
        
    
    def handle_system_error(self, err):
        """ Log the error and return "500 Internal Server Error".
        """
        
        logging.error(err, exc_info=True)
        return self.error(status=500)
        
    
    

class RequestHandler(BaseHandler):
    """ A request handler (aka view class) implementation.
      
      Accepts GET and HEAD requests by default, when used in tandem with an 
      :py:class:`~weblayer.method.ExposedMethodSelector` (or any method selector 
      implementation that checks to see if the request method name is listed in 
      ``RequestHandler.__all__``).
    """
    
    __all__ = (
        'head', 
        'get'
    )
    

