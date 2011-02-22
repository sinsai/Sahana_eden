/* 
    Logistics Static JS Code

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2011-01-27
*/ 
$(document).ready(function() {
	$('.quantity.ajax_more').live( 'click', function (e) {		
		e.preventDefault();
		DIV = $(this)
		if (DIV.hasClass("collapsed")) {
			if (DIV.hasClass("fulfil")) {
				ShipmentType = "recv"
			} else if (DIV.hasClass("transit")) {
				ShipmentType = "send"
			} else if (DIV.hasClass("commit")) {
				ShipmentType = "commit"
			}	
			DIV.after('<div class="ajax_throbber quantity_req_ajax_throbber"/>')
			   .removeClass("collapsed")
			   .addClass("expanded");
			
			//Get the req_item_id
			UpdateURL = $(".action-btn",DIV.parent().parent().parent()).attr("href");
			re = /req_item\/(.*)/i;
			req_item_id = re.exec(UpdateURL)[1];
			url = "/eden/logs/" + ShipmentType + "_item_json/" + req_item_id;						
			$.ajax( { 
				url: url,
				dataType: 'json',
				context: DIV,
				success: function(data) {
					RecvTable = '<table class="recv_table">'	
					for(i=0; i<data.length; i++) {
						RecvTable += "<tr><td>";
						if (i==0) {
							//Header Row
							RecvTable += data[0].id
							
						} else {
							RecvURL = "/eden/logs/" + ShipmentType + "/" +  data[i].id;
							RecvTable += "<a href = '" + RecvURL + "'>"; 
							RecvTable += data[i].datetime.substring(0,10) + "</a>"; 						
						}
						RecvTable += "</td><td>" + data[i].quantity + "</td></tr>";
					}
					RecvTable += "</table>";	
					$('.quantity_req_ajax_throbber',this.parent()).remove();
					this.parent().after(RecvTable);
				}
			});
		} else {			
			DIV.removeClass("expanded")
			   .addClass("collapsed");			
			$('.recv_table', DIV.parent().parent() ).remove()
		}
			
	});
});