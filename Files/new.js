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
				if (xmlstring_to_boolean(this.responseText)) {
					document.getElementById("register_quiz").submit();
				} else {
					document.getElementById("title_register").innerHTML =
						"No such quiz!<br />Name of quiz:";
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
				xmlDoc = parse_xml_from_string(this.responseText);
				quizes = xmlDoc.getElementsByTagName("quiz");
				string_quizes = "";
				for (var i = 0; i < quizes.length; i++) {
					string_quizes += "<span class=quiz>" + quizes[i].getAttribute("name") + "</span>";
					if ((i+1) % QUIZES_IN_LINE == 0 && i != 0) {
						string_quizes += "<br/>";
					} else if ((i + 1) < quizes.length) {
						string_quizes += "&emsp;";
					}
				}
				document.getElementById("quizes").innerHTML = string_quizes;
			}
		}
	});
}


/** @} */
