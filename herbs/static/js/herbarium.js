var cpage = 1; // Current paginated page 

function incrPage(el, inc){  // Just increment the page number 
cpage = cpage + inc
herbitemFind(false);
}

function getornone(el){
var res = null;
var obj = $(el).select2('data');
if (obj !== undefined){
	if (obj[0] !== undefined){
		res = obj[0].text;	
	}
}
return res;
}


function createSearchResult(idata){
// idata -- assumed to be a plain object (converted from json response)
var sftempl = _.template($("#searchform-template").html());
var maptempl = _.template($("#herbitem-map-template").html());
var table = sftempl({items:idata.herbitems, has_previous: idata.has_previous,
							total: idata.total, 
							has_next: idata.has_next,
							pagenumber: idata.pagenumber,
							pagecount: idata.pagecount							
							}); 
var map = maptempl({items:idata.herbitems, has_previous: idata.has_previous,
							total: idata.total, 
							has_next: idata.has_next,
							pagenumber: idata.pagenumber,
							pagecount: idata.pagecount							
							}); 
var result={};
result.map = map;
result.table = table;
return result 
}

function bindSearch(model, mname){
	var element = '#' + model + '-input';
	
$(element).select2({
		language: "{{request.LANGUAGE_CODE}}",
		placeholder: '{%trans "Выберите " %}' + mname,
		ajax: {
    	 url: "{% url 'herbs.views.advice_select' %}",
  		 dataType: 'json',
  		 type: 'GET',
    	 delay: 250,
    	 cache: false,
    	 data: function (params) { 
				    	var familyname = $("#family-input :selected").text();
							var genusname = $("#genus-input :selected").text();
    	 					return {q: params.term,
    	 					model: model,
    	 					family: familyname,
    	 					genus: genusname,
    	 					};
    	 					},
	 processResults: function (data, page) {
      	return {
        	results: data.items
      	};},
    	 },
    	 escapeMarkup: function (m) { return m; }
    		});
}

var scrollPosition = 0;

function showHerbitem(herbid){
  $("table#herbitem-table tr").removeClass("herbitem-selected");
  $("#herbitem-"+herbid).addClass("herbitem-selected");
  scrollPosition = $(document).scrollTop();
  var el = $("div.herbitem-newpage");
  el.html("<h3>{%trans "Открыть в отдельном окне"%}</h3>");
  $("#herbitem-iframe").attr('src', '{{herbitem_personal_url}}' + herbid)
  $("#herbitem-tabs").tabs('option','active',1);
  el.unbind("click");
  el.click(function(){
    var win = window.open('{{herbitem_personal_url}}' + herbid, '_blank');
      if (win) {
         win.focus();
          } else {
           alert('Please allow popups for this website');
            }
  });
  $(document).scrollTop(0);
 }


function csvDownloader(response, status, xhr) {
        // check for a filename
        var filename = "";
        var disposition = xhr.getResponseHeader('Content-Disposition');
        if (disposition && disposition.indexOf('attachment') !== -1) {
            var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            var matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
        }

        var type = xhr.getResponseHeader('Content-Type');
        var blob = new Blob([response], { type: type });

        if (typeof window.navigator.msSaveBlob !== 'undefined') {
            // IE workaround for "HTML7007: One or more blob URLs were revoked by closing the blob for which they were created. These URLs will no longer resolve as the data backing the URL has been freed."
            window.navigator.msSaveBlob(blob, filename);
        } else {
            var URL = window.URL || window.webkitURL;
            var downloadUrl = URL.createObjectURL(blob);

            if (filename) {
                // use HTML5 a[download] attribute to specify filename
                var a = document.createElement("a");
                // safari doesn't support this yet
                if (typeof a.download === 'undefined') {
                    window.location = downloadUrl;
                } else {
                    a.href = downloadUrl;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                }
            } else {
                window.location = downloadUrl;
            }

            setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 100); // cleanup
        $("#herbitem-csv-loading").remove();
        }
    }; 

