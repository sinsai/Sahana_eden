/* 
    Supply Static JS Code

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-01-27
*/ 
//============================================================================

$(document).ready(function() {
	//=========================================================================
	// Displays the number of items available in a inventory
    function InvItemPackIDChange() {     
        $('#TotalQuantity').remove();           
        $('[name = "quantity"]').after('<div id="inv_quantity_ajax_throbber" class="ajax_throbber" style="float:right"/>'); 
             
        url = '/eden/inv/inv_item_quantity/' 
        url += $('[name = "inv_item_id"]').val();
        $.getJSON(url, function(data) {
            /* @todo: Error Checking */
            var InvQuantity = data.inv_inv_item.quantity; 
            var InvPackQuantity = data.supply_item_pack.quantity; 
            
            var PackName = $('[name = "item_pack_id"] option:selected').text();
            var re = /\(([0-9]*)/;
            var PackQuantity = re.exec(PackName)[1];
            
            var Quantity = (InvQuantity * InvPackQuantity) / PackQuantity;
                            
            TotalQuantity = '<span id = "TotalQuantity"> / ' + Quantity.toFixed(2) + ' ' + PackName + ' in inv.</span>';
            $('#inv_quantity_ajax_throbber').remove();
            $('[name = "quantity"]').after(TotalQuantity);
        });
    };
    $('#inv_send_item_item_pack_id').change(InvItemPackIDChange);
    
	function ItemIDChange() { 
		var selField = $('[name $= "item_id"]');
        var selSubField = $('[name = "item_pack_id"]');
        
        $('[id$="item_pack_id__row1"]').show();
        $('[id$="item_pack_id__row"]').show();        
        
        /* Show Throbber */
        selSubField.after('<div id="item_pack_ajax_throbber" class="ajax_throbber style="display:inline;"/>')
                   .hide();
        
        var url;
        
        if (selField.length != 0) {
            url = S3.Ap.concat('/supply/item_pack.json?item_pack.item_id=', selField.val());
        } else {
            url = S3.Ap.concat('/inv/inv_item_packs/', selField.val());
        }
        
        var data;
                        
		$.ajax( { 
			url: url,
			dataType: 'json',
			context: selField,
			success: function(data) {        
            /* Create Select Element */
	            var options = '';
	            var UM = '';
	            
	            if (data.length == 0) {
	                options += '<option value="">' + S3.i18n.no_packs + '</options>';
	            } else {
	            	for (var i = 0; i < data.length; i++){
	            		if (data[i].quantity == 1) {
	            			UM = data[i].name;
	            			break;
	            		}	            		
	            	}
	                for (var i = 0; i < data.length; i++){
	                	options += '<option value="' +  data[i].id + '">'
	                	if (data[i].quantity == 1) {
	                		options += data[i].name 
	                	} else {
	                		options += data[i].name + ' (' + data[i].quantity + ' x ' + UM +')'
	                	}
	                    options += '</option>';
	                }                
	            }
	            
	            /* 1 = default value */
	            selSubField.html(options)  
	                       .val(1)        
	                       .show(); 
	            
	            /* Show "Add" Button & modify link */  
	            href = $('#item_pack_add').attr('href') + "&item_id=" + $('[name = "item_id"]').val();
	            $('#item_pack_add').attr('href', href)
	         						 .show();
	            
	            /* Hide Throbber */
	            $('#item_pack_ajax_throbber').hide();
	            
	            /* If this is an inventory item */
	            if ( this.attr('name') == 'inv_item_id' ) {
	                InvItemPackIDChange();
	            }
	        } 
        });   
    };
    
    var ItemID = $('[name $= "item_id"]').val();       
        
    if (ItemID == '' | ItemID == undefined) {
        /* Hide the item pack input if the item hasn't been entered */
        $('[id$="item_pack_id__row1"]').hide();
        $('[id$="item_pack_id__row"]').hide();    
    } else {
        /* Show the item pack input id the item has already been entered (if this is an error or update) */      
        ItemIDChange();
    }
   
    /* Includes Inventory Item too */
    $('[name $= "item_id"]').change(ItemIDChange);

    //=========================================================================
    /* Function to show the transactions related to request commit, transit &
     * fulfil quantities
     */
	$('.quantity.ajax_more').live( 'click', function (e) {		
		e.preventDefault();
		var DIV = $(this)
        var ShipmentType;
		var App;
		if (DIV.hasClass('collapsed')) {
			if (DIV.hasClass('fulfil')) {
				App = 'inv';
				ShipmentType = 'recv';
			} else if (DIV.hasClass('transit')) {
				ShipmentType = 'send';
				App = 'inv';
			} else if (DIV.hasClass('commit')) {
				ShipmentType = 'commit';
				App = 'req';
			}	
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass('collapsed')
			   .addClass('expanded');
			
			//Get the req_item_id
			var UpdateURL = $('.action-btn', DIV.parent().parent().parent()).attr('href');
			var re = /req_item\/(.*)\//i;
			var req_item_id = re.exec(UpdateURL)[1];
			var url = S3.Ap.concat('/', App, '/', ShipmentType, '_item_json/', req_item_id);	
			//var url = S3.Ap.concat('/', App, '/', ShipmentType, '_item.s3json?/', 
			//		   ShipmentType, '_item.req_item_id=', req_item_id);	
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
							RecvURL = S3.Ap.concat('/', App, '/', ShipmentType, '/',  data[i].id);
							RecvTable += "<a href = '" + RecvURL + "'>"; 
							if (data[i].datetime != null) {
								RecvTable += data[i].datetime.substring(0, 10) + '</a>';
							} else {
								RecvTable +=  ' - </a>';
							}
							
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