/**
 * @file Files/quiz.js Implementation of @ref quiz
 * @defgroup quiz Functions for quiz.js
 * @addtogroup quiz
 * @{
 */

var PLAYERS_IN_LINE = 3;
var state = "Registration";
timer = window.setTimeout(getnames, 1000);

var pathParts = window.location.pathname.split('/');
pathParts = pathParts.slice(0, -1);
baseuri = pathParts.join('/');
var ws = new WebSocket("ws://" + location.host + baseuri + "/websocket/");

ws.onopen = function() {
  console.log("onopen");

  pkt = {"action":"connectQuiz"};
  ws.send(JSON.stringify(pkt));
};

ws.onmessage = function (evt) {
  console.log("ws.onmessage = " + evt.data);
  var pkt = JSON.parse(evt.data);

  console.log("action = " + pkt.action);

  if(pkt.action == "updatePlayers") {
    updatePlayers(pkt);
  } else if(pkt.action == "opening") {
    $("#quiz_name").html(pkt.info.name);
    $("#number_questions").html(pkt.info.number_of_questions + " questions");
    switchState("Opening", "#f57986");
  } else if(pkt.action == "question") {
    $("#question_title").html(pkt.question.text);
    var questionsID = ["A_answer", "B_answer", "C_answer", "D_answer"];
    for (i = 0; i < 4; i++) {
      let _answer = pkt.question.answers[i];

      if (_answer != null) {
	fontsize = 100;
	alen = _answer.text.length;
	if (alen > 0 && alen < 10) {
	  fontsize = 120;
	} else if (alen > 20 && alen < 40) {
	  fontsize = 80;
	} else if (alen > 40 && alen < 60) {
	  fontsize = 60;
	} else if (alen > 60 && alen < 80) {
	  fontsize = 50;
	}

	$("#"+questionsID[i]).html('<font style="font-size: ' + fontsize + '%">' + _answer.text + '</font>');
	$("#"+questionsID[i]).show();
      } else {
	$("#"+questionsID[i]).html("");
	$("#"+questionsID[i]).hide();
      }
    }
    switchState("Question", "#ccf6fc");
  } else if(pkt.action == "answer") {
    answer_html = "";
    list_answers = pkt.answers;
    if(list_answers.length == 1) {
      $("#anstext").html("The right answer is:");
    } else {
      $("#anstext").html("The right answers are:");
    }
    for (var i = 0; i < list_answers.length; i++) {
      answer_html += "<span>"+$("#"+list_answers[i] + "_answer").html() + "</span>";
    }
    $("#ans").html(answer_html);
    switchState("Answer", "#3df548");
  } else if(pkt.action == "leaderboard") {
    leaderboard = document.getElementById("Leaderboard");
    //TODO: Move as much as I can into the HTML page
    var list_players = pkt.leaderboard.players
    var lb = '<table id="Leaderboard_table">';
    for (i = 0; i < list_players.length; i++) {
      player = list_players[i];
      lb += "<tr>" +
	"   <td>" +
	player.name +
	"   </td>" +
	"   <td>" +
	player.score +
	"   </td>" +
	"</tr>";
    }
    lb += "</table>";
    $("#Leaderboard_content").html(lb);
    switchState("Leaderboard", "Orange");
  } else if(pkt.action == "finish") {
    var oTable = document.getElementById("Leaderboard_table");

    var oCells = oTable.rows.item(0).cells;

    $("#Finish_name").html(oCells.item(0).innerHTML);
    $("#Finish_score").html(oCells.item(1).innerHTML);
    switchState("Finish", "#96A5A9");
  }

};

function switchState(newstate, color) {
  console.log("switchState " + state + " to " + newstate);
  $("#"+state).css("display", "none");
  state = newstate;
  $("#"+state).css("display", "inline");
  document.body.style.background = color;
}

/**
 * Get the join number and print it to the screen
 */
function get_join_number() {
  $.ajax({url:"get_join_number",
	  dataType: 'json',
         })
    .done(function(pkt) {
	    $("#join_number").html(pkt.join_number);
	  })
    .fail(function() {
	    window.location.href = '';
	  })
}

/**
 * Get the names of all the players and print it to the screen
 */
function getnames() {
  $.ajax({url:"getnames",
	  dataType: 'json',
         })
    .done(function(pkt) {
	    updatePlayers(pkt);
	  })
    .fail(function() {
	    window.location.href = '';
	  })
}

function updatePlayers(pkt) {
  string_players = "";
  players = pkt.players;
  for (i = 0; i < players.length; i++) {
    string_players += players[i];
    if (i % PLAYERS_IN_LINE === 0 && i !== 0) {
      string_players += "<br/>";
    } else if ((i + 1) < players.length) {
      string_players += "&emsp;";
    }
  }
  $("#names").html(string_players);
  if(players.length > 0) {
    $("#br1").html("Connected players:");
    $("#br1").css("display", "inline");
    $("#names").css("display", "inline");
  } else {
    $("#br1").html("No connected players");
    $("#br1").css("display", "none");
    $("#names").css("display", "none");
  }
}

/**
 *continue only if at least one user is online
 */
function check_moveable() {
  if (document.getElementById("names").innerHTML.length > 0) {
    change_Registeration_Opening();
  }
}

/**
 * Switch from Registration screen to Opening screen
 */
function change_Registeration_Opening() {
  pkt = {"action":"startGame"};
  ws.send(JSON.stringify(pkt));
}

/** @} */