function herbitemFind(csvFlag){
	var family = getornone('#family-input');
	var genus = getornone('#genus-input');
	var species = $('#species-input').val();
	var itemcode = $("#itemcode-input").val();
	var identifiedby = $("#identifiedby-input").val();
	var collectedby = $("#collectedby-input").val();
	var country = getornone("#country-input");
	var colstart = $("#colstart-input").val();
  var colend = $("#colend-input").val();
  var place = $("#place-input").val();

  var acronym = $("#herbitem-acronym").val();
  var pagcount = $("#herbitem-pagination").val();
  var subdivision = $("#herbitem-subdivision").val();
  var synonyms = $("#synonyms-input").is(":checked");
  var additionals = $("#additionals-input").is(":checked"); 

  // TODO: orderby field, increasing decreasing ordering
  var orderby = null;
  var order = null;
  var latl = $('#latl-input').val();
  var latu = $('#latu-input').val();
  var lonl = $('#lonl-input').val();
  var lonu = $('#lonu-input').val();
  var outputHTML = '';
  var errorString = '';
  var warningString = '';
  var outputData = null;
  var commonError = "{%trans "Возникла ошибка при получении ответа за поисковый запрос" %}";
  if (csvFlag){
    $("#herbitem-csv-export").append('<div class="herbitem-loader" id="herbitem-csv-loading" style="width: 16px; height: 16px;background-size:cover;"></div>');
  }

  if (!csvFlag) {
   $("#herbitem-content-found").html('<div class="herbitem-loader"></div>')
   $.get("{% url 'herbs.views.show_herbs' %}",
			{family:family, genus:genus, species_epithet:species, itemcode:itemcode,
			identifiedby:identifiedby,place:place,collectedby:collectedby, country:country, colstart:colstart,
			colend:colend, page:cpage, pagcount: pagcount,acronym:acronym, subdivision:subdivision,
      latl:latl, lonl: lonl, latu:latu, lonu:lonu, synonyms: synonyms, additionals: additionals,
      orderby:orderby, order:order      
      }).done(function(data) {
      if (data.warnings.length>0){
        warningString += '<ul class="herbitem-warnings">'
      for(var i=0;i<data.warnings.length; i++){
               warningString += '<li>' +  data.warnings[i] + '</li>'
              }
               warningString += '</ul>'}

      if (data.errors.length > 0) {
        errorString += '<ul class="herbitem-errors">'
        for (var i=0; i<data.errors.length; i++){
              errorString +=   '<li>' +  data.errors[i] + '</li>'
                           }
        errorString += '</ul>'
           } else {
      outputHTML = createSearchResult(data);
      outputData = data;
      }}
			).fail(function() {
        $("#herbitem-content-found").html("<h2>" + commonError + "</h2>")
        $("#herbitem-map").html("<h2>" + commonError + "</h2>")
      }).always(function () {
                            $("#herbitem-content-found").html( outputHTML.hasOwnProperty('table') ? warningString + errorString + outputHTML.table : "<h2>" + commonError + "</h2>" + warningString + errorString);
        $("#herbitem-map-pagelister").html(outputHTML.hasOwnProperty('map') ? warningString + errorString + outputHTML.map : "<h2>" + commonError + "</h2>" + warningString + errorString);
        if (outputData&&google) { 
            renderMap(outputData);      
          };      
      })	
                            
  }
  else{
    $.get("{% url 'herbs.views.show_herbs' %}",
			{family:family, genus:genus, species_epithet:species, itemcode:itemcode,
			identifiedby:identifiedby,place:place,collectedby:collectedby, country:country, colstart:colstart,
			colend:colend, page:cpage, pagcount: pagcount,acronym:acronym, subdivision:subdivision,
      latl:latl, lonl: lonl, latu:latu, lonu:lonu, getcsv:csvFlag, synonyms: synonyms, additionals: additionals,
      orderby:orderby, order:order      
      }, csvDownloader);
    }

};

var markers=[];
var infoWindows=[];
var map=null;
var rectSelector=null;
                                         
function clearMarkers() {
  for (var i = 0; i < markers.length; i++ ) {
  markers[i].setMap(null);
  infoWindows[i].close();

}
markers.length = 0;
infoWindows.length = 0;
};


function initHerbitemMap(){
el = document.getElementById('herbitem-map-placeholder');
if (map == null && google){ 
    map = new google.maps.Map(el, {
            zoom: 2,
            center: {'lat': 43.0,'lng': 132.0},
            mapTypeId: 'hybrid'});

    map.addListener('dblclick', function (event) {
              if (rectSelector == null){ 
             var thepoint = event.latLng;
             bounds = {
                  north: thepoint.lat() + 3,
                  south: thepoint.lat() - 3,
                  east:  thepoint.lng() + 3,
                  west:  thepoint.lng() - 3}
                  initRectSelection(bounds);
                  $("#latl-input").val(bounds.south);
                  $("#latu-input").val(bounds.north);
                  $("#lonu-input").val(bounds.east);
                  $("#lonl-input").val(bounds.west);                  
                            }})}};


