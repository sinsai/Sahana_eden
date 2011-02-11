//ocr pdf print button ext.window popup script
//@author: Shiv Deepak <idlecool@gmail.com>
//this script will only be added if number of languages is > 1.
Ext.onReady(function(){
    var langSelectWindow
    var button = Ext.get('download-pdf-btn');
    function onclickevent()
    {	
	var len = document.pdfLangForm.pdfLangRadio.length;
	var i;
	for (i=0;i<len;i++)
	{
	    if (document.pdfLangForm.pdfLangRadio[i].checked)
	    {
    		Ext.getCmp('dwnldpdfbtn').enable();
	    }
	}
    }
    function validateform()
    {
	var i;
	var radioButton = document.forms['pdf-lang-form'].pdfLangRadio;
	var langs = radioButton.length;
	alert(typeof(radioButton));
	for(i=0; i<langs; i++)
	{
	    if (radioButton[i].checked)
	    {
		return true;
	    }
	}
	return false;
    }
    var formPanel =  {
        xtype       : 'form',
        autoScroll  : true,
        defaultType : 'field',
        frame       : true,
	applyTo     : 'download-pdf-form-div'
    };
    var langSelectWindow = new Ext.Window({
	id: 'pdf-lang-selection-win',
	width:250,
//	height:300,
	title: Ext.fly('download-pdf-window-title').dom.innerHTML,
	closeAction:'hide',
	items:[formPanel],
	buttons: [{
	    id: 'dwnldpdfbtn',
	    text:'Download',
	    disabled:true,
	    handler: function(){
		if (document.pdfLangForm.pdfLangRadio.value!='')
		{
		    document.pdfLangForm.submit();
		    langSelectWindow.hide();
		}
		else
		{
		    alert("Please select language for pdf!");
		}
	    },
	},{
	    text: 'Close',
	    handler: function(){
		document.pdfLangForm.reset();
		langSelectWindow.hide();
	    }
	}]
    });
    button.on('click', function(){
	var len = document.pdfLangForm.pdfLangRadio.length;
	var i;
	for (i=0;i<len;i++)
	{
	    document.pdfLangForm.pdfLangRadio[i].onclick = onclickevent;
	}
	langSelectWindow.show(this);
    });
});
