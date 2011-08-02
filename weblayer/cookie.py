#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" :py:mod:`weblayer.cookie` provides :py:class:`SignedSecureCookieWrapper`,
  an implementation of :py:class:`~weblayer.interfaces.ISecureCookieWrapper`.
  
  :py:class:`SignedSecureCookieWrapper` provides two key methods,
  :py:meth:`~SignedSecureCookieWrapper.set` and 
  :py:meth:`~SignedSecureCookieWrapper.get` to set and get cookies whose value
  is signed using the required ``settings['cookie_secret']``.
  
  The resulting cookies are secure, in the sense that they can't be forged
  (without the forger knowing the ``settings['cookie_secret']``).  However,
  it's important to note that they are just as vulnerable to `sidejacking`_ as
  normal cookies.  The only way to secure cookies against `sidejacking`_ is to
  serve your application over `HTTPS`_ and that is a matter for web server 
  configuration, outside the scope of :ref:`weblayer`.
  
  .. _`sidejacking`: http://codebutler.com/firesheep
  .. _`https`: http://techcrunch.com/2010/10/25/firesheep/
"""

__all__ = [
    'SignedSecureCookieWrapper'
]

import base64
import datetime
import hashlib
import hmac
import logging
import time

from zope.component import adapts
from zope.interface import implements

from interfaces import IRequest, IResponse, ISettings
from interfaces import ISecureCookieWrapper
from settings import require_setting
from utils import encode_to_utf8

require_setting('cookie_secret', help='a long, random sequence of bytes')

def _time_independent_equals(a, b):
    """ Logically equal to ``a == b``::
      
          >>> _time_independent_equals('a', 'a')
          True
          >>> _time_independent_equals('b', u'b')
          True
          >>> _time_independent_equals('a', 'b')
          False
          >>> _time_independent_equals('abc', 'acb')
          False
      
      As long as you give it ``basestring``s::
      
          >>> _time_independent_equals(None, [])
          Traceback (most recent call last):
          ...
          ValueError: `None` must be a `basestring`
          >>> _time_independent_equals('a', [])
          Traceback (most recent call last):
          ...
          ValueError: `[]` must be a `basestring`
      
      But not vulnerable to 
      `timing attacks <http://seb.dbzteam.org/crypto/python-oauth-timing-hmac.pdf>`_.
    """
    
    if not isinstance(a, basestring):
        raise ValueError(u'`%s` must be a `basestring`' % a)
    
    if not isinstance(b, basestring):
        raise ValueError(u'`%s` must be a `basestring`' % b)
    
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    
    return result == 0
    

def _generate_cookie_signature(cookie_secret, *parts):
    """ Generate a secure cookie signature::
      
          >>> cookie_secret = ''
          >>> _generate_cookie_signature(cookie_secret)
          'fbdb1d1b18aa6c08324b7d64b71fb76370690e1d'
      
      All args after the first are passed to the hasher and must
      be str or unicode, with the unicode being encoded to utf-8::
      
          >>> parts = ['a', 'b', 'c']
          >>> _generate_cookie_signature(cookie_secret, *parts)
          '9b4a918f398d74d3e367970aba3cbe54e4d2b5d9'
          >>> parts.append(u'd')
          >>> _generate_cookie_signature(cookie_secret, *parts)
          'afa29ab8534495251ac8346a985717c54bc49c26'
          >>> parts.append([])
          >>> _generate_cookie_signature(cookie_secret, *parts) #doctest:+ELLIPSIS
          Traceback (most recent call last):
          ...
          ValueError: [] must be a `basestring`
      
    """
    
    hasher = hmac.new(cookie_secret, digestmod=hashlib.sha1)
    
    parts = [encode_to_utf8(part) for part in parts]
    for part in parts:
        hasher.update(part)
    
    return hasher.hexdigest()
    


class SignedSecureCookieWrapper(object):
    """ Adapts an :py:class:`~weblayer.interfaces.IRequest`, 
      :py:class:`~weblayer.interfaces.IResponse` and
      :py:class:`~weblayer.interfaces.ISettings` to provide methods to get
      and set cookies that can't be forged.
    """
    
    adapts(IRequest, IResponse, ISettings)
    implements(ISecureCookieWrapper)
    
    def __init__(self, request, response, settings):
        self.request = request
        self.response = response
        self._cookie_secret = settings['cookie_secret']
        
    
    def set(self, name, value, timestamp=None, expires_days=30, **kwargs):
        """ Signs and timestamps a cookie so it cannot be forged.
        """
        
        timestamp = timestamp and timestamp or str(int(time.time()))
        value = base64.b64encode(value)
        args = (name, value, timestamp)
        signature = _generate_cookie_signature(self._cookie_secret, *args)
        value = "|".join([value, timestamp, signature])
        
        max_age = None
        if expires_days:
            if not isinstance(expires_days, int):
                raise TypeError(u'%s must be an `int`' % expires_days)
            max_age = expires_days * 24 * 60 * 60
        
        return self.response.set_cookie(
            name, 
            value=value, 
            max_age=max_age, 
            **kwargs
        )
        
    
    def get(self, name, value=None):
        """ Returns the given signed cookie if it validates, or ``None``.
        """
        
        if value is None:
            value = self.request.cookies.get(name, None)
        
        if value is None:
            return None
        
        parts = value.split("|")
        if len(parts) != 3: 
            return None
        
        timestamp = int(parts[1])
        if timestamp < time.time() - 31 * 86400:
            logging.warning("Expired cookie %r", value)
            return None
        
        args = (name, parts[0], parts[1])
        signature = _generate_cookie_signature(self._cookie_secret, *args)
        
        if not _time_independent_equals(parts[2], signature):
            logging.warning("Invalid cookie signature %r", value)
            return None
        
        try:
            return base64.b64decode(parts[0])
        except TypeError:
            return None
        
    
    def delete(self, name, path="/", domain=None):
        """ Convenience method to clear a cookie.
        """
        
        self.response.set_cookie(
            name, 
            '', 
            path=path, 
            domain=domain, 
            max_age=0, 
            expires=datetime.timedelta(days=-5)
        )
        
    
    

