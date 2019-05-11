#! /usr/bin/env python3

"""python program to solve the world problems..."""

from gevent import monkey; monkey.patch_all()

import os, sys, string, time, logging, argparse
import bottle
from bottle import get, run, route, static_file, post, Bottle, abort, request, response
import json
import glob

from xml.etree import ElementTree


if 1:
  from bottle.ext.websocket import GeventWebSocketServer
  from bottle.ext.websocket import websocket

import services
import common
import util

import config

_version = "0.1"

SERVICES_LIST = {service.NAME: service for service in
                 (services.Service.__subclasses__() +
                  services.XMLService.__subclasses__()
                  )}

class BottleApp(bottle.Bottle):
  def __init__(self):
    #bottle.Bottle.__init__(self)
    super().__init__(self)
    self.common = common.Common()
    self._base_directory = "."

app = BottleApp()

@app.route(config.uriprefix + '/')
def index():
  bottle.redirect(config.uriprefix + '/home.html')

@app.route(config.uriprefix + '/new')
def new():
  bottle.redirect(config.uriprefix + '/new.html')

@app.route(config.uriprefix + '/check_test_exist')
def check_test_exist():
  quiz_name = request.query.get('quiz_name')
  
  ret = os.path.isfile(
    os.path.normpath("%s/Quizes/%s.xml" % (app._base_directory, os.path.normpath(quiz_name))))
  root = {}
  root['ret'] = ret
  return json.dumps(root)
  

@app.route(config.uriprefix + '/getquizes')
def getquizes():
  root =  {"quizes":[]}
  quizes = glob.glob(os.path.join(app._base_directory, "Quizes", "*.json"))
  for fn in quizes:
    path, f = os.path.split(fn)
    name, ext = os.path.splitext(f)
    root['quizes'].append(name)
  logging.warn("quizes %s" % root)
  return json.dumps(root)


@app.route(config.uriprefix + '/get_join_number')
def get_join_number():
  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: return

  return json.dumps({"join_number": app.common.pid_client[pid].join_number})

@app.route(config.uriprefix + '/getnames')
def getnames():
  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: return
  _game = app.common.pid_client[pid]

  players = []
  pkt = {"players":players}

  for player in _game.get_player_dict().values():
    if player.name is not None:
      players.append(player.name)
  return json.dumps(pkt)


@app.get(config.uriprefix + '/websocket/', apply=[websocket])
def handle_websocket(ws):
  if not ws:
    abort(400, 'Expected WebSocket request.')

  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: return
  _game = app.common.pid_client[pid]
  _game.websocket = ws

  while True:
    message = ws.receive()
    if message is None: break
    
    #logging.info("message %s" % message)

    msg = json.loads(message)

    logging.info("message: %s" % msg)
    if msg['action'] == "startGame":
      gameRuntime = GameMasterThread(_game)
      gameRuntime.start()
    if msg['action'] == "connectPlayer":
      gameRuntime = GamePlayerThread(_game)
      gameRuntime.start()

class GameMasterThread(object):
  def __init__(self, game):
    self.daemon = True
    self.game = game

  def start(self):
    self.run()

  def run(self):
    info = self.game.get_information()
    logging.debug("info: %s" % info)
    self.game.state = "opening"
    self.game.send({"action" : "opening", "info":info})
    for player in self.game.get_player_dict().values():
      player.send({"action" : "wait"})
    time.sleep(5)

    while 1:
      question = self.game.get_question()
      self.game.start_question()
      logging.debug("question state")
      self.game.state = "question"
      self.game.send({"action" : "question", "question":question})

      for player in self.game.get_player_dict().values():
        player.send({"action" : "question", "question": question})

      endtime = time.time() + self.game.get_question()['duration']
      while 1:
        if self.game.check_all_players_answered(): break
        if time.time() >= endtime: break
        #logging.debug("timeleft: %d" % int(endtime - time.time()))
        time.sleep(0.5)
        
      answers = self.game.get_correct_answers()
      logging.debug("answer state: %s" % answers)
      self.game.state = "answer"
      self.game.send({"action" : "answer", "answers":answers})
      for player in self.game.get_player_dict().values():
        player.send({"action" : "wait_question"})
      time.sleep(5)

      leaderboard = self.game.get_leaderboard()
      logging.debug("leaderboard state")
      self.game.state = "leaderboard"
      self.game.send({"action" : "leaderboard", "leaderboard":leaderboard})
      for player in self.game.get_player_dict().values():
        score = player.get_score()
        place = player.get_place()
        player.send({"action" : "leaderboard", "score":score, "place":place})
      time.sleep(5)
      self.game.move_to_next_question()

      logging.debug("questions left: %s" % self.game.get_left_questions())
      if self.game.get_left_questions() == 0:
        break

    logging.debug("finish state")
    self.game.state = "finish"
    self.game.send({"action" : "finish"})
    for player in self.game.get_player_dict().values():
      score = player.get_score()
      place = player.get_place()
      player.send({"action" : "leaderboard", "score":score, "place":place})
    time.sleep(1)

    for player in self.game.get_player_dict().values():
      player.state = "done"
      
class GamePlayerThread(object):
  def __init__(self, game):
    self.daemon = True
    self.game = game

  def start(self):
    self.run()

  def run(self):
    self.game.send({"action" : "wait"})

    while self.game.game_master.state != "finish":
      if self.game.state == "done": break
      time.sleep(1)
    

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

  if 1:
    run(host=host, port=port, app=app, server=GeventWebSocketServer, debug=False, quiet=True)

  if 0:
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
