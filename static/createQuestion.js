$(document).ready(function() {
    $('#btnDel' ).attr('disabled', 'disabled').button('disable');
    
    $('#btnAdd').click( function() {
        $('#btnDel').removeAttr('disabled').button('enable');   // enable the "del" button
        // how many "duplicatable" input fields we currently have
        var num = $('.clonedInput').length; 
        
        // the numeric ID of the new input field being added    
        var newNum  = new Number(num + 1);      
        var newElem = $('#input' + num ).clone().attr('id', 'input' + newNum);
                                 
        newElem.children(':first').attr( 'id', 'option' + newNum ).attr('option', 'option_label[]');
        $('#input' + num).after(newElem);
        
        
        // Limit to 10
        if (newNum == 10) {
             $('#btnAdd' ).attr('disabled', 'disabled').button('disable');
             $('#btnAdd').parent().find('.ui-btn-text').text('maximum fields reached');
        }                        
    });

    $( '#btnDel' ).click( function() {
        // how many "duplicatable" input fields we currently have           
        var num = $( '.clonedInput' ).length;   
        
        // remove the last element  
        $('#input' + num ).remove();
        
        // enable the "add" button, since we've removed one             
        $('#btnAdd').removeAttr('disabled').button('enable');   
        $('#btnAdd').parent().find('.ui-btn-text').text('Add a new option');
        
        // if only one element remains, disable the "remove" button
        if ( num-1 == 1 )
        $('#btnDel' ).attr('disabled', 'disabled').button('disable');

    });  
   
    $( '#submit' ).click( function() {
        var option_list= new Array();
        $('input[name^="option_label"]').each(function() 
        {
            option_list.push($(this).val());
        });
        
        var group_list = [];
        $('#checkboxes input:checked').each(function()
        {
            group_list.push(parseInt(($(this).attr('id')).substr(14)));
        });
        if(group_list.length == 0)
        {
            alert("Specify at least one target group to have access to this market");
            return;
        }
        var jsonOut = JSON.stringify(option_list);
        var groupJsonOut = JSON.stringify(group_list);
//         $.post("/createQuestionDB",{ question: $("#title").val(), options: JSON.stringify(option_list)},function(data)
        $.post("/createQuestionDB",{ question: $("#title").val(), options: jsonOut, groupIds: groupJsonOut},function(data)
        {
            if(data != "FAILURE")
            {
                var id = parseInt(data)
                $(location).attr('href', 'question?questionId=' + id);
            }
            else
            {
                alert("Question has already been asked!");
            }
        });
    });
    
    $( '#cancel' ).click( function() {
        $(location).attr('href', 'home');
    });
});        