function updateLatLng(){
   if (map != null && rectSelector != null) {
        var ne = rectSelector.getBounds().getNorthEast();
        var sw = rectSelector.getBounds().getSouthWest();
        $('#lonl-input').val(sw.lng());
        $('#lonu-input').val(ne.lng());
        $('#latu-input').val(ne.lat());
        $('#latl-input').val(sw.lat());
        }}; 


function initRectSelection(bounds){
  if (map != null){
      var mapCenter = map.getCenter();
      var mapBounds = map.getBounds();
      var scale;
      scale = (mapBounds.north - mapBounds.south)/5.0
      if (!bounds) {      
      var bounds;
      bounds = {
                north: mapCenter.lat() + scale,
                south: mapCenter.lat() - scale,
                east:  mapCenter.lng() + scale,
                west:  mapCenter.lng() - scale
                                           };
                                           }
      rectSelector = new google.maps.Rectangle({
                        bounds: bounds,
                        editable: true,
                        draggable: true,
                        fillOpacity: 0.4,
                        fillColor: '#11AA33'
                                  });
      rectSelector.setMap(map);
      rectSelector.addListener('bounds_changed', updateLatLng);
      if (!($('div.clear-rect-bounds').is(":visible"))){ 
        $('div.clear-rect-bounds').show();};
  }
  else{
    alert("{% trans "Карты google еще не инициализированы"%}");
  }
}

function renderMap(data){
  var avLat=0.0, avLon=0.0;

if (map&&google) {
clearMarkers();
}
else if (google){
initHerbitemMap();
clearMarkers();
}
else{return;}

var indw=0;
for(var i=0; i<data.herbitems.length; i++){
var pos={'lat': parseFloat(data.herbitems[i].lat), 'lng': parseFloat(data.herbitems[i].lon)}
if ((!pos['lat']==0)&&(!pos['lng']==0)){                                          
var marker=new google.maps.Marker({
              position: pos,
              map: map,
              herbitemid: data.herbitems[i].id,
              wix: indw
                                           });
            var infoString='<strong> <b>{%trans "Вид"%}: </strong>' + data.herbitems[i].species + '</br>'
                 + '<strong> {%trans "Дата сбора"%}: </strong>'+ data.herbitems[i].collected_s + '</br>'
                 + '<strong> {%trans "Собрал(и)"%}: </strong>' + data.herbitems[i].collectedby + '</br>'
                       + '<strong> {%trans "Широта"%}: </strong>' + data.herbitems[i].lat + '</br>'                                             + '<strong> {%trans "Долгота"%}: </strong>' + data.herbitems[i].lon + '</p>'                   
var infowindow = new google.maps.InfoWindow({
   content: infoString,
   disableAutoPan: true});
infoWindows.push(infowindow);
                                           
marker.addListener('click', function() {
      showHerbitem(this.herbitemid);
                                           });

marker.addListener('mouseover', function() {
    infoWindows[this.wix].open(map, this);

               });
marker.addListener('mouseout', function() {
  for(var i =0;i<infoWindows.length; i++){ infoWindows[i].close();}
               });

markers.push(marker);
indw+=1;
  }}

var a,b, cnt=0;
for(var i = 0; i < markers.length; i++){
   a =  pos['lat'];
   b  = pos['lng']
  if ((a!=0.0)&&(b!=0.0)){
   cnt += 1
   avLat += a;
   avLon += b;
    };

  };

if (cnt == 0) {
  avLat=0.0; avLon=0.0;
  }
else {
  avLat = avLat/cnt;
  avLon = avLon/cnt;
  }

  if (markers){
for (var i =0; i<markers.length; i++){markers[i].setMap(map)};
 $("#herbitem-markers-available").html('{% trans "На карте отображено" %} ' + markers.length + ' {% trans "запись(ей)" %}*');
                              } 
else{
  $("#herbitem-markers-available").html('');
   }                           
};

function applyFilter(){
  cpage = 1
  herbitemFind(false)
}

