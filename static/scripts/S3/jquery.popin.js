jQuery.fn.popin = function(o) {
	
	var settings = jQuery.extend({
		width : 250,
		height : 250,
		className: "",
		loaderImg: "",
		opacity: .5,
		onStart: null,
		onComplete: null,
		onExit: null
	}, o);
			
	// Action ouverture
	jQuery(this).each(function() {
		jQuery(this).click(function() {
			PPNopen($(this).attr("href"));
			return false;
		});
	});
	
	// Popin Ouverture
	var Loader = new Image();
	Loader.src = settings.loaderImg;
	
	ie6 = ($.browser.msie && ($.browser.version == "6.0")) ? true : false;

	// CSS
	$("body").css("position", "relative");
	

	function PPNopen(url) {
		
		if(settings.onStart != null) {
			settings.onStart();
		}
		
		if(ie6 == true) {
			$("#PPNCSS").remove();
			$("body").append(''
				+	'<style type="text/css" id="PPNCSS">'
				+	'.popin-voile {top:expression(documentElement.scrollTop + body.scrollTop + "px")}'
				+	'.popin {top:expression(documentElement.scrollTop + body.scrollTop + (documentElement.clientHeight/2) - ' + (settings.height/2) + ' + "px")}'
				+	'</style>'
				+	'');
		}

	
		// Insertion du voile & Verrouillage du scroll	
		$("body").prepend('<div class="popin-voile"></div>');
		
		// CSS du voile
		$(".popin-voile")	.css("opacity",						0)
							.css("left",						0)
							.css("z-index",						"9000")
							.css("width",						"100%")
							.css("height",						0)
							.css("background-color",			"#000")
							.css("background-position",			"center center")
							.css("background-repeat",			"no-repeat")
							;
		if(ie6 == true) {
			$(".popin-voile")		.css("position",					"absolute")
									;
		}
		else {
			$(".popin-voile")		.css("top",							0)
									.css("position",					"fixed")
									;
		}
		
		// Patch IE6
		if(ie6 == true) {
			
			PPNhtmlScroll 			= document.getElementsByTagName("html")[0].scrollTop;
			var PPNbodyMargin 		= new Object();
			PPNbodyMargin.top 		= parseInt($("body").css("margin-top"));
			PPNbodyMargin.right 	= parseInt($("body").css("margin-right"));
			PPNbodyMargin.bottom 	= parseInt($("body").css("margin-bottom"));
			PPNbodyMargin.left 		= parseInt($("body").css("margin-left"));
			
			$("html, body").css("height", "100%");
			$("html, body").css("overflow", "hidden");
			$("body").height($("body").height());
			PPNbodyHeight = parseInt($("body").height());
			$("html, body").css("overflow", "visible");
			$("html, body").css("overflow-x", "visible");
			
			PPNbodyTop = ((PPNbodyMargin.top + PPNbodyMargin.bottom) < PPNhtmlScroll) ? (PPNbodyMargin.top + PPNbodyMargin.bottom - PPNhtmlScroll) : 0;
			$("body").css("top", PPNbodyTop );		
			$(".popin-voile").css("top", -(PPNbodyMargin.top + PPNbodyMargin.bottom - PPNhtmlScroll) );
			$(".popin-voile").css("left", (- PPNbodyMargin.left) );
			$(".popin-voile").css("width", $("html").width());
			
		} else {
			$("html, body").css("overflow", "hidden");
		}
	
		// Affichage du voile
		$(".popin-voile").animate({opacity:settings.opacity, height:((ie6 == true) ? (PPNbodyHeight + PPNbodyMargin.top + PPNbodyMargin.bottom) : "100%")}, function() {
		
			// Loader
			$(".popin-voile").css("background-image", "url('"+settings.loaderImg+"')");
			
			// Insertion de la popin et animation
			$(".popin").css("height", $("body").height() );
							
			// Requête
			$.ajax({
				type: "GET",
				url: url,
				dataType: "html",
				success: function(m){
	
					// Création de la popin
					$("body").prepend('<div class="popin ' + settings.className + '"><div class="popin-content"></div></div>');
					
					// CSS du voile
					$(".popin")			.css("left",						"50%")
										.css("z-index",						"9500")
										.css("width",						settings.width)
										.css("height",						settings.height)
										.css("overflow",					"hidden")
										.css("margin-left",					-(settings.width/2))
										;
					$(".popin-content")	.css("overflow",					"auto")
										.css("height",							$(".popin").height()
																			- 	parseInt($(".popin").css("padding-top"))
																			- 	parseInt($(".popin").css("padding-bottom"))
																			)
										;
					if(ie6 == true) {
						$(".popin")		.css("position",					"absolute")
										.css("margin-top",					0)
										;
					}
					else {
						$(".popin")		.css("position",					"fixed")
										.css("top",							"50%")
										.css("margin-top",					-(settings.height/2))
										;
					}
					
					
					// Chargement du contenu
					$(".popin-content").html(m);
	
				},
				complete: function(){
					
					// Loader
					$(".popin-voile").css("background-image", "");
					
					// Affichage
					if(ie6 == true) {
						$(".popin").css("top", parseInt($(".popin").css("top")) - PPNbodyTop );
					}
					$(".popin").fadeIn("slow", function() {
						if(settings.onComplete != null) {
							settings.onComplete();
						}
					});
					
					// Action fermeture
					$(".popin-close, .popin-voile").click(function() {
						PPNclose();
						return false;
					});
				}
			});
	
			
		});
			
		$("html").keydown(function(e){
			if(e.keyCode == '27') {
				PPNclose();
			}
		});
	
	}
	
	// Popin fermeture
	function PPNclose() {
	
		$("html").unbind("keydown");
		
		$(".popin").fadeOut("slow", function() {
		
			$(".popin-voile").animate({opacity:0, height:0}, function() {
			
				// Suppression du voile & Déverrouillage du scroll	
				if(ie6 == true) {
					$("html, body").css("height", "auto");
					$("html, body").css("overflow", "auto");
					$("html, body").css("overflow-x", "hidden");
					$("body").css("top", 0);
					window.scrollTo(0, (PPNhtmlScroll) );
				} else {
					$("html, body").css("overflow", "auto");
				}
				$(".popin, .popin-voile").remove();
				
				if(settings.onExit != null) {
					settings.onExit();
				}
				
			});

		});
		
	}


};
