var csvContent = "data:text/csv;charset=utf-8,";
csvs.forEach(function(infoArray, index){

   dataString = infoArray.join(",");
   csvContent += index < csvs.length ? dataString+ "\n" : dataString;

}); 

console.log(csvContent);

// var encodedUri = encodeURI(csvContent);
// var link = document.createElement("a");
// link.setAttribute("href", encodedUri);
// link.setAttribute("download", "sensors.csv");

// link.click(); // This will download the data file named "my_data.csv".
// window.location="http://www.yobi.tech/id_dash";