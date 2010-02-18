var popupWin = null;
function openPopup(url) {
	if ( !popupWin || popupWin.closed ) {
		popupWin = window.open( url, "popupWin", "width=640,height=480" );
	} else popupWin.focus();
}
function set_org_id(id){
    var href = $('#add_office')[0].href;
    if(id == ''){
        $('#add_office').attr('href', href.replace(/organisation_id=(.*?)&/,''));
    } 
    else if(!$('#add_office')[0].href.match(/organisation_id/)){
        $('#add_office').attr('href', href.replace('?','?organisation_id=' + id + '&'));
    }
    else{
        $('#add_office').attr('href', href.replace(/organisation_id=(.*?)&/,'organisation_id=' + id + '&'));
    }
};
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
	    if($(this).attr('id') == 'add_office' && $(this).parents('tr').attr('id') == 'or_contact_office_id__row') {
	        set_org_id($("#or_contact_organisation_id").val());
		//reset_org_office();
	    }
            // Add the caller to the URL vars so that the popup knows which field to refresh/set
            var url_in = $(this).attr('href');
            var caller = $(this).parents('tr').attr('id').replace(/__row/, '');
            // This has to be the last var: &TB_iframe=true
	    /* Why we accumulating caller= over and over? */
            if(url_in.match(/caller=/)){
	        return url_in.replace(/caller=.*?&/, 'caller=' + caller + '&');
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
/* 
  ajaxS3 ------------------------------------------------------------
  added by sunneach 2010-feb-14
*/
(function($) {
    jQuery.ajaxS3 = function(s) {
        var options = jQuery.extend({}, jQuery.ajaxS3Settings, s);
	options.tryCount = 0;
	showStatus('getting ' + (s.message ? s.message : 'form data') + '...', this.ajaxS3Settings.msgTimeout);
	options.success = function(data, status) {
	    hideStatus();
	    if(s.success)
		s.success(data, status);
	}
	options.error = function(xhr, textStatus, errorThrown ) {
	    if (textStatus == 'timeout') {
		this.tryCount++;
		if (this.tryCount <= this.retryLimit) {
		    //try again
    		    showStatus('getting ' + (s.message ? s.message : 'form data') + '... retry ' + this.tryCount, $.ajaxS3Settings.msgTimeout);
		    $.ajax(this);
		    return;
		}
		showStatus('We have tried ' + (this.retryLimit + 1) +
		           ' times and it is still not working. We give in. Sorry.',
			   $.ajaxS3Settings.msgTimeout, false, true);
		return;
	    }
	    if (xhr.status == 500) {
		showStatus('Sorry - the server has a problem, please try again later.', $.ajaxS3Settings.msgTimeout, false, true);
	    } else {
		showStatus('There was a problem, sorry, please try again later.', $.ajaxS3Settings.msgTimeout, false, true);
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
	// shift arguments if data argument was ommited
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
	    message: message,
        });
    };

    jQuery.getJSONS3 = function(url, data, callback, message) {
        return jQuery.getS3(url, data, callback, 'json', message);
    };

    jQuery.ajaxS3Settings = {
	timeout : 5000,
	msgTimeout: 1000,
	retryLimit : 3,
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
        if(_statusbar)
            $('#_statusbar').remove();
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
    if(_statusbar)
	_statusbar.release();
}
