/* 
    Logistics Static JS Code

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-01-27
*/ 
$(document).ready(function() {
	function ItemIDChange() {                
        var selSubField = $('[name = "item_packet_id"]');
        
        $('[id$="item_packet_id__row1"]').show();
        $('[id$="item_packet_id__row"]').show();        
        
        /* Show Throbber */
        selSubField.after('<div id="item_packet_ajax_throbber" class="ajax_throbber style="display:inline;"/>')
                   .hide();
        
        var url;
        
        if ($('[name = "item_id"]').length != 0) {
            url = S3.Ap.concat('/supply/item_packet.json?item_packet.item_id=', $('[name = "item_id"]').val());
        } else {
            url = S3.Ap.concat('/inventory/store_item_packets/', $('[name $= "item_id"]').val());
        }
        
        var data;
                                
        $.getJSON(url, function(data) {
            /* Create Select Element */
            var options = '';
            var v = '';
            
            if (data.length == 0) {
                options += '<option value="">' + S3.i18n.no_packets + '</options>';
            } else {
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + ' (' + data[i].quantity + ')</option>';
                }                
            }
            
            /* 1 = default value */
            selSubField.html(options)  
                       .val(1)        
                       .show(); 
            
            /* Show "Add" Button & modify link */  
            href = $('#item_packet_add').attr('href') + "&item_id=" + $('[name = "item_id"]').val();
            $('#item_packet_add').attr('href', href)
            $('#item_packet_add').show();
            
            /* Hide Throbber */
            $('#item_packet_ajax_throbber').hide();
            
            if ( typeof ItemPacketIDChange == "function" ) {
                ItemPacketIDChange();
            }; 
        });   
    }
    var ItemID = $('[name $= "item_id"]').val();       
    
    if (ItemID == '' | ItemID == undefined) {
        /* Hide the item packet input if the item hasn't been entered */
        $('[id$="item_packet_id__row1"]').hide();
        $('[id$="item_packet_id__row"]').hide();    
    } else {
        /* Show the item packet input id the item has already been entered (if this is an error or update) */      
        ItemIDChange();
    }
   
    /* Includes Inventory Item too */
    $('[name $= "item_id"]').change(ItemIDChange);
    
	$('.quantity.ajax_more').live( 'click', function (e) {		
		e.preventDefault();
		var DIV = $(this)
        var ShipmentType;
		if (DIV.hasClass('collapsed')) {
			if (DIV.hasClass('fulfil')) {
				ShipmentType = 'recv';
			} else if (DIV.hasClass('transit')) {
				ShipmentType = 'send';
			} else if (DIV.hasClass('commit')) {
				ShipmentType = 'commit';
			}	
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass('collapsed')
			   .addClass('expanded');
			
			//Get the req_item_id
			var UpdateURL = $('.action-btn', DIV.parent().parent().parent()).attr('href');
			var re = /req_item\/(.*)/i;
			var req_item_id = re.exec(UpdateURL)[1];
			var url = S3.Ap.concat('/logs/', ShipmentType, '_item_json/', req_item_id);						
			$.ajax( { 
				url: url,
				dataType: 'json',
				context: DIV,
				success: function(data) {
					RecvTable = '<table class="recv_table">'	
					for (i=0; i<data.length; i++) {
						RecvTable += '<tr><td>';
						if (i==0) {
							//Header Row
							RecvTable += data[0].id
							
						} else {
							RecvURL = S3.Ap.concat('/logs/', ShipmentType, '/',  data[i].id);
							RecvTable += "<a href = '" + RecvURL + "'>"; 
							RecvTable += data[i].datetime.substring(0, 10) + '</a>';
						}
						RecvTable += '</td><td>' + data[i].quantity + '</td></tr>';
					}
					RecvTable += '</table>';
					$('.quantity_req_ajax_throbber', this.parent()).remove();
					this.parent().after(RecvTable);
				}
			});
		} else {			
			DIV.removeClass('expanded')
			   .addClass('collapsed');
			$('.recv_table', DIV.parent().parent() ).remove()
		}
			
	});
});