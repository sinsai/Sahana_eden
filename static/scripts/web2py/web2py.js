function popup(url) {
  newwindow=window.open(url,'name','height=400,width=600');
  if (window.focus) newwindow.focus();
  return false;
}
function collapse(id) { $('#'+id).slideToggle(); }
function fade(id,value) { if(value>0) $('#'+id).hide().fadeIn('slow'); else $('#'+id).show().fadeOut('slow'); }
function ajax(u,s,t) {
  var query="";
  for(i=0; i<s.length; i++) { 
     if(i>0) query=query+"&";
     query=query+encodeURIComponent(s[i])+"="+encodeURIComponent(document.getElementById(s[i]).value);
  }
  $.ajax({type: "POST", url: u, data: query, success: function(msg) { document.getElementById(t).innerHTML=msg; } });  
}
String.prototype.reverse = function () { return this.split('').reverse().join('');};
$(document).ready(function() {
    $('.hidden').hide();
    $('.error').hide().slideDown('slow');
    $('.flash').hide().slideDown('slow')
    $('.flash').click(function() { $(this).fadeOut('slow'); return false; });
    $('input.string').attr('size',50);
    $('textarea.text').attr('cols',50).attr('rows',10);
    $('input.integer').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-]|\-(?=.)/g,'').reverse();});
    $('input.double').keyup(function(){this.value=this.value.reverse().replace(/[^0-9\-\.]|[\-](?=.)|[\.](?=[0-9]*[\.])/g,'').reverse();});
});