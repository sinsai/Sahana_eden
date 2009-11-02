$(document).ready(function() {
    $('.error').hide().slideDown('slow')
    $('.error').click(function() { $(this).fadeOut('slow'); return false; });
    $('.warning').hide().slideDown('slow')
    $('.warning').click(function() { $(this).fadeOut('slow'); return false; });
    $('.information').hide().slideDown('slow')
    $('.information').click(function() { $(this).fadeOut('slow'); return false; });
    $('.confirmation').hide().slideDown('slow')
    $('.confirmation').click(function() { $(this).fadeOut('slow'); return false; });
    $('a.thickbox').click(function(){
        $(this).attr('href', function() {
            // Add the caller to the URL vars so that the popup knows which field to refresh/set
            var url_in = $(this).attr('href');
            var caller = $(this).parents('tr').attr('id').replace(/__row/, '');
            // This has to be the last var: &TB_iframe=true
            var url_out = url_in.replace(/&TB_iframe=true/, '&caller=' + caller + '&TB_iframe=true');
            return url_out;
        });
        return false;
    });
});
