#! /usr/bin/env python3

"""python program to solve the world problems..."""

from gevent import monkey; monkey.patch_all()

import os, sys, string, time, logging, argparse
import bottle
from bottle import get, run, route, static_file, post, Bottle, abort, request, response
import json
import glob

if 1:
  from bottle.ext.websocket import GeventWebSocketServer
  from bottle.ext.websocket import websocket
  import geventwebsocket

import common
import util
import game

import config

_version = "0.1"


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

@app.route(config.uriprefix + '/check_test')
def check_test():
  join_number = int(request.query.get('join_number'))

  ret = (join_number in app.common.join_number and app.common.join_number[join_number].TYPE == "MASTER")
  return json.dumps({'ret':ret})
  
@app.route(config.uriprefix + '/get_active_game')
def get_active_game():
  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: 
    return json.dumps({'ret':False})

  _game = app.common.pid_client[pid]
  if _game.game_master.state != "finish":
    return json.dumps({'ret':True, 'name':_game.quiz_name})
  return json.dumps({'ret':False})
  
@app.route(config.uriprefix + '/check_name')
def check_name():
  join_number = int(request.query.get('join_number'))
  name = request.query.get('name')

  ret = False

  master = app.common.join_number.get(join_number, None)

  if master and master.TYPE == "MASTER":
    name_list = [player.name for player in master.get_player_dict().values()]

    if name not in name_list: ret = True

  return json.dumps({'ret':ret})
  
@app.route(config.uriprefix + '/join')
def join():
  pid = request.cookies.get("pid")
  if pid in app.common.pid_client:
    util.remove_from_sysyem(app.common, pid)
    pid = None

  join_number = int(request.query.get('join_number'))
  name = request.query.get('name')

  if join_number not in app.common.join_number: 
    bottle.redirect(config.uriprefix + '/home.html')
    return
  else:
    g = game.GamePlayer(app.common.join_number[join_number], app.common, name)
    app.common.pid_client[g.pid] = g
    g.game_master.add_player(g.pid, g)
    bottle.response.set_cookie("pid", g.pid)    
    bottle.redirect(config.uriprefix + '/game.html')
      
@app.route(config.uriprefix + '/check_test_exist')
def check_test_exist():
  quiz_name = request.query.get('quiz_name')
  
  ret = os.path.isfile(
    os.path.normpath(os.path.join((app._base_directory, "Quizes", os.path.normpath(quiz_name)+".json"))))
  root = {}
  root['ret'] = ret
  return json.dumps(root)
  

@app.route(config.uriprefix + '/getquizes')
def getquizes():
  root =  {"quizes":[]}
  quizes = glob.glob(os.path.join(app._base_directory, "Quizes", "*.json"))
  quizes.sort()
  for fn in quizes:
    path, f = os.path.split(fn)
    name, ext = os.path.splitext(f)
    root['quizes'].append(name)
  return json.dumps(root)


@app.route(config.uriprefix + '/get_join_number')
def get_join_number():
  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: abort(400, 'Invalid PID')

  game = app.common.pid_client[pid]
  if game.state == "finish":
    abort(400, 'Game Finished')

  return json.dumps({"join_number": game.join_number})

@app.route(config.uriprefix + '/getnames')
def getnames():
  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: abort(400, 'Invalid PID')
  _game = app.common.pid_client[pid]

  players = []
  pkt = {"players":players}

  for player in _game.get_player_dict().values():
    if player.name is not None:
      players.append(player.name)
  return json.dumps(pkt)

@app.route(config.uriprefix + '/register_quiz')
def register_quiz():
  pid = request.cookies.get("pid")
  if pid in app.common.pid_client: 
    util.remove_from_sysyem(app.common, pid)
    pid = None

  quiz_name = request.query.get('quiz_name')

  m = game.GameMaster(quiz_name, app.common, app._base_directory)
  app.common.pid_client[m.pid] = m
  app.common.join_number[m.join_number] = m

  bottle.response.set_cookie("pid", m.pid)

  bottle.redirect(config.uriprefix + '/quiz.html')
  
  

