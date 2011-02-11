// Custom Javascript functions added as part of the S3 Framework

// Global variable to store all of our variables inside
var S3 = Object();
S3.gis = Object();

var popupWin = null;

function openPopup(url) {
    if ( !popupWin || popupWin.closed ) {
        popupWin = window.open(url, 'popupWin', 'width=640, height=480');
    } else popupWin.focus();
}
$(document).ready(function() {   
    // T2 Layer
    try { 
    	$('.zoom').fancyZoom( { 
    		scaleImg:true, 
    		closeOnClick:true, 
    		directory: S3Ap.concat("/static/media")
    	}); 
    } catch(e) {};
    
    $('input.date').datepicker({
        changeMonth: true, changeYear: true,
        //showOtherMonths: true, selectOtherMonths: true,
        showOn: 'both', 
        buttonImage: S3Ap.concat('/static/img/jquery-ui/calendar.gif'), 
        buttonImageOnly: true,
        dateFormat: 'yy-mm-dd', 
        isRTL: S3.rtl 
     });    
    
    $('.error').hide().slideDown('slow')
    $('.error').click(function() { $(this).fadeOut('slow'); return false; });
    $('.warning').hide().slideDown('slow')
    $('.warning').click(function() { $(this).fadeOut('slow'); return false; });
    $('.information').hide().slideDown('slow')
    $('.information').click(function() { $(this).fadeOut('slow'); return false; });
    $('.confirmation').hide().slideDown('slow')
    $('.confirmation').click(function() { $(this).fadeOut('slow'); return false; });
    
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
                if (popup_width != null){
                  if (popup_width < header_width){
                    $('ul', this).css({
                        'width': header_width.toString() + 'px'
                    });
                  }
                }
                $('ul', this).css('display', 'block');
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
    
    // Colorbox Popups
    $('a.colorbox').attr('href', function(index, attr) {
        // Add the caller to the URL vars so that the popup knows which field to refresh/set
        var caller = '';
        try {
            caller = $(this).parents('tr').attr('id').replace(/__row/, '');
        } catch(e) {
            // Do nothing
            if(caller == '') return attr;
        }
        // Avoid Duplicate callers
        var url_out = attr;
        if (attr.indexOf('&caller=') == -1){
            url_out = attr + '&caller=' + caller;
        }
        return url_out;
    });    
    $('.colorbox').click(function(){
        $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:this.href, title:this.title});
        return false;
    });
    
    $('.tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    var tipCloseText = '<img src="' + S3Ap.concat('/static/img/cross2.png') + '" alt="close" />';
    $('.stickytip').cluetip( { 
    	activation: 'hover', 
    	sticky: true, 
    	closePosition: 'title', 
    	closeText: tipCloseText, 
    	splitTitle: '|'
    } );
    $('.ajaxtip').cluetip( { 
    	activation: 'click', 
    	sticky: true, 
    	closePosition: 'title', 
    	closeText: tipCloseText, 
    	width: 380
    } );
    now = new Date();
    $('form').append("<input type='hidden' value=" + now.getTimezoneOffset() + " name='_utc_offset'/>");    
});

function s3_tb_remove(){
    // Colorbox Popup
    $.fn.colorbox.close();
}

/*
  ajaxS3 ------------------------------------------------------------
  added by sunneach 2010-feb-14
  modified by flavour
  Strings get set in a localised in views/l10n.js :
*/


