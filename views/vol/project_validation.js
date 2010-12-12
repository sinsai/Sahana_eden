<!-- form start end date validation for vol/project form -->
<script type="text/javascript">//<![CDATA[
jQuery(document).ready(function() {
    $('.form-container > form').submit(function () {
	var datePattern = /^(19|20)\d\d([-\/.])(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$/;
	if (!(datePattern.test(this.start_date.value) && datePattern.test(this.end_date.value))) {
	    error_msg = '{{=T("start date and end date should have valid date value")}}'
	    jQuery('#project_project_end_date__row > td').last().text(error_msg);
	    jQuery('#project_project_end_date__row > td').last().addClass('red');
	    return false;
	}
	from_date = this.start_date.value.split('-')
	from_date = new Date(from_date[0], from_date[1], from_date[2])
	to_date = this.end_date.value.split('-')
	to_date = new Date(to_date[0], to_date[1], to_date[2])
	if (from_date > to_date) {
	    error_msg = '{{=T("start date should be prior to end address")}}'
	    jQuery('#project_project_end_date__row > td').last().text(error_msg);
	    jQuery('#project_project_end_date__row > td').last().addClass('red');
	    return false;
	} else {
	    return true;
	}
    });
});
//]]></script>

