$(document).ready(function() {
$('.error').hide().slideDown('slow')
$('.error').click(function() { $(this).fadeOut('slow'); return false; });
$('.warning').hide().slideDown('slow')
$('.warning').click(function() { $(this).fadeOut('slow'); return false; });
$('.information').hide().slideDown('slow')
$('.information').click(function() { $(this).fadeOut('slow'); return false; });
$('.confirmation').hide().slideDown('slow')
$('.confirmation').click(function() { $(this).fadeOut('slow'); return false; });
$('.tooltip').cluetip({activation: 'click',splitTitle: '|',closePosition: 'bottom'});
});
