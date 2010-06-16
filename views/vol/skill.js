<head>
<script type="text/javascript">//<![CDATA[

//alert("foo");
 
   jQuery(document).ready(function(){
 //   $("#vol_skill_General_Skill__row").hide();
    $("#vol_skill_Animals__row").hide();
        $("#vol_skill_Animal_Control_Vehicles__row").hide();
        $("#vol_skill_Animal_Handling__row").hide();
        $("#vol_skill_Other__row").hide();
    $("#vol_skill_Automotives__row").hide();
        $("#vol_skill_Body_Repair__row").hide();
        $("#vol_skill_Engine_Repair__row").hide();
        $("#vol_skill_Tire_Repair__row").hide();
    $("#vol_skill_Electrical__row").hide();
        $("#vol_skill_External_Wiring__row").hide();
        $("#vol_skill_Internal_Wiring__row").hide();
        
        
    $("#vol_skill_Building_Aide__row").hide();
        $("#vol_skill_Own_BackHoe__row").hide();
        $("#vol_skill_Own_Crane__row").hide();
    $("#vol_skill_Vehicle__row").hide();
        $("#vol_skill_Own_Aircraft__row").hide();
        $("#vol_skill_Own_Boat__row").hide();
    $("#vol_skill_Warehouse__row").hide();
        $("#vol_skill_ForkLift__row").hide();
        $("#vol_skill_General__row").hide();
        
    $("#vol_skill_Can_not_Drive__row").hide();
    $("#vol_skill_Can_not_Swim__row").hide();
    $("#vol_skill_No_Heavy_Lifting__row").hide();
    
    $("#vol_skill_Skill_Other__row").hide();
        $("#vol_skill_Baby_Care_Help__row").hide();
        $("#vol_skill_Clerical__row").hide();
        $("#vol_skill_Food_Help__row").hide();
    $("#vol_skill_With_Tools__row").hide();
        $("#vol_skill_With_Brooms__row").hide();
        $("#vol_skill_With_Carpentry_Tools__row").hide();
        $("#vol_skill_With_Other_Tools__row").hide();
    
       

//General skill
        $('#vol_skill_General_Skill').css({'margin-left': '50px'}).change(function(){

            if($('#vol_skill_General_Skill').attr('checked')){
            
                //jQuery("#vol_skill_Animals__row").margin(left: 100);
                $("#vol_skill_Animals__row").show();
                        $('#vol_skill_Animals').css({'margin-left': '50px'}).change(function(){
                            if($('#vol_skill_Animals').attr('checked')){
                                $("#vol_skill_Animal_Control_Vehicles__row").show();
                                $("#vol_skill_Animal_Handling__row").show(); 
                                $("#vol_skill_Other__row").show();                                
                                        }else{
                                $("#vol_skill_Animal_Control_Vehicles__row").hide();
                                $("#vol_skill_Animal_Handling__row").hide(); 
                                $("#vol_skill_Other__row").hide();
                                $("#vol_skill_Animal_Control_Vehicles").removeAttr('checked');
                                $("#vol_skill_Animal_Handling").removeAttr('checked');
                                $("#vol_skill_Other").removeAttr('checked');
                                }
                                });
                
                $("#vol_skill_Automotives__row").show();
                
                        $('#vol_skill_Automotives').css({'margin-left': '50px'}).change(function(){
                            if($('#vol_skill_Automotives').attr('checked')){
                                $("#vol_skill_Body_Repair__row").show();
                                $("#vol_skill_Engine_Repair__row").show(); 
                                $("#vol_skill_Tire_Repair__row").show();                                
                                        }else{
                                $("#vol_skill_Body_Repair__row").hide();
                                $("#vol_skill_Engine_Repair__row").hide();  
                                $("#vol_skill_Tire_Repair__row").hide();
                                $("#vol_skill_Body_Repair").removeAttr('checked');
                                $("#vol_skill_Engine_Repair").removeAttr('checked');
                                $("#vol_skill_Tire_Repair").removeAttr('checked');
                                }
                                });

                $("#vol_skill_Electrical__row").show();
                
                       $('#vol_skill_Electrical').css({'margin-left': '50px'}).change(function(){
                            if($('#vol_skill_Electrical').attr('checked')){
                                $("#vol_skill_External_Wiring__row").show();
                                $("#vol_skill_Internal_Wiring__row").show(); 

                                        }else{
                                $("#vol_skill_External_Wiring__row").hide();
                                $("#vol_skill_Internal_Wiring__row").hide();  
                                $("#vol_skill_External_Wiring").removeAttr('checked');
                                $("#vol_skill_Internal_Wiring").removeAttr('checked');
                                }
                                });
           
                

            }else {
           
             $("#vol_skill_Animals__row").hide();
             $("#vol_skill_Automotives__row").hide();
             $("#vol_skill_Electrical__row").hide();
             
             $("#vol_skill_Animal_Control_Vehicles__row").hide();
             $("#vol_skill_Animal_Handling__row").hide(); 
             $("#vol_skill_Other__row").hide();
             
             $("#vol_skill_Body_Repair__row").hide();
             $("#vol_skill_Engine_Repair__row").hide();  
             $("#vol_skill_Tire_Repair__row").hide();
             
             $("#vol_skill_External_Wiring__row").hide();
             $("#vol_skill_Internal_Wiring__row").hide();           
             
             
             $("#vol_skill_Animals").removeAttr('checked');
             $("#vol_skill_Automotives").removeAttr('checked');
             $("#vol_skill_Electrical").removeAttr('checked');
             
             
              $("#vol_skill_Animal_Control_Vehicles").removeAttr('checked');
              $("#vol_skill_Animal_Handling").removeAttr('checked');
              $("#vol_skill_Other").removeAttr('checked');
              

              $("#vol_skill_Body_Repair").removeAttr('checked');
              $("#vol_skill_Engine_Repair").removeAttr('checked');
              $("#vol_skill_Tire_Repair").removeAttr('checked');              
              
              $("#vol_skill_External_Wiring").removeAttr('checked');
              $("#vol_skill_Internal_Wiring").removeAttr('checked');            
            }
            });

//Resources Start        
        jQuery('#vol_skill_Resources').css({'margin-left': '50px'}).change(function(){

            if(jQuery('#vol_skill_Resources').attr('checked')){
            
                $("#vol_skill_Building_Aide__row").show();
                $("#vol_skill_Vehicle__row").show();
                $("#vol_skill_Warehouse__row").show();
    
                

            }else {
           
              $("#vol_skill_Building_Aide__row").hide();
              $("#vol_skill_Vehicle__row").hide();
              $("#vol_skill_Warehouse__row").hide();
              $("#vol_skill_Building_Aide").removeAttr('checked');
              $("#vol_skill_Vehicle").removeAttr('checked');
              $("#vol_skill_Warehouse").removeAttr('checked');
            
            }
            });      
            

//Restriction Start        
        jQuery('#vol_skill_Restrictions').css({'margin-left': '50px'}).change(function(){

            if(jQuery('#vol_skill_Restrictions').attr('checked')){
            
                $("#vol_skill_Can_not_Drive__row").show();
                $("#vol_skill_Can_not_Swim__row").show();
                $("#vol_skill_No_Heavy_Lifting__row").show();
    
                

            }else {
           
              $("#vol_skill_Can_not_Drive__row").hide();
              $("#vol_skill_Can_not_Swim__row").hide();
              $("#vol_skill_No_Heavy_Lifting__row").hide();
              $("#vol_skill_Can_not_Drive").removeAttr('checked');
              $("#vol_skill_Can_not_Swim").removeAttr('checked');
              $("#vol_skill_No_Heavy_Lifting").removeAttr('checked');
            
            }
            });               
            
 
 jQuery('#vol_skill_Site_Manager').css({'margin-left': '50px'});
 
 //Unskilled Start
 //jQuery('#vol_skill_Unskilled').css({'margin-left': '50px'});
 
  $('#vol_skill_Unskilled').css({'margin-left': '50px'}).change(function(){

            if($('#vol_skill_Unskilled').attr('checked')){
            
                //jQuery("#vol_skill_Animals__row").margin(left: 100);
                $("#vol_skill_Skill_Other__row").show();
                        $('#vol_skill_Skill_Other').css({'margin-left': '50px'}).change(function(){
                            if($('#vol_skill_Skill_Other').attr('checked')){
                                $("#vol_skill_Baby_Care_Help__row").show();
                                $("#vol_skill_Clerical__row").show(); 
                                $("#vol_skill_Food_Help__row").show();                                
                                        }else{
                                $("#vol_skill_Baby_Care_Help__row").hide();
                                $("#vol_skill_Clerical__row").hide(); 
                                $("#vol_skill_Food_Help__row").hide();
                                $("#vol_skill_Baby_Care_Help").removeAttr('checked');
                                $("#vol_skill_Clerical").removeAttr('checked');
                                $("#vol_skill_Food_Help").removeAttr('checked');
                                }
                                });
                
                $("#vol_skill_With_Tools__row").show();
                
                        $('#vol_skill_With_Tools').css({'margin-left': '50px'}).change(function(){
                            if($('#vol_skill_With_Tools').attr('checked')){
                                $("#vol_skill_With_Brooms__row").show();
                                $("#vol_skill_With_Carpentry_Tools__row").show(); 
                                $("#vol_skill_With_Other_Tools__row").show();                                
                                        }else{
                                $("#vol_skill_With_Brooms__row").hide();
                                $("#vol_skill_With_Carpentry_Tools__row").hide();  
                                $("#vol_skill_With_Other_Tools__row").hide();
                                $("#vol_skill_With_Brooms").removeAttr('checked');
                                $("#vol_skill_With_Carpentry_Tools").removeAttr('checked');
                                $("#vol_skill_With_Other_Tools").removeAttr('checked');
                                }
                                });

                            

            }else {
           
             $("#vol_skill_Skill_Other__row").hide();
             $("#vol_skill_With_Tools__row").hide();

             
             $("#vol_skill_Baby_Care_Help__row").hide();
             $("#vol_skill_Clerical__row").hide(); 
             $("#vol_skill_Food_Help__row").hide();
             
             $("#vol_skill_With_Brooms__row").hide();
             $("#vol_skill_With_Carpentry_Tools__row").hide();  
             $("#vol_skill_With_Other_Tools__row").hide();
                          
             $("#vol_skill_Other").removeAttr('checked');
             $("#vol_skill_With_Tools").removeAttr('checked');

                         
              $("#vol_skill_Baby_Care_Help").removeAttr('checked');
              $("#vol_skill_Clerical").removeAttr('checked');
              $("#vol_skill_Food_Help").removeAttr('checked');
              

              $("#vol_skill_With_Brooms").removeAttr('checked');
              $("#vol_skill_With_Carpentry_Tools").removeAttr('checked');
              $("#vol_skill_With_Other_Tools").removeAttr('checked');              
                  
            }
            });
            

          


   });

 
 
</script>
</head>
