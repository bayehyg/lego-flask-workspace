$('.star-icon').click(function() {
    var star = $(this).data('bool');
    var setNum = $(this).data('setnum');

    
    
    var send;
    if (star === 'True') {
        send = false;
        $(this).data('bool', 'False');
        $(this).attr('src', './static/unstar.png');
    } else {
        send = true;
        $(this).data('bool', 'True');
        $(this).attr('src', './static/starred.png');
    }
    console.log('Star', send);

    $.ajax({    
        url: '/star',
        type: 'GET',
        data: { star: send, set_num: setNum },
        success: function(response) {
            
            console.log('Star updated successfully:', response);
        },
        error: function(xhr, status, error) {
            console.error('Error updating star:', error);
        }
    });
});