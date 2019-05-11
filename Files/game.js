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

ws.onmessage = function (evt) {
  console.log("ws.onmessage = " + evt.data);
  var pkt = JSON.parse(evt.data);

  console.log("action = " + pkt.action);

  if (pkt.action == "move_to_next_page") {
    move_to_next_page();
  }

  if (pkt.action == "wait") {
    switchState("wait", "#dafccc");
  } else if(pkt.action == "question") {
    $("#title").html(pkt.question.text);

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

    switchState("question", "#ccf6fc");
  } else if(pkt.action == "wait_question") {
    switchState("wait_question", "#cccefc");
  } else if(pkt.action == "leaderboard") {
    $("#score").html(pkt.score);
    $("#place").html(ordinal_suffix_of(pkt.place));
    switchState("leaderboard", "#ffccd7");
  }
};

function switchState(newstate, color) {
  console.log("switchState " + state + " to " + newstate);
    document.getElementById(state).style.display = "";
    state = newstate;
    document.getElementById(state).style.display = "inline";
    document.body.style.background = color;
}

//Checking every second if need to moved
//check_move_to_next();

/**
 * Disconnecting user from the system
 * @return nothing
 */
function disconnect_user() {
	xmlrequest("diconnect_user", function() {
		if (this.readyState == 4) {
			window.location.href = '/pyhoot/';
		}
	});
}

/**
 * switch screens for the next screen
 * @return nothing
 */
function switch_screens() {
	console.log(state);
	switch (state) {
		case "question":
			to = "wait";
			color = "#dafccc";
			break;
		case "leaderboard":
			to = "question";
			color = "#ccf6fc";
			break;
		case "wait":
			to = "question";
			color = "#cccefc"
			break;
		case "wait_question":
			state = "wait";
			to = "leaderboard";
			color = "#ffccd7";
			break;
	}
	var from_style_display = document.getElementById(state).style.display;
	var to_style_display = document.getElementById(to).style.display;
	from_style_display = [to_style_display, to_style_display = from_style_display][0];
	document.getElementById(state).style.display = from_style_display;
	document.getElementById(to).style.display = to_style_display;
	document.body.style.background = color
}

/**
 * Send the answer the user clicked on
 * @param letter (string) the letter of the answer
 *
 */
function send_answer(letter) {
	xmlrequest("answer?letter=" + letter,
		function() {
			if (this.readyState == 4 && this.status == 200) {
			  switchState("wait_question", "#cccefc");
			}
		}
	);
}

/**
 * Get the score and place of the player from the server and print it to the screens
 * @return nothing
 */
function get_score() {
	xmlrequest("get_score",
		function() {
		     if (this.readyState == 4 && this.status == 200) {
		       var score_place = parse_xml_from_string(this.responseText).getElementsByTagName("score_place")[0];
		       document.getElementById("score").innerHTML = score_place.getAttribute("score");
		       document.getElementById("place").innerHTML = ordinal_suffix_of(score_place.getAttribute("place"));
		     }
		   }
	);
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

/**
 * Get the title of the question and print it in the right place
 *
 */
function get_title() {
	xmlrequest("get_title",
		function() {
		     if (this.readyState == 4 && this.status == 200) {
		       document.getElementById("title").innerHTML =
			 parse_xml_from_string(this.responseText).getElementsByTagName("title")[0].textContent
			}
		}
	)
}

/**
 * check if there is a need to move to the next part
 * @return nothing
 */

function move_to_next_page() {
 switch (state) {
  case "wait":
    get_title();
    switch_screens();
    state = "question";
    xmlrequest("moved_to_next_question", null);
    break;
  case "question":
    switch_screens();
    state = "leaderboard";
    xmlrequest("moved_to_next_question", null);
    break;
  case "wait_question":
    get_score();
    switch_screens();
    state = "leaderboard";
    xmlrequest("moved_to_next_question", null);
    break;
  case "leaderboard":
    get_title()
    switch_screens();
    xmlrequest("moved_to_next_question", null);
    state = "question";
    break;
  }
}

/** @} */
