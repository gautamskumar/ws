var jsons = new Array();
var arr = document.getElementsByClassName('data');
for(var i=0; i< arr.length; i++){
  jsons.push(JSON.parse(arr[i].innerHTML));
}

var villages = new Array();
for (var j in jsons) {
	json = jsons[j];
	villages.push(JSON.parse('{"ts":"'+json.ts+'","t1":"'+(parseFloat(json.t1)).toFixed(1)+'","t2":"'+(parseFloat(json.t2)).toFixed(1)+'","h":"'+(parseFloat(json.h)).toFixed(2)+'","tk":"'+json.w+'","w":"'+(parseFloat(json.w)*0.07*0.37699111843077518861551720599354).toFixed(0)+'","tp":"'+json.r+'","r":"'+((parseFloat("1"+json.r)-10)*3000/(50*50*3.14159)).toFixed(2)+'","s":"'+(parseFloat(json.s)/1024*5*.05*36/1000/(.03*.029)/2).toFixed(1)+'","p":"'+(parseFloat(json.p)/101325).toFixed(2)+'","sg":"'+(parseFloat(json.sg)).toFixed(0)+'","lt":"'+json.lt+'","ln":"'+json.ln+'"}'));
}