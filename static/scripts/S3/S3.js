var popupWin = null;
function openPopup(url) {
	if ( !popupWin || popupWin.closed ) {
		popupWin = window.open( url, "popupWin", "width=640,height=480" );
	} else popupWin.focus();
}

$(document).ready(function() {
    $('.error').hide().slideDown('slow')
    $('.error').click(function() { $(this).fadeOut('slow'); return false; });
    $('.warning').hide().slideDown('slow')
    $('.warning').click(function() { $(this).fadeOut('slow'); return false; });
    $('.information').hide().slideDown('slow')
    $('.information').click(function() { $(this).fadeOut('slow'); return false; });
    $('.confirmation').hide().slideDown('slow')
    $('.confirmation').click(function() { $(this).fadeOut('slow'); return false; });
    $('a.popup').click(function(){
        var url=$(this).attr('href');
        var caller=$(this).parents('tr').attr('id').replace(/__row/,'');
//        openPopup(url.replace(/format=plain/,'format=popup')+'&caller='+caller);
        return false;
    });
});
