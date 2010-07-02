function import_spreadsheet(table,header_row,importsheet,map_from_ss_to_field)
{
	var map=map_from_ss_to_field;
	var impobj={};
	var temp=table.split("_");
	var prefix=temp[0];
	var name=temp[1];
	document.write(map);
	for(var i=0;i<importsheet.rows;i++)
	{
		for(var j=0;j<imporsheet.numcols;j++)
		{
			
		}
	}
	//TBD
}