//<!-- ============ When DOM is ready ============  -->
$(document).ready(function() { 

bindSearch('family', "{% trans 'Семейство'%}");
bindSearch('genus', "{% trans 'Род'%}");
bindSearch('country', "{% trans 'Страну'%}");

$('#herbitemform-button').click(function (event){
	event.preventDefault();
  cpage = 1;
	herbitemFind(false);
	})
$("#colstart-input, #colend-input").click(function (event){
	$(this).siblings('div.clear-button').css('display', 'inline-block');
})
$("div>input[type=search]" ).keypress(function() {
  $(this).siblings('div.clear-button').css('display', 'inline-block')
});

$('select').on("select2:selecting", function(e) { 
  $(this).siblings('div.clear-button').css('display', 'inline-block')
});

$("#latlon-rect").click(function(){
  cpage=1;
  herbitemFind(false);
});

$('div.clear-button').click(function (event){
$(this).css('display', 'none')
var el = $(this).siblings('select') 
if (el.length !== 0 ) { //Clearing select element
el.select2('val', '');
} else{
$(this).siblings('input[type=search]').val(''); //cleaning regular input field
}a
});

$('div.clear-rect-bounds').click(function(){
$(this).css('display', 'none');
$('#latl-input').val('');
$('#latu-input').val('');
$('#lonl-input').val('');
$('#lonu-input').val('');
if (rectSelector!=null){rectSelector.setMap(null);};
rectSelector=null;
});

$("#colstart-input").datepicker({dateFormat: "dd.mm.yy"});
$("#colend-input").datepicker({dateFormat: "dd.mm.yy"});
$("#searchform-clear").click(function (event){
	event.preventDefault();
$("#synonyms-input").prop('checked', false);
$("#additionals-input").prop('checked', false);
clearMarkers();
$("#synonyms-error-message").hide(); 
$('#family-input').select2('val',''); 
$('#genus-input').select2('val', '');
$('#country-input').select2('val', '');
$('div>input[type=search]').val('');
$("#herbitem-search-filtering select").val('');
$('div.clear-button').hide();
$("div.clear-rect-bounds").hide();
// Clear map rectangular filtering
$('#latl-input').val('');
$('#latu-input').val('');
$('#lonl-input').val('');
$('#lonu-input').val('');
if (rectSelector!=null){rectSelector.setMap(null);};
rectSelector=null;
$( "div#herb-search-form ul li input:text" ).each(function() {  
	$(this).val('');
});

cpage = 1;// <!-- Find cpage in the outer scope and change it; i.e. pagination counter -->
herbitemFind(false);
});

$("#latl-input, #latu-input, #lonl-input, #lonu-input").change(function(){
  var latl, latu, lonl, lonu;
  latl = $("#latl-input").val();
  lonl = $("#lonl-input").val();
  latu = $("#latu-input").val();
  lonu = $("#lonu-input").val();
  if (latl&&lonl&&latu&&lonu){
      if (rectSelector != null){
      rectSelector.setMap(null);
      rectSelector = null
      };
       var bounds;
       bounds = {
                north: parseFloat(latu),
                south: parseFloat(latl),
                east:  parseFloat(lonu),
                west:  parseFloat(lonl)}
        try {      
             initRectSelection(bounds);
             }
        catch (err){
         return;}
  }
  if (!latl&&!lonl&&!latu&&!lonu){
    if (rectSelector != null){
      rectSelector.setMap(null);
      rectSelector = null;
    }
  }
});

$("#species-input, #genus-input").change(function(){
  var genus = getornone('#genus-input');
  var species = $('#species-input').val();
  if ((genus!=null)&&(species.length>0))
  {$("#synonyms-error-message").hide();}
});

$("#synonyms-input").change(function(){
  var genus = getornone('#genus-input');
	var species = $('#species-input').val();
  if (this.checked){
    if ((genus==null)||(species.length==0)){
    $("#synonyms-error-message").show();
    
    }}
  else {
    $("#synonyms-error-message").hide();
  }});


$("#herbitem-search-filtering select").change(applyFilter);
$("#herbitem-tabs").tabs({active: 0, 
  activate: function(el,ui){
   if (ui.newPanel.selector == "#herbitem-content-main"){
    $(document).scrollTop(scrollPosition);
    scrollPosition = 0;
   }
  if (ui.newPanel.selector == '#herbitem-map'){
     if (google&&map){google.maps.event.trigger(map,'resize');
        };
  }

}});

var colwidth = $("div.centralcontainer").width();
var swidth = $("#herb-search-form").width();
$("#herbitem-tabs").width(colwidth-swidth-40 + 'px')
$("#herbitem-filtering-container").width(colwidth-swidth-40+'px');
$("#herbitem-filtering").show();
herbitemFind(false);
$("#herbitem-tabs").tabs('option','active',0);
$("#tab-preloader").remove();
$("#herbitem-tabs").show();
initHerbitemMap();
});

