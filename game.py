## @package PyHoot.game
# Game objects for the game, there is both player and master
## @file game.py Implementation of @ref PyHoot.game


import base64
import os
import random
import time
import logging

import json

import constants

# Registration -> Opening -> Question -> Answer -> Leaderboard -> Question
# (number_of_questions > -1) -> Finish

import geventwebsocket

class Game(object):
    """Base game object, for the pid"""

    def __init__(self, common):
        """initialization"""
        super(Game, self).__init__()
        while True:
            pid = base64.b64encode(os.urandom(constants.LENGTH_COOKIE)).decode('utf-8')
            if pid not in common.pid_client.keys():
                break
        """the pid, mostly the cookie"""
        self._pid = pid

        """The time you need to change when using the timer"""
        self._change_timer = None

        """Do you need to move to the next part"""
        self._move_to_next_page = False

        self.state = None
        self._websocket = None
        self._message_queue = []

    @property
    def websocket(self): return self._websocket

    @websocket.setter
    def websocket(self, websocket): 
      self._time_alive = time.time()
      self._websocket = websocket

      if self._message_queue:
        pkt = self._message_queue[-1]
        self._try_send(pkt)

    @property
    def pid(self):
        """The number of the object in the database"""
        return self._pid

    def get_move_to_next_page(self):
        """Check if need to move to the next part"""
        return self._move_to_next_page

    def order_move_to_next_page(self):
        """Ordering moving to the next part"""
        self._move_to_next_page = True

        self.send({"action" : "move_to_next_page"})

    def moved_to_next_page(self):
        """Confirm that the user moved to the next part"""
        self._move_to_next_page = False

    def set_time_change(self, new_time):
        """Set time to change, for the timer"""
        self._change_timer = time.time() + new_time

    def check_timer_change(self):
        """Check if need to change, for the timer"""
        try:
            return self._change_timer - time.time() < 0
        except TypeError:
            return False

    def send(self, pkt):
      self._message_queue.append(pkt)

      if not self.websocket:
        dt = time.time() - self._time_alive
        if dt > 60:
          self.state = "finish"
        else:
          logging.warn("%s: closed socket" % self.name)

      self._try_send(pkt)
      
    def _try_send(self, pkt):
      if self.websocket:
        try:
          self.websocket.send(json.dumps(pkt))
          self._time_alive = time.time()
        except geventwebsocket.exceptions.WebSocketError:
          logging.warn("websocket closed for %s" % (self.name))
          self.websocket = None

    @property
    def time(self):
        """property time, when the player answered or when the question started"""
        return self._time

    @time.setter
    def time(self, new_time):
        """Setter for property answer"""
        self._time = new_time

