import webapp2
from webapp2_extras import json
from collections import OrderedDict as odict
from jinja2 import Environment,FileSystemLoader
import hashlib
import logging
from data import *

_maxint = 2147483647

jenv = Environment(loader=FileSystemLoader('templates'))

errorMsgs = [json.encode(odict([
  ('error','syntax error'),
  ('help','{{}}/api/help')
])),json.encode(odict([
  ('error','system id not available'),
])),json.encode(odict([
  ('error','corporation id not available'),
])),json.encode(odict([
  ('error','securityMask out of range'),
]))]

templates = {
  'helpMsg':jenv.get_template('help.html')
}
cache = {
  'loader':{
    'body':jenv.get_template('loader.html').render({
      'datasetname':datasetname,
      'solarSystemsIdOffset':30000000,
      'corporationsIdOffset':1000000,
    })
  },
  'app':{
    'body':jenv.get_template('app.html').render({
      'solarSystems':solarSystems,
      'solarSystemsSorted':solarSystemsSorted,
      'solarSystemsIdOffset':30000000,
      'solarSystemsDefault':30000142, # Jita
      'corporations':corporations,
      'corporationsSorted':corporationsSorted,
      'corporationsIdOffset':1000000,
      'corporationsDefault':1000125 # CONCORD
    })
  }
}
for v in cache.viewvalues():
  v['etag'] = hashlib.md5(v['body']).hexdigest()

class CronHandler(webapp2.RequestHandler):
  def get(self):
    pass

class LoaderHandler(webapp2.RequestHandler):
  def get(self):
    serve = True
    if 'If-None-Match' in self.request.headers:
      etags = [x.strip('" ') for x in self.request.headers['If-None-Match'].split(',')]
      if cache['loader']['etag'] in etags:
        serve = False
    self.response.headers['ETag'] = '"{}"'.format(cache['loader']['etag'])
    if serve:
      self.response.write(cache['loader']['body'])
    else:
      self.response.set_status(304)

class AppHandler(webapp2.RequestHandler):
  def get(self):
    serve = True
    if 'If-None-Match' in self.request.headers:
      etags = [x.strip('" ') for x in self.request.headers['If-None-Match'].split(',')]
      if cache['app']['etag'] in etags:
        serve = False
    self.response.headers['ETag'] = '"{}"'.format(cache['app']['etag'])
    if serve:
      self.response.write(cache['app']['body'])
    else:
      self.response.set_status(304)

class HelpHandler(webapp2.RequestHandler):
  def get(self):
    self.response.write(templates['helpMsg'].render({'host_url':self.request.host_url}))

class ApiHandler(webapp2.RequestHandler):
  def get(self, system, corporation, securityMask):
    response = self.response
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers.add_header('Access-Control-Allow-Origin', '*')
    
    try:
      system = int(system)
      corporation = int(corporation)
      securityMask = int(securityMask)
    except TypeError:
      response.set_status(400)
      response.write(errorMsgs[0].replace('{{}}',self.request.host_url))
      return
    
    if system not in solarSystems:
      response.set_status(400)
      response.write(errorMsgs[1])
      return
    
    if corporation not in corporations:
      response.set_status(400)
      response.write(errorMsgs[2])
      return
    
    if securityMask >= 2**11:
      response.set_status(400)
      response.write(errorMsgs[3])
      return
    
    securityMask = [not not (securityMask & (1<<bit)) for bit in range(11)]
    
    # calculate distances
    dist = {system:0}
    qIn = set([system])
    while len(qIn):
      this = qIn.pop()
      for j in solarSystems[this]['jumps']:
        if securityMask[solarSystems[j]['rating']]:
          continue
        if j not in dist or dist[j] > dist[this] + 1:
          dist[j] = dist[this] + 1
          qIn.add(j)
    results = []
    for s in corporations[corporation]['stations']:
      if stations[s]['solarSystem'] not in dist:
        dist[stations[s]['solarSystem']] = -1
      results.append({
        'distance':dist[stations[s]['solarSystem']],
        'solarSystem':{
          'id':stations[s]['solarSystem'],
          'name':solarSystems[stations[s]['solarSystem']]['name']
        },
        'station':{
          'id':s,
          'name':stations[s]['name']
        },
        'region':{
          'id':solarSystems[stations[s]['solarSystem']]['region'],
          'name':regions[solarSystems[stations[s]['solarSystem']]['region']]['name']
        }
      })
    results = sorted(results,key=lambda item:item['station']['name'])
    results = sorted(results,key=lambda item:item['distance'] < 0 and _maxint or item['distance'])
    response.write(json.encode(results))

class ApiErrorHandler(webapp2.RequestHandler):
  def get(self):
    response = self.response
    response.set_status(400)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers.add_header('Access-Control-Allow-Origin', '*')
    response.write(errorMsgs[0].replace('{{}}',self.request.host_url))

class BlacklistHandler(webapp2.RequestHandler):
  def get(self):
    response = self.response
    response.set_status(403)

class BlacklistRoute(webapp2.BaseRoute):
  """Catchall route for blacklisting based non-uri criteria.
  
  'Configuration' is done algorithmically in match()
  
  Based on SimpleRoute.
  """
  
  def __init__(self, handler):
    super(BlacklistRoute, self).__init__('', handler=handler)
  
  def match(self, request):
    """Matches this route against the current request.
    
    .. seealso:: :meth:`BaseRoute.match`.
    """
    
    userAgent = ''
    if 'User-Agent' in request.headers:
      userAgent = request.headers['User-Agent']
    
    results = (self, (), {})
    
    # Referer should never match requested url
    if request.url == request.referer:
      logging.debug('Warning: url matched referer')
      # Ignore this for now. There are some aggressive tracking blocking software that do this to defeat sites that require a same-site referer.
    
    # block XoviBot
    if userAgent.find('XoviBot') >= 0:
      logging.debug('Blocked: XoviBot')
      return results
    
    # Can't block on Accept-Encoding so block on known User-Agent of non-gzip clients
    if userAgent in (
      'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)', # Unknown, never requests gzip
      'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; InfoPath.2)', # TalkTalk Virus Alerts Scanning Engine
      'Wget/1.9+cvs-stable (Red Hat modified)', # TalkTalk Virus Alerts Scanning Engine
      '(TalkTalk Virus Alerts Scanning Engine)' # TalkTalk Virus Alerts Scanning Engine
    ):
      logging.debug('Blocking known non-gzip client')
      return results
    
    # Less common non-gzip clients are blocked in the page during page load.
  
  def __repr__(self):
    return '<BlacklistRoute(%r)>' % (self.handler,)


app = webapp2.WSGIApplication([
  (r'/cron', CronHandler),
  BlacklistRoute(BlacklistHandler),
  (r'/', LoaderHandler),
  (r'/app', AppHandler),
  webapp2.Route(r'/api/<system:\d+>/<corporation:\d+>/<securityMask:\d+>', ApiHandler),
  (r'/api/help', HelpHandler),
  (r'/api/.*', ApiErrorHandler)
], debug=True)
