<script type="text/javascript">//<![CDATA[
$(function() {
    // Default to One-time costs
    // Hide the Running Cost inputs
    $("#budget_item_monthly_cost__row").hide();
    $("#budget_item_minute_cost__row").hide();
    $("#budget_item_megabyte_cost__row").hide();
            
    // When the Cost type changes:
	$("select[name='cost_type']").change(function() {
		// What is the new cost type?
        cost_type=$(this).val();
        if (cost_type=="Recurring") {
            // Hide the Category
            $("#budget_item_category__row").hide();
            // Hide the Unit Cost input
            $("#budget_item_unit_cost__row").hide();
            // Show the Running Cost inputs
            $("#budget_item_monthly_cost__row").show();
            $("#budget_item_minute_cost__row").show();
            $("#budget_item_megabyte_cost__row").show();
        } else if (cost_type=="One-time") {
            // Hide the Running Cost inputs
            $("#budget_item_monthly_cost__row").hide();
            $("#budget_item_minute_cost__row").hide();
            $("#budget_item_megabyte_cost__row").hide();
            // Show the Category & Unit Cost input
            $("#budget_item_category__row").show();
            $("#budget_item_unit_cost__row").show();
        }
	})
    
    // Set unused values before submitting form
    $("input[type='submit']:last").click(function(event){
        // What is the final cost type?
        cost_type=$("select[name='cost_type']").val();
        if (cost_type=="Recurring") {
            // Set the Category
            $('select#budget_item_category').val("Running Cost")
            // Set the Unit Cost input
            $('input#budget_item_unit_cost').val('0.0')
        } else if (cost_type=="One-time") {
            // Set the Running Cost inputs
            $('input#budget_item_monthly_cost').val('0.0')
            $('input#budget_item_minute_cost').val('0.0')
            $('input#budget_item_megabyte_cost').val('0.0')
        }
        // Pass to RESTlike CRUD controller
        event.default();
        return false;
    })
});
//]]></script>
