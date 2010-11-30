    // Add checkbox to hide/unhide optional school fields.
    // If the optional hospital_id field is present, add checkbox to
    // hide/unhide it.
    if ($('#cr_shelter_hospital_id__row').length != 0) {
        $('#cr_shelter_hospital_id__row').before(
            '{{=TR(TD(LABEL(T("Is this a Hospital?")),
                      INPUT(_type="checkbox",
                            _name="is_hospital", _id="is_hospital")),
                   TD(DIV(_id="is_hospital_tooltip",
                      _class="tooltip",
                      _title=T("Hospital Information") + "|" +
                             T("If this is a hospital, please check the " +
                               "hospital checkbox, then select the " +
                               "hospital. If there is no record for " +
                               "this hospital, you can create one and " +
                               "enter just the name if no other " +
                               "information is available."))))}}');
        // Add tooltip decorations.
        $('#is_hospital_tooltip').cluetip(
            {activation: 'hover', sticky: false, splitTitle: '|'});
        // If data is present (on update), or if there's a validation error
        // (meaning box was checked but no hospital id filled in on create),
        // set checked and do not hide.
        if ($('#cr_shelter_hospital_id').val() != "" ||
            $('#cr_shelter_hospital_id__row #hospital_id__error').length != 0) {
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
    }