@app.get(config.uriprefix + '/websocket/', apply=[websocket])
def handle_websocket(ws):
  if not ws:
    logging.warn("websocket: Invalid websocket")
    abort(400, 'Expected WebSocket request.')

  pid = request.cookies.get("pid")
  if pid not in app.common.pid_client: 
    logging.warn("websocket: Invalid PID: %s" % pid)
    ws.send(json.dumps({"action":"invalid_pid"}))
    ws.close()
    return

  _game = app.common.pid_client[pid]
  _game.websocket = ws

  while True:
    try:
      message = ws.receive()
    except geventwebsocket.exceptions.WebSocketError:
      break

    if message is None: break
    
    #logging.info("message %s" % message)

    msg = json.loads(message)

    logging.info("message: %s" % msg)
    if msg['action'] == "startGame":
      gameRuntime = GameMasterThread(_game)
      gameRuntime.start()
    elif msg['action'] == "connectPlayer":
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
    logging.debug(self.game.quiz_name + ": info: %s" % info)
    self.game.state = "opening"
    self.game.send({"action" : "opening", "info":info})
    for player in self.game.get_player_dict().values():
      player.send({"action" : "starting", "info":info})

    for t in range(5, 0, -1):
      for player in self.game.get_player_dict().values():
        player.send({"action" : "opening_countdown", "countdown":t})
        time.sleep(1)
    player.send({"action" : "opening_countdown", "countdown":0})
    time.sleep(1)

    while 1:
      question = self.game.get_question()
      if not question: break
      self.game.start_question()
      logging.debug(self.game.quiz_name + ": question state")
      self.game.state = "question"
      self.game.send({"action" : "question", "question":question})

      for player in self.game.get_player_dict().values():
        player.send({"action" : "question", "question": question, "countdown":self.game.get_question()['duration']})

      endtime = time.time() + self.game.get_question()['duration']

      lasttime = None
      while 1:
        if self.game.check_all_players_answered(): break
        if time.time() >= endtime: break
        #logging.debug("timeleft: %d" % int(endtime - time.time()))

        t = int(endtime - time.time())
        if t != lasttime:
          for player in self.game.get_player_dict().values():
            player.send({"action" : "question_countdown", "countdown":t})
          lasttime = t

        time.sleep(.5)
        
      answers = self.game.get_correct_answers()
      logging.debug(self.game.quiz_name + ": answer state: %s" % answers)
      self.game.state = "answer"
      self.game.send({"action" : "answer", "answers":answers})
      for player in self.game.get_player_dict().values():
        sendShowAnswer(player)
        #player.send({"action" : "wait_question"})

      for t in range(5, 0, -1):
        for player in self.game.get_player_dict().values():
          player.send({"action" : "answer_countdown", "countdown":t})
          time.sleep(1)

      if len(self.game.get_player_dict().values()) > 1:
        leaderboard = self.game.get_leaderboard()
        logging.debug(self.game.quiz_name + ": leaderboard state")
        self.game.state = "leaderboard"
        self.game.send({"action" : "leaderboard", "leaderboard":leaderboard})
        for player in self.game.get_player_dict().values():
          place = player.get_place()
          player.send({"action" : "leaderboard", "score":player.score, "place":place})

        for t in range(5, 0, -1):
          for player in self.game.get_player_dict().values():
            player.send({"action" : "leaderboard_countdown", "countdown":t})
            time.sleep(1)

      if len(self.game.get_player_dict().values()) == 0:
        break

      self.game.clearScores()

      self.game.move_to_next_question()

      logging.debug(self.game.quiz_name + ": questions left: %s" % self.game.get_left_questions())
      if self.game.get_left_questions() == 0:
        break

    logging.debug(self.game.quiz_name + ": finish state")
    self.game.state = "finish"
    self.game.send({"action" : "finish"})
    for player in self.game.get_player_dict().values():
      player.send({"action" : "leaderboard", "score":player.score, "place":player.get_place()})
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
    #self.game.send({"action" : "wait"})

    while self.game.game_master.state != "finish":
      try:
        message = self.game.websocket.receive()
      except geventwebsocket.exceptions.WebSocketError:
        break
    
      logging.info("[%s %s]: message %s" % (self.game.quiz_name, self.game.name, message))

      if message is None: break
      if self.game.state == "done": 
        logging.info("[%s %s]: state is done" % (self.game.quiz_name, self.game.name))
        break

      msg = json.loads(message)

      if msg['action'] == "submitAnswer":
        self.game.answer = msg['answer']
        sendShowAnswer(self.game)
        
      elif msg['action'] == "disconnect":
        self.game.state = "done"
        break
    #self.game.state = "done"

def sendShowAnswer(game):        
  right_answers = game.game_master.get_correct_answers()
  correct = False
  if game.answer in right_answers:
    correct = True

  ## calculate new score
  if game.diff_score is None:
    game.diff_score = 0
    if correct:
      game.correct += 1
      game.diff_score = game.game_master.time - game.time
      game.score += game.diff_score
    else:
      game.incorrect += 1

  game.send({"action":"showAnswer", 
             "answers":right_answers,
             "correct":correct,
             "answers_correct": game.correct,
             "answers_incorrect": game.incorrect,
             "diff_score":game.diff_score, 
             "score":game.score})

@app.route(config.uriprefix + '/<filepath:path>')
def server_static(filepath):
  self = app
  uri_path = "/" + filepath
  return bottle.static_file(filepath, root="Files")

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

  open("pyhoot.pid", "w").write(str(os.getpid()))

  start()

if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)
