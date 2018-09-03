var all_circles = [];
var all_infos = [];
var all_colors = ['red', 'orange', 'yellow', 'green'];

var legend_lines = {
  temperature: ['> 40&#8451', '38-40&#8451', '36-38&#8451', '< 36&#8451'],
  rainfall: ['> 10mm', '8-10mm', '6-8mm', '< 6mm'],
  humidty: ['> 60%', '57.5-60%', '55-57.5%', '< 55%'],
  flood: ['> 70%', '60-70%', '50-60%', '< 50%'],
  windspeed: ['> 14 km/h', '12-14 km/h', '10-12 km/h', '< 10 km/h']
}

console.log(villages);

function circleColor(time) {
    orange_min = 5*24*60;
    red_min = 8*24*60;
    date = new Date(time.substring(0,19));
    console.log(date);
    var d = new Date();
    var utc = d.getTime() + (d.getTimezoneOffset() * 60000);
    var now = new Date(utc + (3600000*5.5));
    if ((now-date) > red_min*60*1000) {
        // return '#ffb3b3';
        return 'red';
    }
    else if ((now-date) > orange_min*60*1000) {
        // return '#ffe0b3';
        return 'orange';
    }
    else {
        // return '#c1f0c1';
        console.log(now-date)
        return 'green';
    }
}

function randrange(min, max, dec) {
  // return Math.floor(Math.random() * max)
  return (Math.random() * (max - min) + min).toFixed(dec);
}

