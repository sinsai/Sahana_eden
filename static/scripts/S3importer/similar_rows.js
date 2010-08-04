function no_similar()
{
	Ext.onReady(function()
	{
		Ext.Msg.alert("","No similar rows!!");
	});
}

function similar(similar_rows)
{
	Ext.onReady(function()
	{
		Ext.Msg.alert("","Similar" + similar_rows);
	});
}

