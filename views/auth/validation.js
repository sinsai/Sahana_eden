// Client-side validation (needed to check for passwords being same)
$(document).ready(function() {
    // validate signup form on keyup and submit
    //HACK
    var validator = $('#regform').validate({
        errorClass: 'req',
        rules: {
            first_name: {
                required: true
                },
            email: {
                required: true,
                email: true
                //remote: 'emailsurl'  // TODO
            },
            password: {
                required: true
            },
            password_two: {
                required: true,
              {{if request.cookies.has_key("registered"):}}
                equalTo: '.password:last'
              {{else:}}
                equalTo: '.password:first'
              {{pass}}
            }
        },
        messages: {
            firstname: '  {{=T("Enter your firstname")}}',
            password: {
                required: '  {{=T("Provide a password")}}'
            },
            password_two: {
                required: '  {{=T("Repeat your password")}}',
                equalTo: '  {{=T("Enter the same password as above")}}'
            },
            email: {
                required: '  {{=T("Please enter a valid email address")}}',
                minlength: '  {{=T("Please enter a valid email address")}}'
            }
        },
        errorPlacement: function(error, element) {
            error.appendTo( element.parent().next() );
        },
        submitHandler: function(form) {
            form.submit();
        }
    });
});