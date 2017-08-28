function join_group(uid, gid)
{
    $.post("/joinGroup", { userId: uid, groupId: gid },function(data)
    {
        if(data == 'SUCCESS')
        {
            link = 'group?groupId=' + gid;
            $(location).attr('href', link);
        }
        else
        {
            alert('Could not join group for some reason')
        }
    });
}

function leave_group(uid, gid)
{
    $.post("/leaveGroup", { userId: uid, groupId: gid },function(data)
    {
        if(data == 'SUCCESS')
        {
            link = 'group?groupId=' + gid;
            $(location).attr('href', link);
        }
        else
        {
            alert('Could not leave group for some reason')
        }
    });
}
