/**
 * @file Files/new.js Implementation of @ref new
 * @defgroup new Functions for new.js
 * @addtogroup new
 * @{
 */

/**
 * Check if test exist on the system
 */
function check_test_exist() {
	xmlrequest(
		"check_test_exist?quiz_name=" + document.getElementById("quiz_name").value,
		function() {
		  if (this.readyState == 4 && this.status == 200) {
		    root = JSON.parse(this.responseText);
		    console.log("root " + root);
		    if (root['ret']) {
		      $("#register_quiz").submit();
		    } else {
		      $("#title_register").html("No such quiz!<br />Name of quiz:");
		    }
		  }
		}
	);
}

QUIZES_IN_LINE = 4;

/**
 * Get the names of all the players and print it to the screen
 */
function getquizes() {
	xmlrequest("getquizes", function() {
		if (this.readyState == 4) {
			if (this.status == 200) {
				root = JSON.parse(this.responseText);

				string_quizes = "";
				for (var i = 0; i < root.quizes.length; i++) {
					string_quizes += '<button class=quiz onclick="location.href=\'/pyhoot/register_quiz?quiz_name=' + root.quizes[i] + '\';">' + root.quizes[i] + '</button>';
					if ((i+1) % QUIZES_IN_LINE == 0 && i != 0) {
						string_quizes += "<br/>";
					} else if ((i + 1) < root.quizes.length) {
						string_quizes += "&emsp;";
					}
				}
				$("#quizes").html(string_quizes);
			}
		}
	});
}


/** @} */
