/**
 * @file Files/home.js Implementation of @ref home
 * @defgroup home Functions for home.js
 * @addtogroup home
 * @{
 */

/**
 * Change the parts of the page
 */
function changeDiv() {
  $('#p1').css("display", "none");
  $('#p2').css("display", "inline");
  $('#name').focus();
}

/**
 * Make sure the name is valid
 */
function check_length_name() {
  if ($("#name").val().length >= 3) {
    checkName();
  } else {
    $("#p2_title").html("Name too short, at least 3 characters");
  }
}

/**
 * Check if name / test exist
 */
function checkTest() { //Check if name / test exist
  var join_number = $("#join_number").val();
  
  $.ajax({url:"/pyhoot/check_test?join_number=" + join_number,
	  dataType: 'json'})
    .done(function(pkt) {
	    if (pkt.ret) {
	      changeDiv();
	    } else {
	      $("#p1_title").html("No such Game Pin, enter right one");
	    }
	  })
    .fail(function() {
	    
	  });
}

function checkName() {
  
  $.ajax({url:"/pyhoot/check_name?join_number=" + $("#join_number").val() + "&name=" + $("#name").val(),
	     dataType: 'json'})
    .done(function(pkt) {
	    console.log("name:"+pkt.ret);
	    if (pkt.ret) {
	      $("#join").submit();
	    } else {
	      $("#p2_title").html("Name taken, choose another name.");
	    }
	  })
    .fail(function() {
	    
	  });
}


/**
 * Check if name / test exist
 */
function check(type) { //Check if name / test exist
  var data = $("#join_number").val();
  if (type == "name") {
    data += "&name=" + $("#name").val();
  }
  
  $.ajax({url:"check_" + type + "?join_number=" + data})
    .done(function(pkt) {
	  })
    .fail(function() {

	  })

	xmlrequest("check_" + type + 
		function() {
			if (this.readyState == 4 && this.status == 200) {
				var ans = xmlstring_to_boolean(this.responseText);
				if (type == "test") {
					if (ans) {
						changeDiv();
					} else {
						document.getElementById("p1_title").innerHTML =
							"No such Game Pin, enter right one";
					}
				} else if (type == "name") {
					if (ans) {
						document.getElementById("join").submit();
					} else {
						document.getElementById("p2_title").innerHTML =
							"Name taken, choose another name";
					}
				}
			}
		}
	);
}

/** @} */