class GameMaster(Game):
    """Game object for Mastser, controller of the sytstem"""

    ## The type of the object, MASTER
    TYPE = "MASTER"

    def __init__(self, quiz_name, common, base_directory):
        """initialization"""
        super(GameMaster, self).__init__(common)

        """name of the quiz"""
        self._quiz_name = quiz_name

        """list of the players"""
        self._players_list = {}  # {pid: GamePlayer}

        self.quiz = json.load(open(os.path.join("Quizes", quiz_name + ".json"), "r"))

        ## shuffle the questions
        random.shuffle(self.quiz['questions'])
        
        self.questionNum = 0

        while True:
            join_number = random.randint(constants.MIN_PID, constants.MAX_PID)
            if join_number not in common.join_number.keys():
                break

        """Join number, the players enter it in 'Enter pid' to join"""
        self._join_number = join_number

        """The time the question started"""
        self._time = None

    @property
    def game_master(self): return self

    @property
    def quiz_name(self): return self._quiz_name

    @property
    def join_number(self):
        """The number of the object in the database"""
        return self._join_number

    def add_player(self, new_pid, game_player):
        """Adding new player for the master"""
        self._players_list[new_pid] = game_player
        
        if self.websocket:
          cmd = {"action" : "updatePlayers"}
          cmd["players"] = [player.name for player in self._players_list.values()]
          self.websocket.send(json.dumps(cmd))

    def remove_player(self, pid):
        """Removing player from the system"""
        if pid in self._players_list:
          del self._players_list[pid]

    def get_player_dict(self):
        """Return dictionary of all the players"""
        return self._players_list.copy()

    def get_score(self, pid):
        """Returning the score of specific player"""
        return self._players_list[pid].score

    def get_current_question_title(self):
        """Return the title of the current question"""
        return self.quiz['questions'][self.questionNum]['text']

    def clearScores(self):
        """Updating the score of all the players"""
        
        for pid, player in self._players_list.items():
          player.clearAnswer()

    def get_leaderboard(self):
        """Return the leaderboard"""
        dic_name_score = {}
        for pid, player in self._players_list.items():
          dic_name_score[player.name] = player.score

        dic_score_names = {}
        for name in dic_name_score:
            score = dic_name_score[name]
            if score in dic_score_names:
                dic_score_names[score].append(name)
            else:
                dic_score_names[score] = [name]

        players = []
        root = {"players":players}
        score_sorted = sorted(dic_score_names, reverse=True)
        for i in range(min(5, len(dic_score_names))):
            score = score_sorted[i]
            for player in dic_score_names[score]:
              players.append({"name":player, "score":score})
        return root

    def get_place(self, pid):
        """Return the place of the player"""
        scores_by_place = []
        for p, player in self._players_list.items():
            scores_by_place.append(player.score)
        # Remove doubles and sort
        return sorted(list(set(scores_by_place)), reverse=True).index(
            self._players_list[pid].score) + 1

    def get_question(self):
        """Return the question and it's answers"""
        try:
          return self.quiz['questions'][self.questionNum]
        except IndexError:
          return None

    def get_information(self):
        """Return the information about the question: It's name and how many
         questions"""
        q = self.quiz.copy()
        q['number_of_questions'] = len(self.quiz['questions'])
        del q['questions']
        return q

    def move_to_next_question(self):
        """Moving to the next question.
        """
        self.questionNum += 1

    def get_left_questions(self):
        """Return how many questions left - 1"""
        return len(self.quiz['questions'])-self.questionNum

    def start_question(self):
        """Start the question"""
        self._time = self.get_question()['duration'] * 100 + int(
            time.time() * 100)

    def check_all_players_answered(self):
        """Check if all the players answered"""
        ans = True
        for player in self._players_list.values():
          if player._answer not in ["A", "B", "C", "D"]:
            ans = False
            break
        return ans

    def get_answers(self):
        """Return the right answers as A,B,C,D"""
        return self.quiz['questions'][self.questionNum]['answers']

    def get_correct_answers(self):
        right_answer = []
        answers = self.quiz['questions'][self.questionNum]['answers']
        for ans in answers:
          if "correct" in ans and ans["correct"] in ("1", True, 1):
            right_answer.append(["A", "B", "C", "D"][answers.index(ans)])
        return right_answer

    def _get_picture(self):
        """Get the name of the picture file in the question
        @return Picture name (string) if available, else return None"""
        question = ElementTree.fromstring(
            self.get_question).find("./Text").text
        if "img" not in question:
            return None
        question = question[question.index("<img"):]
        question = question[0:question.index("/>") + len("/>")]
        question = question[question.index("src=") + len("src=") + 1:]
        question = question[:question.index('"')]
        return question



class GamePlayer(Game):
    """Game object for player"""

    ## The type of the object, player
    TYPE = "PLAYER"

    def __init__(self, master, common, name=None):
        """Initialization"""
        super(GamePlayer, self).__init__(common)
        self._name = name
        self._game_master = master  # Game object GameMaster
        self._answer = None
        self._time = None
        self._score = 0
        self._diff_score = None
        self._correct = 0
        self._incorrect = 0
        
    @property
    def quiz_name(self): return self.game_master.quiz_name

    def get_place(self):
        """Return the place of the player"""
        return self._game_master.get_place(self._pid)

    def get_title(self):
        """Return the title of the question"""
        return self._game_master.get_current_question_title()

    @property
    def correct(self): return self._correct

    @correct.setter
    def correct(self, correct): self._correct = correct

    @property
    def incorrect(self): return self._incorrect

    @incorrect.setter
    def incorrect(self, incorrect): self._incorrect = incorrect


    @property
    def score(self): return self._score

    @score.setter
    def score(self, score): self._score = score

    @property
    def diff_score(self): return self._diff_score

    @diff_score.setter
    def diff_score(self, diff_score): self._diff_score = diff_score

    @property
    def name(self): return self._name

    @name.setter
    def name(self, name): self._name = name

    @property
    def game_master(self): return self._game_master

    @game_master.setter
    def game_master(self, new): self._game_master = new

    @property
    def answer(self): return self._answer

    @answer.setter
    def answer(self, answer):
        """Settter for property answer"""
        if answer in ["A", "B", "C", "D"] or answer is None:
            self._answer = answer
            self._time = int(time.time() * 100)
            #logging.warn("answer %s: %s" % (answer, self._time))
        else:
            raise Exception("Answer not allowd")

    def clearAnswer(self):
      self._diff_score = None
      self._answer = None
      self._time = int(time.time() * 100)
      
    def send(self, pkt):
      if pkt['action'].find("countdown") == -1:
        self._message_queue.append(pkt)

      if not self.websocket:
        dt = time.time() - self._time_alive
        if dt > 60*3:
          logging.warn("%s: removing player" % self.name)
          self.game_master.remove_player(self.pid)
          self.state = "done"
        else:
          if int(dt) % 10 == 0:
            logging.warn("%s: closed socket: %s" % (self.name, int(dt)))

      self._try_send(pkt)

