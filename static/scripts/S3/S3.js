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
    $("input.date").datepicker({ changeMonth: true, changeYear: true, dateFormat: 'yy-mm-dd', isRTL: false });
    $('a.thickbox').click(function(){
        $(this).attr('href', function() {
            // Add the caller to the URL vars so that the popup knows which field to refresh/set
            var url_in = $(this).attr('href');
            var caller = $(this).parents('tr').attr('id').replace(/__row/, '');
            // This has to be the last var: &TB_iframe=true
	    /* Why we accumulating caller= over and over? */
            if(url_in.match(/caller=/)){
	        return url_in.replace(/caller=.*&/, 'caller=' + caller + '&');
		//return url_in.split('caller=')[0] + 'caller=' + caller + url_in.match(/&TB_.*$/i);
	    } 
	    else{
		return url_in.replace(/&TB_iframe=true/, '&caller=' + caller + '&TB_iframe=true');
	    }
        });
        return false;
    });
    // IE6 non anchor hover hack
    $('.hoverable').hover(
        function() { $(this).addClass('hovered'); },
        function() { $(this).removeClass('hovered'); }
    );
    // Menu popups (works in IE6)
    $('#modulenav li').hover(
        function() {
                var popup_width = $(this).width()-2;
                $('ul', this).css({
                    'display': 'block',
                    'width': popup_width.toString() + 'px'
                });
            },
        function() { $('ul', this).css('display', 'none');  }
    );
    $('#subnav li').hover(
        function() {
                var popup_width = $(this).width()-2;
                $('ul', this).css({
                    'display': 'block',
                    'width': popup_width.toString() + 'px'
                });
            },
        function() { $('ul', this).css('display', 'none');  }
    );
});
