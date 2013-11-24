function main(zoomval, lat, lng) {

  zoomval = typeof zoomval === 'undefined' ? 4 : zoomval;
  lat = typeof lat === 'undefined' ? 40 : lat;
  lng = typeof lng === 'undefined' ? -98.5 : lng;
  
  // Define the map options
  var cartodbMapOptions = {
    zoom: zoomval,
    center: new google.maps.LatLng(lat, lng),
    disableDefaultUI: true,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  
  // Init the map
  var map = new google.maps.Map(document.getElementById("map"),cartodbMapOptions);
  
  // move zoom buttons to lower right
  map.setOptions({zoomControl: true,
    zoomControlOptions: {
      style: google.maps.ZoomControlStyle.SMALL,
      position: google.maps.ControlPosition.RIGHT_BOTTOM
    }
  });
  
  // Define the map style to appear very minimalistic and washed out
  var mapStyle = [{stylers: [{ saturation: -65 }, { gamma: 1.52 }] }, 
    {featureType: "administrative", stylers: [{ saturation: -95 }, { gamma: 2.26 }] }, 
    {featureType: "water", elementType: "labels", stylers: [{ visibility: "off" }] }, 
    {featureType: "administrative.locality", stylers: [{ visibility: 'off' }] }, 
    {featureType: "road", stylers: [{ visibility: "simplified" }, { saturation: -99 }, { gamma: 2.22 }] }, 
    {featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }, 
    {featureType: "road.arterial", stylers: [{ visibility: 'off' }] }, 
    {featureType: "road.local", elementType: "labels", stylers: [{ visibility: 'off' }] }, 
    {featureType: "transit", stylers: [{ visibility: 'off' }] }, 
    {featureType: "road", elementType: "labels", stylers: [{ visibility: 'off' }] }, 
    {featureType: "poi", stylers: [{ saturation: -55 }] } 
  ];
  
  map.setOptions({styles: mapStyle});
  
  return map;
  
};

function add_tiles(map, sqlquery, cartocss) {
  
  cartodb.createLayer(map, {
    user_name: 'censusmapper',
    type: 'cartodb',
    sublayers: [{
      sql: sqlquery,
      cartocss: cartocss
    }]
  })
  .addTo(map)
  
};

function add_legend() {
  
  // Create a div to hold the control.
  var controlDiv = document.createElement('div');
  
  // Set CSS styles for the DIV containing the control
  // Setting padding to 5 px will offset the control
  // from the edge of the map.
  controlDiv.style.padding = '10px';
  
  // Set CSS for the control border.
  var controlUI = document.createElement('div');
  controlUI.style.backgroundColor = 'white';
  controlUI.style.borderStyle = 'solid';
  controlUI.style.borderWidth = '1px';
  controlUI.style.borderColor = '#dddddd';
  controlUI.style.cursor = 'pointer';
  controlUI.style.textAlign = 'center';
  controlUI.title = 'Click to set the map to Home';
  controlDiv.appendChild(controlUI);
  
  // Set CSS for the control interior.
  var controlText = document.createElement('div');
  controlText.style.fontFamily = 'Helvetica,Arial,sans-serif';
  controlText.style.fontSize = '12px';
  controlText.style.paddingLeft = '4px';
  controlText.style.paddingRight = '4px';
  controlText.innerHTML = '<strong>Home</strong>';
  controlUI.appendChild(controlText);
  
  map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(controlDiv);
  
};

function adjust_height() {
  var height = window.innerHeight;
  document.getElementById("map").style.height = height - 56 + 'px';
};

