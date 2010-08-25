    // Add checkbox to hide/unhide optional school fields.
    $('#cr_shelter_school_code__row').before(
        '{{=TR(TD(LABEL(T("Is this a school?"))),
               TD(INPUT(_type="checkbox",
                        _name="is_school", _id="is_school")),
               TD())}}');
    // For update, set checked and do not hide if data is present.
    if ($('#cr_shelter_school_code').val() != "") {
        $('#is_school').attr('checked','on');
    } else {
        $('#cr_shelter_school_code__row').hide();
        $('#cr_shelter_school_pf__row').hide();
    }
    $('#is_school').change(function() {
        if ($(this).attr('checked')) {
            $('#cr_shelter_school_code__row').show();
            $('#cr_shelter_school_pf__row').show();
        } else {
            // Clear values if user unchecks? Nicer for user if the values
            // are left in, in case user accidentally unchecks.  If values not
            // cleared, either no values should be sent on submit if unchecked,
            // or checkbox setting should be tested on server and values not
            // stored if unchecked.
            $('#cr_shelter_school_code__row').hide();
            $('#cr_shelter_school_pf__row').hide();
        }
    })

    // Add checkbox to hide/unhide optional hospital field.
    $('#cr_shelter_hospital_id__row').before(
        '{{=TR(TD(LABEL(T("Is this a hospital?"))),
               TD(INPUT(_type="checkbox",
                        _name="is_hospital", _id="is_hospital")),
               TD())}}');
    // For update, set checked and do not hide if data is present.
    if ($('#cr_shelter_hospital_id').val() != "") {
        $('#is_hospital').attr('checked','on');
    } else {
        $('#cr_shelter_hospital_id__row').hide();
    }
    $('#is_hospital').change(function() {
        if ($(this).attr('checked')) {
            $('#cr_shelter_hospital_id__row').show();
        } else {
            $('#cr_shelter_hospital_id__row').hide();
        }
    })
