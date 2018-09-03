var jsons = new Array();
var arr = document.getElementsByClassName('data');
for(var i=0; i< arr.length; i++){
  jsons.push(JSON.parse(arr[i].innerHTML));
}

var csvs = new Array();
csvs.push(['last_update', 'temp', 'humidity', 'wind_speed', 'rainfall', 'solar_radiation', 'signal']);
for (var j in jsons) {
	var json = jsons[j];
	csvs.push([json.ts, (parseFloat(json.t1)).toFixed(1), (parseFloat(json.t2)).toFixed(2), (parseFloat(json.h)).toFixed(2), (parseFloat(json.w)*0.07*0.37699111843077518861551720599354).toFixed(0), ((parseFloat("1"+json.r)-10)*3000/(50*50*3.14159)).toFixed(2), (parseFloat(json.s)/1024*5*.05*36/1000/(.03*.029)/2).toFixed(1), (parseFloat(json.sg)).toFixed(1)]);
}

var csvContent = "data:text/csv;charset=utf-8,";
csvs.forEach(function(infoArray, index){

   dataString = infoArray.join(",");
   csvContent += index < csvs.length ? dataString+ "\n" : dataString;

}); 

var encodedUri = encodeURI(csvContent);
var link = document.createElement("a");
link.setAttribute("href", encodedUri);
link.setAttribute("download", "ws.csv");

link.click(); // This will download the data file named "my_data.csv".
window.location="http://www.yobi.tech/dashboard";