function randint(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function circleSize(rainfall) {
  // return Math.pow(10,3)*5;
  return 7000;
}

function showVillageDetails(event) {

  // $('#village-name').text($(this)[0].data);

  // $('#flood-val').text(randint(0,100) + '%');
  // $('#rainfall-val').text(randrange(0,3,1) + ' mm ('+randint(0,100) + '%)');
  // $('#windspeed-val').text(randint(0,20) + ' km/h');
  // $('#maxtemp-val').text(randint(0,100) + ' C');
  // $('#mintemp-val').text(randint(0,100) + ' C');
  // $('#humidity-val').text(randint(0,100) + '%');

  // console.log(event);
  // console.log($(this)[0].data);
  // console.log(event.data);
  // console.log(data);
}

function controlLine(ui, type, params) {

  var line = document.createElement('div');
  line.style.color = 'rgb(25,25,25)';
  line.style.fontFamily = 'Roboto,Arial,sans-serif';
  line.style.fontSize = '16px';
  line.style.fontWeight = '300';
  line.style.lineHeight = (type == 'legendLine') ? '24px' : '38px';
  line.style.paddingLeft = (type == 'legendLine') ? '20px' : '10px';
  line.style.paddingRight = (type == 'legendLine') ? '20px' : '10px';

  // line.style.paddingTop = '5px';
  // line.style.paddingBottom = '5px';
  if (type == 'legendLine') {
    if (params.color == 'red') {
    line.style.paddingTop = '10px';
    }
    if (params.color == 'green') {
      line.style.paddingBottom = '10px';
    }
    line.innerHTML = '<svg height="20" width="30"><circle cx="10" cy="10" r="8" stroke='
    + params.color + ' stroke-width="2" fill=' + params.color 
    + ' fill-opacity="0.35" stroke-opacity="0.8"/></svg>' + params.text;
// strokeColor: villageColor,
//       strokeOpacity: 0.8,
//       strokeWeight: 2,
//       fillColor: villageColor,
//       // fillColor: circleColor(),
//       fillOpacity: 0.35,
  }
  else {
    line.innerHTML = params.text;
  }
  ui.appendChild(line);

}

function controlTable(controlDiv, params) {
  var table = document.createElement('table');
  table.style.color = 'rgb(25,25,25)';
  table.style.fontFamily = 'Roboto,Arial,sans-serif';
  table.style.fontSize = '14px';
  table.style.fontWeight = '300';
  table.style.paddingLeft = '10px';
  table.style.paddingRight = '10px';
  // table.style.paddingTop = '20px';
  table.style.paddingBottom = '10px';
  table.style.textAlign = 'left';
  
  for (var param of params) {
    // console.log(param, param.name, param.value)
    var tr = document.createElement('tr');
    var td1  = document.createElement('td');
    var td2 = document.createElement('tr');
    var text1 = document.createTextNode(param.name);
    var text2 = document.createTextNode(param.value);
    td1.appendChild(text1);
    td2.appendChild(text2);
    tr.appendChild(td1);
    tr.appendChild(td2);
    table.appendChild(tr);
  }

  controlDiv.appendChild(table);
}

function createControl(controlDiv, map, controlType, text) {
  // Set CSS for the control border.
  var controlUI = document.createElement('div');
  controlUI.style.backgroundColor = '#fff';
  controlUI.style.border = '2px solid #fff';
  controlUI.style.borderRadius = '3px';
  controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
  controlUI.style.cursor = 'pointer';
  controlUI.style.marginRight = '22px';
  controlUI.style.marginTop = '22px';
  controlUI.style.marginLeft = (controlType == 'measurement') ? '0px' : '22px';
  controlUI.style.marginBottom = '22px';

  controlUI.style.textAlign = (controlType == 'legend') ? 'left' : 'center';
  controlUI.title = '';
  controlDiv.appendChild(controlUI);

  if (controlType == 'legend') {

    controlUI.id = 'div-legend';

    for (var i=0; i < legend_lines['rainfall'].length; i++) {
      var line = legend_lines['rainfall'][i];
      var legendLine = new controlLine(controlUI, 
        'legendLine', {'text': line, 'color': all_colors[i]});
    }

    // var legendLine1 = new controlLine(controlUI, 
    //  'legendLine', {'text': 'Very high', 'color': 'red'});
    // var legendLine2 = new controlLine(controlUI, 
    //  'legendLine', {'text': 'High', 'color': 'orange'});
    // var legendLine3 = new controlLine(controlUI, 
    //  'legendLine', {'text': 'Average', 'color': 'yellow'});
    // var legendLine4 = new controlLine(controlUI, 
    //  'legendLine', {'text': 'Low', 'color': 'green'});
    // var legendLine1 = new legendLine(controlUI, 'Very High', 'red');
    // var legendLine2 = new legendLine(controlUI, 'High', 'orange');
    // var legendLine3 = new legendLine(controlUI, 'Average', 'yellow');
    // var legendLine4 = new legendLine(controlUI, 'Low', 'green');

  }
  else if (controlType == 'details') {

    var detailsLine = new controlLine(controlUI, 'detailLine', {'text': 'Dadenggre'})
    var detailsTable = new controlTable(controlUI, [
      {'name': 'Chance of flood', 'value': '40%'},
      {'name': 'Rainfall', 'value': '1.5 mm (50%)'},
      {'name': 'Windspeed', 'value': '13 km/h'},
      {'name': 'Max temp', 'value': '30 C'}, 
      {'name': 'Min temp', 'value': '22 C'},
      {'name': 'Humidity', 'value': '48%'}
    ]);
    // controlUI.appendChild(detailsTable);

  }
  else if (controlType == 'params') {
    var generalLine = new controlLine(controlUI, 'general');
  }
  else if (controlType == 'measurement') {
    var generalLine = new controlLine(controlUI, 'general');
  }
  else {

    var generalLine = new controlLine(controlUI, 'general', {'text': text});

  }

  controlUI.addEventListener('click', function() {
    // map.setCenter(chicago);
    // alert('clicked');
  });
}

function getCenter(villages) {

  var sum_lat = 0.;
  var sum_lng = 0.;

  for (var v in villages) {
    village = villages[v];
    sum_lat += village.lt;
    sum_lng += village.ln;
  }

  return {
    'lat': sum_lat/villages.length, 
    'lng': sum_lng/villages.length
  }

}

function initMap() {
  // get map center
  var map_center = getCenter(villages);

  // Create the map.
  var map = new google.maps.Map(document.getElementById('map'), {
    // zoom: 10,
    zoom: 9,
    // center: {lat: 25.721316, lng: 90.194303},
    center: map_center,
    mapTypeId: google.maps.MapTypeId.TERRAIN,
    mapTypeControl: false,
    zoomControl: true,
    zoomControlOptions: {
      position: google.maps.ControlPosition.LEFT_BOTTOM
    },
    scaleControl: true,
    streetViewControl: false,
    fullScreenControl: true
  });

  // Construct the circle for each value in citymap.
  // Note: We scale the area of the circle based on the population.
  var index = 0
  for (var v in villages) {

    var village = villages[v]
    var villageColor = circleColor(village.ts);
    var villageInfo = new google.maps.InfoWindow({
      content: '<div id="content">'
      +'<h3>' + village.name + '&nbsp<a href="ws/'+village.id+'">' 
      + '<img width="15px" padding-left="30px" src="../static/img/download.svg"></a>&nbsp<a href="analytics/'+village.id+'">' 
      + '<img width="15px" padding-left="60px" src="../static/img/chart2.jpg"></a></h3>'
      + '<i>Updated: '+village.ts.substring(0,19)+'</i>'
      // + '<a href="#">Download data</a>'
      + '<br /><br />'
        + '<table>'
          +'<tr><td>Air temperature&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+(parseFloat(village.t)).toFixed(1)+'&deg;C</td></tr>'
          +'<tr><td>Humidity&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+(parseFloat(village.h)).toFixed(2)+'%</td></tr>'
          //+'<tr><td>Windspeed&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+(parseFloat(village.w)*0.07*0.37699111843077518861551720599354).toFixed(0)+' km/h</td></tr>'
          +'<tr><td>Wind speed&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+(parseFloat(village.w)*0.5).toFixed(0)+' km/h</td></tr>'
          +'<tr><td>Rainfall&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+((parseFloat("1"+village.r)-10)*3000/(50*50*3.14159)).toFixed(2)+' mm</td></tr>'
          //+'<tr><td>Air Pressure</td><td>'+(parseFloat(village.p)/101325).toFixed(2)+' atm</td></tr>'
          // +'<tr><td>Solar radiation&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+(parseFloat(village.s)/1024*5*.05*36/1000/(.03*.029)/2).toFixed(1)+' kwH/m<sup>2</sup></td></tr>'

        + '</table>'
      + '</div>'
    });
    all_infos.push(villageInfo);

    // Add the circle for this city to the map.
    var villageCircle = new google.maps.Circle({
      //villageColor here
      // strokeColor: 'green',
      strokeColor: villageColor,
      strokeOpacity: 0.8,
      strokeWeight: 0.5,
      //villageColor here
      // fillColor: 'green',
      fillColor: villageColor,
      fillOpacity: 0.35,
      map: map,
      center: {'lat': village.lt, 'lng': village.ln},
      position: {'lat': village.lt, 'lng': village.ln},
      radius: circleSize(village.r),
      data: village
      // raidius: 
      // radius: Math.sqrt(villages[village]*1000000) * 100
    });
    all_circles.push(villageCircle);

    // if (village == 'Dingok') {
    // villageCircle.addListener('click', function() {
    google.maps.event.addListener(all_circles[index], 'click', function(innerKey) {
      // console.log('derp');
      // console.log(i,e,h);
      // console.log(all_infos, this)
      return function() {
        all_infos[innerKey].open(map, all_circles[innerKey]);
      }
      // all_infos[all_infos.length-1].open(map, this);
    }(index));
    // }

    index++;
    
  }
  // Create the DIV to hold the control and call the CenterControl()
        // constructor passing in this DIV.
  // var downloadDiv = document.createElement('div');
  // var downloadControl = new createControl(downloadDiv, map, 'download', 'Download Data');
  // downloadDiv.index = 1;
 //  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(downloadDiv);

  var legendDiv = document.createElement('div');
  var legend = new createControl(legendDiv, map, 'legend', '');
  legendDiv.index = 1;
  
  //activate legend here
  //map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legendDiv);

  var paramsDiv = document.createElement('div');
  var paramsControl = new createControl(paramsDiv, map, 'params', '24 hours');
  paramsDiv.index = 1;
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(paramsDiv);

  var measurementDiv = document.createElement('div');
  var measureControl = new createControl(measurementDiv, map, 'measurement', 'Rainfall');
  measurementDiv.index = 1;
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(measurementDiv);

  // $('#display-param').change(function() {

  // var detailsDiv = document.createElement('div');
  // var detailControl = new createControl(detailsDiv, map, 'details', '');
  // detailsDiv.index = 1;
  // map.controls[google.maps.ControlPosition.RIGHT_CENTER].push(detailsDiv);

  // map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(document.getElementById('legend'));
}

setTimeout(function() {

  $('#select-measurement').change(function() {
    // console.log('changed');
    for (circle of all_circles) {
      var color = circleColor(0);
      circle.setOptions({fillColor: color, strokeColor: color});
    }
    // change the loaded thing
    // console.log($(this).val());
    var measurement = $(this).val();
    $('#div-legend').empty();

    var controlUI = document.getElementById('div-legend');

    for (var i=0; i < legend_lines[measurement].length; i++) {
      var line = legend_lines[measurement][i];
      var legendLine = new controlLine(controlUI, 
        'legendLine', {'text': line, 'color': all_colors[i]});
    }

  })

  $('#select-hours').change(function() {
    // console.log('changed hours');
    for (circle of all_circles) {
      var color = circleColor(0);
      circle.setOptions({fillColor: color, strokeColor: color});
    }
    hrs = document.getElementById("select-hours").value;
    if (hrs !== 0) {
    all_infos = [];   
        for (var v in villages) {

          var village = villages[v]
          // Parsing aw_data
          try {
            // making JSON readable
            village.aw_data = village.aw_data.split("u\'").join("\"")
            village.aw_data = village.aw_data.split("\'").join("\"")
            village.aw_data = village.aw_data.split("True").join("true")
            
            var aw_rain = JSON.parse(village.aw_data).rain + " mm"
          } catch(err) {
            aw_rain = "Unknown"
          }
          
          // Parsing sm_data
          try {
            // making JSON readable
            village.sm_data = village.sm_data.split("u\'").join("\"")
            village.sm_data = village.sm_data.split("\'").join("\"")
            village.sm_data = village.sm_data.split("True").join("true")
            
            var sm_rain = JSON.parse(village.sm_data).rain + " mm"
          } catch(err) {
            sm_rain = "Unknown"
          }
          
          // Parsing wrf_data
          try {
            // making JSON readable
            village.wrf_data = village.wrf_data.split("u\'").join("\"")
            village.wrf_data = village.wrf_data.split("\'").join("\"")
            village.wrf_data = village.wrf_data.split("True").join("true")
            
            var wrf_rain_max = JSON.parse(village.wrf_data).rmax + " mm"
            var wrf_rain_min = JSON.parse(village.wrf_data).rmin + " mm"
          } catch(err) {
            wrf_rain_max = "Unknown"
            wrf_rain_min = "Unknown"
          }
          

          var villageColor = circleColor(village.r);
          var villageInfo = new google.maps.InfoWindow({
            content: '<div id="content">'
            +'<h3>' + village.name + '&nbsp<a href="../../alert_dash/'+village.id+'">' 
            + '<img width="15px" padding-left="60px" src="../static/img/sms.jpg"></a></h3>'
            + '<i>Updated: '+village.ts+'</i>'
            // + '<a href="#">Download data</a>'
            + '<br /><br />'
              + '<table>'
                +'<tr><td>WRF (Max)&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+wrf_rain_max+'</td></tr>'
                +'<tr><td>WRF (Min)&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+wrf_rain_min+'</td></tr>'
                +'<tr><td>AW&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+aw_rain+'</td></tr>'
                +'<tr><td>Skymet&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>'+sm_rain+'</td></tr>'
                +'<tr><td>Internal&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>7 mm (80%)</td></tr>'
              + '</table>'
            + '</div>'
          });
          all_infos.push(villageInfo);
        }
    }
  })

}, 2000);