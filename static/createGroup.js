$(document).ready(function() {
    $( '#submit' ).click( function() {
        gName = $("#groupName").val()
        gDesc = $("#groupDescription").val()
        
        $.post("/createGroupDB",{ groupName: gName, groupDescription: gDesc},function(data)
        {
            if(data != "FAILURE")
            {
                var id = parseInt(data)
                $(location).attr('href', 'group?groupId=' + id);
            }
            else
            {
                alert("Group already exists, or group name is too short!");
            }
        });
    });
    
    $( '#cancel' ).click( function() {
        $(location).attr('href', 'home');
    });
});        