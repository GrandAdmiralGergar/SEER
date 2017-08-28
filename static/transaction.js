function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function buy_click(id, number)
{
    oid = parseInt(id.substr(3));
    paramName = getParameterByName('questionId');
    $.post("/buy", { questionId: paramName, optionId: oid, count: number},function(data)
    {
        if(data == 'SUCCESS')
        {
            link = 'question?questionId=' + paramName;
            $(location).attr('href', link);
        }
        else
        {
            alert('Cannot afford to purchase this share')
        }
    });
}

function sell_click(id, number)
{
    oid = parseInt(id.substr(4));
    paramName = getParameterByName('questionId');
    $.post("/sell", { questionId: paramName, optionId: oid, count: -number},function(data)
    {
        if(data == 'SUCCESS')
        {
            link = 'question?questionId=' + paramName;
            $(location).attr('href', link);
        }
        else
        {
            alert('No shares to sell')
        }
    });
}
