$(document).ready(function(){
	$("#register").click(function()
	{
		var username = $("#un").val();
		var password = $("#pw").val();
		var email = $("#email").val();

		// Checking for blank fields.
		if( username =='' || password =='' || email == '')
		{
			$('input[type="text"],input[type="password"]').css("border","2px solid red");
			$('input[type="text"],input[type="password"]').css("box-shadow","0 0 3px red");
			alert("Please fill all fields...!!!!!!");
		}
		else
		{
			$.post("/createUser", { username1: username, password1:password, email1:email},function(data)
            {
                if(data == 'True')
                {
                    $(location).attr('href', '/home');
                }
                else
                {
                    alert('Username already taken')
                }
            });
		}
	});
});
