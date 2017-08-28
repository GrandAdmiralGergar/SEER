$(document).ready(function(){
	$("#login").click(function()
	{
		var username = $("#username").val();
		var password = $("#password").val();
		// Checking for blank fields.
		if( username == '' || password =='')
		{
			$('input[type="text"],input[type="password"]').css("border","2px solid red");
			$('input[type="text"],input[type="password"]').css("box-shadow","0 0 3px red");
			alert("Please fill all fields...!!!!!!");
		}
		else
		{
			$.post("/loginAttempt",{ username1: username, password1:password},function(data)
			{
			if(data=='SUCCESS')
				{
					$("form")[0].reset();
					$('input[type="text"],input[type="password"]').css({"border":"2px solid #00F5FF","box-shadow":"0 0 5px #00F5FF"});
 					$(location).attr('href', 'home');
				}
				else
				{
					alert(data);
				}
			});
		}
	});
});
