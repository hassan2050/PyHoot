#! /usr/bin/env python3

"""python program to solve the world problems..."""

import os, sys, string, time, logging, argparse
import bottle
from bottle import get, run, route, static_file, post, Bottle, abort, request, response

from gevent import monkey; monkey.patch_all()

if 0:
  from bottle.ext.websocket import GeventWebSocketServer
  from bottle.ext.websocket import websocket

import services
import common

import config

_version = "0.1"

SERVICES_LIST = {service.NAME: service for service in
                 (services.Service.__subclasses__() +
                  services.XMLService.__subclasses__()
                  )}

class BottleApp(bottle.Bottle):
  def __init__(self):
    super().__init__(self)
    self.common = common.Common()
    self._base_directory = "."

app = BottleApp()

@app.route(config.uriprefix + '/')
def index():
  bottle.redirect(config.uriprefix + '/home.html')

@app.route(config.uriprefix + '/<filepath:path>')
def server_static(filepath):
  self = app

  uri_path = "/" + filepath

  if uri_path not in SERVICES_LIST.keys():
    return bottle.static_file(filepath, root="Files")

  service_function = SERVICES_LIST[uri_path]
  dic_argument = request.query

  dic_argument.update({"common": self.common,
                       "base_directory": self._base_directory})

  _game = None

  if "pid" in request.cookies:
    pid = request.cookies.get("pid")
    if pid in self.common.pid_client:
      _game = self.common.pid_client[pid]

  dic_argument.update({"game": _game})
  if _game is not None:
      dic_argument.update({"pid": _game.pid})
      if (_game.TYPE == "PLAYER" and
              _game.game_master is not None):
          dic_argument.update(
              {"server_pid": _game.game_master.pid})

  # Remove un-usable keys
  dic_argument.pop('self', None)

  if 0:
    print("join_number", list(self.common.join_number.items()))
    print("pid_clients", list(self.common.pid_client.items()))
    print("dic_argument", list(dic_argument.items()))

  self._file = service_function(
      *(dic_argument[arg] for arg in
        service_function.__init__.__code__.co_varnames if
        arg in dic_argument)
  )

  if self._file.NAME == "FILE":
    body = self._file.content()
    print (repr(body))
    return body

  _extra_headers = {}
  headers = self._file.headers(_extra_headers)
  if 0:
    print ('headers', headers)

  if "Set-Cookie" in headers:
    cname, cvalue = headers.get('Set-Cookie')
    bottle.response.set_cookie(cname, cvalue)

  if "Status-Code" in headers and headers['Status-Code'] == 302:
    bottle.redirect(headers.get("Location"))
    return
  
  body = self._file.content()
  #print (repr(body))
  return body

def start():
  host,port = (config.hostname, config.port)
  logging.warn("access @ http://%s:%s%s/" % (host,port,config.uriprefix))

  #run(host=host, port=port, app=app, server=GeventWebSocketServer, debug=False, quiet=True)
  run(host=host, port=port, app=app, debug=False, quiet=False)

def test():
  logging.warn("Testing")

def parse_args(argv):
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__)

  parser.add_argument("-t", "--test", dest="test_flag", 
                    default=False,
                    action="store_true",
                    help="Run test function")
  parser.add_argument("--log-level", type=str,
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Desired console log level")
  parser.add_argument("-d", "--debug", dest="log_level", action="store_const",
                      const="DEBUG",
                      help="Activate debugging")
  parser.add_argument("-q", "--quiet", dest="log_level", action="store_const",
                      const="CRITICAL",
                      help="Quite mode")
  #parser.add_argument("files", type=str, nargs='+')

  args = parser.parse_args(argv[1:])

  return parser, args

def main(argv, stdout, environ):
  if sys.version_info < (3, 0): reload(sys); sys.setdefaultencoding('utf8')

  parser, args = parse_args(argv)

  logging.basicConfig(format="[%(asctime)s] %(levelname)-8s %(message)s", 
                    datefmt="%m/%d %H:%M:%S", level=args.log_level)

  if args.test_flag:  test();   return

  start()

if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)