(function($) {
    jQuery.ajaxS3 = function(s) {
        var options = jQuery.extend( {}, jQuery.ajaxS3Settings, s );
        options.tryCount = 0;
        if (s.message) {
            s3_showStatus(_ajaxS3_get_ + ' ' + (s.message ? s.message : _ajaxS3_fmd_) + '...', this.ajaxS3Settings.msgTimeout);
        }
        options.success = function(data, status) {
            s3_hideStatus();
            if (s.success)
                s.success(data, status);
        }
        options.error = function(xhr, textStatus, errorThrown ) {
            if (textStatus == 'timeout') {
                this.tryCount++;
                if (this.tryCount <= this.retryLimit) {
                    // try again
                    s3_showStatus(_ajaxS3_get_ + ' ' + (s.message ? s.message : _ajaxS3_fmd_) + '... ' + _ajaxS3_rtr_ + ' ' + this.tryCount,
                        $.ajaxS3Settings.msgTimeout);
                    $.ajax(this);
                    return;
                }
                s3_showStatus(_ajaxS3_wht_ + ' ' + (this.retryLimit + 1) + ' ' + _ajaxS3_gvn_,
                    $.ajaxS3Settings.msgTimeout, false, true);
                return;
            }
            if (xhr.status == 500) {
                s3_showStatus(_ajaxS3_500_, $.ajaxS3Settings.msgTimeout, false, true);
            } else {
                s3_showStatus(_ajaxS3_dwn_, $.ajaxS3Settings.msgTimeout, false, true);
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

    jQuery.getS3 = function(url, data, callback, type, message, sync) {
        // shift arguments if data argument was omitted
        if ( jQuery.isFunction( data ) ) {
            sync = message;
            message = type;
            type = callback;
            callback = data;
            data = null;
        }
        if (sync) {
            var async = false;
        }
        return jQuery.ajaxS3({
            type: 'GET',
            url: url,
            async: async,
            data: data,
            success: callback,
            dataType: type,
            message: message
        });
    };

    jQuery.getJSONS3 = function(url, data, callback, message, sync) {
        // shift arguments if data argument was omitted
        if ( jQuery.isFunction( data ) ) {
            sync = message;
            message = callback;
            callback = data;
            data = null;
        }
        if (!sync) {
            var sync = false;
        }
        return jQuery.getS3(url, data, callback, 'json', message, sync);
    };

    jQuery.ajaxS3Settings = {
        timeout : 10000,
        msgTimeout: 2000,
        retryLimit : 10,
        dataType: 'json',
        async: true,
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
//  s3_showStatus(message, timeout, additive, isError)
//     1. message  - string - message to display
//     2. timeout  - integer - milliseconds to change the statusbar style - flash effect (1000 works OK)
//     3. additive - boolean - default false - to accumulate messages in the bar
//     4. isError  - boolean - default false - show in the statusbarerror class
//
//  to remove bar, use
//  s3_hideStatus()
//
function S3StatusBar(sel, options) {
    var _I = this;
    var _sb = null;
    // options
    // ToDo allow options passed-in to over-ride defaults
    this.elementId = '_showstatus';
    this.prependMultiline = true;
    this.showCloseButton = false;
    this.afterTimeoutText = null;

    this.cssClass = 'statusbar';
    this.highlightClass = 'statusbarhighlight';
    this.errorClass = 'statusbarerror';
    this.closeButtonClass = 'statusbarclose';
    this.additive = false;
    $.extend(this, options);
    if (sel) {
      _sb = $(sel);
    }
    // Create statusbar object manually
    if (!_sb) {
        _sb = $("<div id='_statusbar' class='" + _I.cssClass + "'>" +
                "<div class='" + _I.closeButtonClass +  "'>" +
                (_I.showCloseButton ? ' X </div></div>' : '') )
                .appendTo(document.body)
                .show();
    }
    //if (_I.showCloseButton)
        $('.' + _I.cssClass).click(function(e) { $(_sb).hide(); });
    this.show = function(message, timeout, additive, isError) {
        if (additive || ((additive == undefined) && _I.additive)) {
            var html = "<div style='margin-bottom: 2px;' >" + message + '</div>';
            if (_I.prependMultiline) {
                _sb.prepend(html);
            } else {
                _sb.append(html);
            }
        }
        else {
            if (!_I.showCloseButton) {
                _sb.text(message);
            } else {
                var t = _sb.find('div.statusbarclose');
                _sb.text(message).prepend(t);
            }
        }
        _sb.show();
        if (timeout) {
            if (isError) {
                _sb.addClass(_I.errorClass);
            } else {
                _sb.addClass(_I.highlightClass);
            }
            setTimeout(
                function() {
                    _sb.removeClass(_I.highlightClass);
                    if (_I.afterTimeoutText) {
                       _I.show(_I.afterTimeoutText);
                    }
                },
                timeout);
        }
    }
    this.release = function() {
        if (_statusbar) {
            $('#_statusbar').remove();
            _statusbar = undefined;
        }
    }
}
// Use this as a global instance to customize constructor
// or do nothing and get a default status bar
var _statusbar = null;
function s3_showStatus(message, timeout, additive, isError) {
    if (!_statusbar) {
        _statusbar = new S3StatusBar();
    }
    _statusbar.show(message, timeout, additive, isError);
}
function s3_hideStatus() {
    if (_statusbar) {
        _statusbar.release();
    }
}

//==============================================================================
//Code to warn on exit without saving 
//@author: Michael Howden (michael@sahanafoundation.org)
function S3SetNavigateAwayConfirm() {
	window.onbeforeunload = function() {
          return _s3_msg_unsaved_changes;
		};	
};

function S3ClearNavigateAwayConfirm() {
	window.onbeforeunload = function() {};
};

function S3EnableNavigateAwayConfirm() {
  $(document).ready(function() {
      if ( $('[class=error]').length > 0 ) {
          // If there are errors, ensure the unsaved form is still protected
	        S3SetNavigateAwayConfirm(); 
	    } 
      $(':input:not(input[id=gis_location_advanced_checkbox])').keypress( S3SetNavigateAwayConfirm );		
      $(':input:not(input[id=gis_location_advanced_checkbox])').change( S3SetNavigateAwayConfirm );	
      $('form').submit( S3ClearNavigateAwayConfirm );
  });
};
//==============================================================================
//@author: Michael Howden (michael@sahanafoundation.org)
function S3ConfirmClick(ElementID, Message) {
	//@param ElementID: the ID of the element which will be clicked 
	//@param Message: the Message displayed in the confirm dialog	
	$(ElementID).click( function(event) {
	    if(confirm(Message)) {
	        return true; 
	    } else {
	        event.preventDefault();
	        return false;
	    }
	});
};
//==============================================================================
function s3_viewMap(feature_id) {
    var url = S3Ap.concat('/gis/display_feature/') + feature_id;
    var oldhtml = $('#map').html();
    var iframe = "<iframe width='640' height='480' src='" + url + "'></iframe>";
    var closelink = $('<a href=\"#\">' + _close_map + '</a>');

    closelink.bind( "click", function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom: 10px' />").append(closelink));
}
function s3_viewMapMulti(module, resource, instance, jresource) {
    var url = S3Ap.concat('/gis/display_feature//?module=') + module + '&resource=' + resource + '&instance=' + instance + '&jresource=' + jresource;
    var oldhtml = $('#map').html();
    var iframe = '<iframe width="640" height="480" src="' + url + '"></iframe>';
    var closelink = $('<a href=\"#\">' + _close_map + '</a>');

    closelink.bind( 'click', function(evt) {
        $('#map').html(oldhtml);
        evt.preventDefault();
    });

    $('#map').html(iframe);
    $('#map').append($("<div style='margin-bottom: 10px' />").append(closelink));
}