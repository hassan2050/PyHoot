/**
 * @file Files/game.js Implementation of @ref game
 * @defgroup game Functions for game.js
 * @addtogroup game
 * @{
 */


// The current state of the game
var state = "wait";

var ws = new WebSocket("ws://" + location.host + "/pyhoot/websocket/");

ws.onopen = function() {
  console.log("onopen");
  ws.send('{"action":"connectPlayer"}');
};

ws.onerror = function (evt) {
  console.log("onerror: " + evt);
  windows.location.href = "/pyhoot/";
}

ws.onmessage = function (evt) {
  console.log("ws.onmessage = " + evt.data);
  var pkt = JSON.parse(evt.data);

  console.log("action = " + pkt.action);

  if (pkt.action == "move_to_next_page") {
    move_to_next_page();
  } else if (pkt.action == "invalid_pid") {
    window.location.href = "/pyhoot/";
    return;
  } else if (pkt.action == "wait") {
    
    switchState("wait", "#dafccc");
  } else if(pkt.action == "wait_question") {
    switchState("wait_question", "#cccefc");
  } else if(pkt.action == "starting") {
    $("#quiz_name").html(pkt.info.name);
    $("#number_questions").html(pkt.info.number_of_questions + " questions");
    switchState("starting", "#cfcefc");
  } else if(pkt.action == "opening_countdown") {
    if(pkt.countdown > 1) {
      $("#opening_countdown").html("Starting in " + pkt.countdown + " seconds.");
    } else if(pkt.countdown == 0) {
      $("#opening_countdown").html("Starting Now!");
    } else {
      $("#opening_countdown").html("Starting in " + pkt.countdown + " second.");
    }
  } else if(pkt.action == "question") {
    $("#question_title").html(pkt.question.text);

    var questionsID = ["A_answer", "B_answer", "C_answer", "D_answer"];
    for (i = 0; i < 4; i++) {
      let _answer = pkt.question.answers[i];

      if (_answer != null) {
	$("#"+questionsID[i]).html(_answer.text);
	$("#"+questionsID[i]).show();
      } else {
	$("#"+questionsID[i]).html("");
	$("#"+questionsID[i]).hide();
      }
    }
    $("#question_countdown").html(pkt.countdown);

    switchState("question", "#ccf6fc");
  } else if(pkt.action == "question_countdown") {
    $("#question_countdown").html(pkt.countdown);
  } else if(pkt.action == "answer_countdown") {
    $("#answer_countdown").html(pkt.countdown);
  } else if(pkt.action == "leaderboard_countdown") {
    $("#leaderboard_countdown").html(pkt.countdown);
  } else if(pkt.action == "showAnswer") {
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

    $("#score").html(pkt.score);
    $("#diff_score").html(pkt.diff_score);

    if (pkt.correct) {
      $("#correct").html("Correct");
    } else {
      $("#correct").html("Incorrect");
    }
    
    switchState("showAnswer", "#cccefc");
  } else if(pkt.action == "leaderboard") {
    $("#leaderboard_score").html(pkt.score);
    $("#leaderboard_place").html(ordinal_suffix_of(pkt.place));
    switchState("leaderboard", "#ffccd7");
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
 * Disconnecting user from the system
 * @return nothing
 */
function disconnect_user() {
  //pkt = {"action":"disconnect"}
  //ws.send(JSON.stringify(pkt));

  window.location.href = "/pyhoot/";
}


/**
 * Send the answer the user clicked on
 * @param letter (string) the letter of the answer
 *
 */
function send_answer(letter) {
  pkt = {"action":"sumbitAnswer", "answer":letter}
  ws.send(JSON.stringify(pkt))
  switchState("wait_question", "#cccefc");
}


/**
 * Add suffix to the number
 * @param i the number we want to add the suffix to
 * @returns the number with the suffix
 */
function ordinal_suffix_of(i) {
	var j = i % 10,
		k = i % 100;
	if (j == 1 && k != 11) {
		return i + "st";
	}
	if (j == 2 && k != 12) {
		return i + "nd";
	}
	if (j == 3 && k != 13) {
		return i + "rd";
	}
	return i + "th";
}


/** @} */
