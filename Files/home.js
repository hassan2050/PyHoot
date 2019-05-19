/**
 * @file Files/home.js Implementation of @ref home
 * @defgroup home Functions for home.js
 * @addtogroup home
 * @{
 */

function onLoad() {
  $.ajax({url:"get_active_game",
	     dataType: 'json'})
    .done(function(pkt) {
	    if (pkt.ret) {
	      $("#returnButton").html("Return to " + pkt.name + " Game");
	      $("#returnToGame").css("display", "inline");
	    } 
	  })
    .fail(function() {
	  });
}

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
  
  $.ajax({url:"check_test?join_number=" + join_number,
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
  
  $.ajax({url:"check_name?join_number=" + $("#join_number").val() + "&name=" + $("#name").val(),
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

/** @} */
