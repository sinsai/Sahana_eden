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
    $('a.colorbox').click(function(){
        // Function to Add a Resource from within a form
        $(this).attr('href', function() {
            // Add the caller to the URL vars so that the popup knows which field to refresh/set
            var url_in = $(this).attr('href');
            var caller = $(this).parents('tr').attr('id').replace(/__row/, '');
            var url_out = url_in;
            if (url_out.indexOf("&caller=") == -1){
                url_out = url_out + '&caller=' + caller;
            }
            return url_out;
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
                var header_width = $(this).width();
                var popup_width = $('ul', this).width();

                //console.log("header is", header_width, "popup_width", popup_width);
                if (popup_width != null){
                  if (popup_width < header_width){
                    $('ul', this).css({
                        'width': header_width.toString() + 'px'
                    });
                  }
                }
                /*$('ul', this).css({
                    'width': popup_width.toString() + 'px'
                });*/

                $('ul', this).css('display','block');
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
/*
  ajaxS3 ------------------------------------------------------------
  added by sunneach 2010-feb-14
*/

/*
  these set in the ajaxS3messages.js :
_ajaxS3_wht_ = {{=T('We have tried')}};
_ajaxS3_gvn_ = {{=T('times and it is still not working. We give in. Sorry.')}};
_ajaxS3_500_ = {{=T('Sorry - the server has a problem, please try again later.')}};
_ajaxS3_dwn_ = {{=T('There was a problem, sorry, please try again later.')}};
_ajaxS3_get_ = {{=T('getting')}};
_ajaxS3_fmd_ = {{=T('form data')}};
_ajaxS3_rtr_ = {{=T('retry')}};
*/
(function($) {
    jQuery.ajaxS3 = function(s) {
        var options = jQuery.extend( {}, jQuery.ajaxS3Settings, s );
        options.tryCount = 0;
        showStatus(_ajaxS3_get_ + ' ' + (s.message ? s.message : _ajaxS3_fmd_) + '...', this.ajaxS3Settings.msgTimeout);
        options.success = function(data, status) {
            hideStatus();
            if (s.success)
                s.success(data, status);
        }
        options.error = function(xhr, textStatus, errorThrown ) {
            if (textStatus == 'timeout') {
                this.tryCount++;
                if (this.tryCount <= this.retryLimit) {
                    // try again
                    showStatus(_ajaxS3_get_ + ' ' + (s.message ? s.message : _ajaxS3_fmd_) + '... ' + _ajaxS3_rtr_ + ' ' + this.tryCount,
                        $.ajaxS3Settings.msgTimeout);
                    $.ajax(this);
                    return;
                }
                showStatus(_ajaxS3_wht_ + ' ' + (this.retryLimit + 1) + ' ' + _ajaxS3_gvn_,
                    $.ajaxS3Settings.msgTimeout, false, true);
                return;
            }
            if (xhr.status == 500) {
                showStatus(_ajaxS3_500_, $.ajaxS3Settings.msgTimeout, false, true);
            } else {
                showStatus(_ajaxS3_dwn_, $.ajaxS3Settings.msgTimeout, false, true);
            }
        };
        jQuery.ajax(options);
    };

    jQuery.postS3 = function(url, data, callback, type) {
        return jQuery.ajaxS3({
            type: "POST",
            url: url,
            data: data,
            success: callback,
            dataType: type
        });
    };

    jQuery.getS3 = function(url, data, callback, type, message) {
        // shift arguments if data argument was omitted
        if ( jQuery.isFunction( data ) ) {
            callback = data;
            data = null;
        }
        return jQuery.ajaxS3({
            type: 'GET',
            url: url,
            data: data,
            success: callback,
            dataType: type,
            message: message
        });
    };

    jQuery.getJSONS3 = function(url, data, callback, message) {
        // shift arguments if data argument was omitted
        if ( jQuery.isFunction( data ) ) {
            message = callback;
            callback = data;
            data = null;
        }
        return jQuery.getS3(url, data, callback, 'json', message);
    };

    jQuery.ajaxS3Settings = {
        timeout : 10000,
        msgTimeout: 2000,
        retryLimit : 10,
        dataType: 'json',
        type: 'GET'
    };

    jQuery.ajaxS3Setup = function(settings) {
        jQuery.extend(jQuery.ajaxS3Settings, settings);
    };

})(jQuery);

// status bar for ajaxS3 operation
// taken from http://www.west-wind.com/WebLog/posts/388213.aspx
// added and fixed by sunneach on Feb 16, 2010
//
//  to use make a call:
//  showStatus(message, timeout, additive, isError)
//     1. message  - string - message to display
//     2. timeout  - integer - milliseconds to change the statusbar style - flash effect (1000 works OK)
//     3. additive - boolean - default false - to accumulate messages in the bar
//     4. isError  - boolean - default false - show in the statusbarerror class
//
//  to remove bar, use
//  hideStatus()
//
function StatusBar(sel,options)
{
    var _I = this;
    var _sb = null;
    // options
    this.elementId = "_showstatus";
    this.prependMultiline = true;
    this.showCloseButton = false;
    this.afterTimeoutText = null;

    this.cssClass = "statusbar";
    this.highlightClass = "statusbarhighlight";
    this.errorClass = "statusbarerror";
    this.closeButtonClass = "statusbarclose";
    this.additive = false;
    $.extend(this, options);
    if (sel)
      _sb = $(sel);
    // create statusbar object manually
    if (!_sb)
    {
        _sb = $("<div id='_statusbar' class='" + _I.cssClass + "'>" +
                "<div class='" + _I.closeButtonClass +  "'>" +
                (_I.showCloseButton ? " X </div></div>" : "") )
                .appendTo(document.body)
                .show();
    }
    //if (_I.showCloseButton)
        $("." + _I.cssClass).click(function(e) { $(_sb).hide(); });
    this.show = function(message, timeout, additive, isError)
    {
        if (additive || ((additive == undefined) && _I.additive))
        {
            var html = "<div style='margin-bottom: 2px;' >" + message + "</div>";
            if (_I.prependMultiline)
                _sb.prepend(html);
            else
                _sb.append(html);
        }
        else
        {
            if (!_I.showCloseButton)
                _sb.text(message);
            else
            {
                var t = _sb.find("div.statusbarclose");
                _sb.text(message).prepend(t);
            }
        }
        _sb.show();
        if (timeout)
        {
            if (isError)
                _sb.addClass(_I.errorClass);
            else
                _sb.addClass(_I.highlightClass);
            setTimeout(
                function() {
                    _sb.removeClass(_I.highlightClass);
                    if (_I.afterTimeoutText)
                       _I.show(_I.afterTimeoutText);
                },
                timeout);
        }
    }
    this.release = function()
    {
        if (_statusbar) {
            $('#_statusbar').remove();
            _statusbar = undefined;
        }
    }
}
// use this as a global instance to customize constructor
// or do nothing and get a default status bar
var _statusbar = null;
function showStatus(message, timeout, additive, isError)
{
    if (!_statusbar)
        _statusbar = new StatusBar();
    _statusbar.show(message, timeout, additive, isError);
}
function hideStatus()
{
    if (_statusbar)
        _statusbar.release();
}
