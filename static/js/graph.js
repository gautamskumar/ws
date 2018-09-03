/********************************************************************/
/*** initial values *************************************************/
/********************************************************************/

var N = 16;
var base = Array.apply(null, {length: N}).map(Number.call, Number);
// var base_half = Array.apply(null, {length: N}).map(Number.call+0.5, Number);
// var base_half = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5];
var ones = repeated_array(N, 1);
var zeros = repeated_array(N, 0);
var years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030];


var HEIGHT = 250;
var WIDTH = 500;
var inputs = [[0,5]];
var inputs_supply = [[0,5]];
var init = {'w': 100.536, 'm': 27.760, 'p': 5.986, 'r': 27.760, 'b': 26.159, 
    'waterdemand': 132, 'rainfall_t': 0.31, 'rainfall': 446, 'err': 20};
var percent = {
    'f': {'w': 0.93,'m': 0.555,'p': 1.0,'r': 1.0,'b': 0.4}, 
    'r': {'w': 0.06,'m': 0.44,'p': 0.0,'r': 0.0,'b': 0.6975}, 
    'd': {'w': 0.0,'m': 0.005,'p': 0.0,'r': 0.0,'b': 0.0025}
}
var eto = {'w': 0.5, 'm': 0.6, 'p': 0.6, 'r': 0.5, 'b': 0.5};
// var hectacres = {'w': }
var marketprice = {'p': 12, 'b': 12, 'w': 15, 'm': 50, 'r': 20}
// var water_demand = {}
var productivity = {'p': 2170, 'b': 930, 'w': 3140, 'm': 1850, 'r': 1152}

var crop_letters = ['w', 'm', 'p', 'r', 'b']
var annual_inflation_rate = 0.08;
var drinking_numbers = {
    'consumption': repeated_array(N, 60),
    'growth': repeated_array(N, 3.5)
}

/********************************************************************/
/*** helper/calc functions ******************************************/
/********************************************************************/

function repeated_array(n, v) {
    return Array.apply(null, Array(n)).map(Number.prototype.valueOf,v);
}

function exp_mult(N, e, init) {
    var tmp = [init];
    for (var i=1; i<=N; i++) {
        tmp.push(tmp[i-1]*e)
    }
    return tmp
}

function calc_drip(pd, yr) {
    return 132*Math.pow(1.0075,yr)*((1-pd/100)+pd/100*.6)+12*Math.pow(1.035,yr)/1000000;
}

function calc_supply(yr) {
    return 216*Math.pow(0.99,yr);
}

function calc_supply_rf(r) {
    return 215 * r / .446 / Math.pow(10,3);
}

function calc_supply_wrainfall(rfs) {
    var ret = []
    for (var r of rfs) {
        ret.push(calc_supply_rf(r));
    }
    return ret;
}


function calc_drinking(consumption, growth, year) {
    // console.log('c', consumption, growth, year, consumption * 365 / 1000 * 1089000 * Math.pow((1 + growth / 100),year));
    return consumption * 365 / 1000 * 1089000 * Math.pow((1 + growth / 100),year) / Math.pow(10, 6);
}

function calc_gdp(ind, agr, lstk) {
    return 4.45*ind+0.48*(agr+lstk);
}

function calc_gdp_bars(bars) {
    var ret = [];
    for (var i=0; i < bars.length; i++) {
        ret.push(calc_gdp(bars[i].Industry, bars[i].Agriculture, bars[i].Livestock));
    }
    // console.log(ret);
    return ret;
}



/********************************************************************/
/*** array building functions ***************************************/
/********************************************************************/


function calc_ecoutput(data_crops, data_rainfall, data_irrigation) {

    // [market price for wheat] * (1 + .08)^year * ( [hectares of wheat that's flood] * [yield for wheat when flooded] + [hectares of wheat that's rain-fed] * [avg yield for wheat] * [winter rainfall / 500 mm] + [hectares of wheat that's drip] * [avg yield of wheat] 

    var ret = [];
    for (var year=0; year<data_crops.length; year++) {
        var val = 0;
        for (c of crop_letters) {
            val += marketprice[c] * Math.pow((1+ annual_inflation_rate),year) * (
                data_crops[year][c] * data_irrigation[year]['f'][c] * productivity[c] + 
                data_crops[year][c] * data_irrigation[year]['r'][c] * productivity[c] * (data_rainfall[year] / 1000 * 0.10 / eto[c]) +
                data_crops[year][c] * data_irrigation[year]['d'][c] * productivity[c])
        }
        // console.log(data_rainfall[year], eto[c], data_rainfall[year] / 1000 * 0.10 / eto[c]);
        ret.push(val * 3 / Math.pow(10,6));
    }
    // console.log('ecoutput', ret);
    return ret;
}

function build_crops (N) {
    var ret = [];
    for (var i=0; i<N; i++) {
        var tmp = {'Year': i};
        for (var c of ['w', 'm', 'p', 'r', 'b']) {
            tmp[c] = init[c];
        }
        ret.push(tmp)
    }
    // console.log(ret);
    return ret;
}

function calc_ag_demand(year, data_crops, data_irrigation) {

    var meters = {'w': 0.7, 'm': 0.84, 'p': 0.84, 'r': 0.7, 'b': 0.7};

    var AG_ANNUAL_GROWTH = 0.01;
    // var rainfall_t = 0.31;
    // var init_waterdemand = 438;
    // var init.waterdemand = 132;
    // var crops = ['w', 'm', 'p', 'r', 'b'];

    var tmp = init.waterdemand * Math.pow((1 + AG_ANNUAL_GROWTH), year);
    // console.log('tmpbefore', tmp);
    if (year == 0) {
        return tmp;
    }
    else {
        for (var c of crop_letters) {
            tmp += (data_crops[year][c]-data_crops[year-1][c]) * (
                data_irrigation[year]['f'][c] * meters[c] + 
                data_irrigation[year]['r'][c] * init.rainfall_t + 
                data_irrigation[year]['d'][c] * eto[c]);
            // console.log(c, data_crops[year][c], data_crops[year-1][c]);
        }
        // console.log('tmpafter', tmp);
        return tmp;
    }
    // console.log(init.waterdemand, 1+AG_Atmp);
    // console.log('before', tmp);
    

}

function base_bars(N) {
    // var ret = [{'Year': 0, 'Drinking': 12, 'Livestock': 3.5, 'Agriculture': 132, 'Industry': 1}];
    var ret = [{
        'Year': 0, 
        // 'Drinking': 12,
        'Drinking': calc_drinking(drinking_numbers.consumption[0], drinking_numbers.growth[0], 0), 
        'Livestock': 3.5, 
        'Agriculture': calc_ag_demand(0, data_crops, data_irrigation), 
        'Industry': 1,
        'Error': init.err
    }];
    for (var i=1; i<N; i++) {
        ret.push({
            'Year': i, 
            // 'Drinking': ret[i-1].Drinking*1.035,
            'Drinking': calc_drinking(drinking_numbers.consumption[i], drinking_numbers.growth[i], i), 
            'Livestock': ret[i-1].Livestock*1.0075, 
            // 'Agriculture': ret[i-1].Agriculture*1.01,
            'Agriculture': calc_ag_demand(i, data_crops, data_irrigation), 
            'Industry': ret[i-1].Industry*1.015,
            'Error': init.err
        });
    }
    // console.log(ret);
    return ret;
}

function build_irrigation(N) {
    var ret = [];
    for (var i=0; i<N; i++) {
        // var tmp = percent.slice();
        var tmp = jQuery.extend(true, {}, percent);
        ret.push(tmp);
    }
    return ret;
}

/* build data*/
var data_irrigation = build_irrigation(N);
var data_crops = build_crops(N);

var data_rainfall = repeated_array(N, 446);
var data_supply = [
    { label: '', 
        // x: years,
        x: base,
        // x: base_half,
        // y: base
        // y: base.map(function (x) {return calc_supply(x)})
        y: calc_supply_wrainfall(data_rainfall)
        // y: ones
    }
];
// console.log(data_supply)

var data_bars = base_bars(16);
// data_bars.push(data_supply);

var data = [ 
    { label: '', 
        x: base,
        // y: [12, 31, 50, 26, 72, 35, 49, 81, 43, 32, 57, 63, 26, 61, 70, 52]
        // y: calc_gdp_bars(data_bars)
        y: calc_ecoutput(data_crops, data_rainfall, data_irrigation)
        // y: ones
    }, 
];




/********************************************************************/
/*** chart plotting functions ***************************************/
/********************************************************************/


// console.log(data, data_bars, data_supply);

var xy_chart = d3_xy_chart()
    .width(WIDTH)
    .height(HEIGHT)
    .xlabel("Time (years)")
    .ylabel("Economic output") ;
var svg = d3.select("#graph-demand").append("svg")
    .datum(data)
    .call(xy_chart) ;


var xy_bars = d3_xy_bars()
    .width(WIDTH)
    .height(HEIGHT)
    .xlabel("Time (years)")
    .ylabel("Water supply (mcm3)") ;
var svg_bars = d3.select("#graph-supply").append("svg")
    .datum({'bars': data_bars, 'lines': data_supply})
    .call(xy_bars) ;

function bar_click(d, i) {
    // console.log(d, i);
    // get the year
    var selected_year = i;
    sessionStorage.year_curr = i;
    // load information for the year
    $('#box-year').val(2015+i);
    populate_info(selected_year);
    // if supply < demand
    // if (data[0].x[selected_year] )
    // console.log(data_supply[0].y[selected_year], (d.Drinking+d.Livestock+d.Agriculture+d.Industry))
    var data_year = data_bars[selected_year]
    if (data_supply[0].y[selected_year] < d.total) {

        // display the agriculture details
        $('#details-agriculture-div').show();
        $('#update-agriculture').prop('disabled', false);

        // randomly decrease the values in a cascading manner
        // data_crops[selected_year]['w'] *= 0.80;
        // data_crops[selected_year]['m'] *= 0.70;
        // data_crops[selected_year]['p'] *= 0.60;
        // data_crops[selected_year]['r'] *= 0.50;
        // data_crops[selected_year]['b'] *= 0.40;
        var curr_w = slider_wheat.slider('getValue');
        var curr_m = slider_mustard.slider('getValue');
        var curr_p = slider_paddy.slider('getValue');
        var curr_r = slider_raya.slider('getValue');
        var curr_b = slider_bajra.slider('getValue');

        // console.log(data_crops[selected_year]);

        slider_wheat.slider('setValue', curr_w * 0.8);
        slider_mustard.slider('setValue', curr_m * 0.7);
        slider_paddy.slider('setValue', curr_p * 0.6);
        slider_raya.slider('setValue', curr_r * 0.5);
        slider_bajra.slider('setValue', curr_b * 0.4);

        // $('#update-agriculture').click();
    }
}

function d3_xy_chart() {
    
    function chart(selection) {
        selection.each(function(datasets) {

            // console.log(datasets);

            var margin = {top: 20, right: 80, bottom: 30, left: 50}, 
                innerwidth = width - margin.left - margin.right,
                innerheight = height - margin.top - margin.bottom ;
            
            var x_scale = d3.scale.linear()
                .range([0, innerwidth])
                .domain([ d3.min(datasets, function(d) { return d3.min(d.x); }), 
                          d3.max(datasets, function(d) { return d3.max(d.x); }) ]) ;
            
            var y_scale = d3.scale.linear()
                .range([innerheight, 0])
                .domain([ d3.min(datasets, function(d) { return d3.min(d.y)-15; }),
                          d3.max(datasets, function(d) { return d3.max(d.y)+15; }) ]) ;

            var color_scale = d3.scale.category10()
                .domain(d3.range(datasets.length)) ;

            var x_axis = d3.svg.axis()
                .scale(x_scale)
                .orient("bottom")
                // .tickValues(d3.range(0, 16, 1));
                .ticks(16) ;



            var y_axis = d3.svg.axis()
                .scale(y_scale)
                .orient("left") ;

            var x_grid = d3.svg.axis()
                .scale(x_scale)
                .orient("bottom")
                .ticks(16)
                .tickSize(-innerheight, 1)
                .tickFormat("") ;

            var y_grid = d3.svg.axis()
                .scale(y_scale)
                .orient("left") 
                .tickSize(-innerwidth)
                .tickFormat("") ;

            var draw_line = d3.svg.line()
                .interpolate("basis")
                .x(function(d) { return x_scale(d[0]); })
                .y(function(d) { return y_scale(d[1]); }) ;

            var svg = d3.select(this)
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")") ;
            
            svg.append("g")
                .attr("class", "x grid")
                .attr("transform", "translate(0," + innerheight + ")")
                .call(x_grid) ;

            svg.append("g")
                .attr("class", "y grid")
                .call(y_grid) ;

            svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + innerheight + ")") 
                .call(x_axis)
                .append("text")
                .attr("dy", "-.71em")
                .attr("x", innerwidth)
                .style("text-anchor", "end")
                .text(xlabel) ;

            // x_axis.tickValues(d3.range(0, 16, 1));
            
            svg.append("g")
                .attr("class", "y axis")
                .call(y_axis)
                .append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", 6)
                .attr("dy", "0.71em")
                .style("text-anchor", "end")
                .text(ylabel) ;

            var data_lines = svg.selectAll(".d3_xy_chart_line")
                .data(datasets.map(function(d) {return d3.zip(d.x, d.y);}))
                .enter().append("g")
                .attr("class", "d3_xy_chart_line") ;
            
            data_lines.append("path")
                .attr("class", "line")
                .attr("d", function(d) {return draw_line(d); })
                .attr("stroke", function(_, i) {return color_scale(i);}) ;
            
            data_lines.append("text")
                .datum(function(d, i) { return {name: datasets[i].label, final: d[d.length-1]}; }) 
                .attr("transform", function(d) { 
                    return ( "translate(" + x_scale(d.final[0]) + "," + 
                             y_scale(d.final[1]) + ")" ) ; })
                .attr("x", 3)
                .attr("dy", ".35em")
                .attr("fill", function(_, i) { return color_scale(i); })
                .text(function(d) { return d.name; }) ;

        }) ;
    }

    chart.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return chart;
    };

    chart.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return chart;
    };

    chart.xlabel = function(value) {
        if(!arguments.length) return xlabel ;
        xlabel = value ;
        return chart ;
    } ;

    chart.ylabel = function(value) {
        if(!arguments.length) return ylabel ;
        ylabel = value ;
        return chart ;
    } ;

    return chart;
}


function d3_xy_bars() {
    
    function chart(selection) {
        selection.each(function(datasets) {
            console.log(datasets);

            var bars_data = datasets.bars,
                lines_data = datasets.lines;

            var margin = {top: 20, right: 80, bottom: 30, left: 50},
                innerwidth = width - margin.left - margin.right,
                innerheight = height - margin.top - margin.bottom;

            var x = d3.scale.ordinal()
                .rangeRoundBands([0, innerwidth], .1);

            var y = d3.scale.linear()
                .rangeRound([innerheight, 0]);

            var color = d3.scale.category10()
                .domain(d3.range(datasets.length))
            // d3.scale.ordinal()
                // .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);
                // .range(['#99CCFF', '#9999FF', '#CC99FF', '#FF99FF', '#FF99CC', '#FF9999', '#FFCC99'])
                // .range(['#97AAC4', '#9A97C4', '#B197C4', '#C497C0', '#C497AA'])

            var xAxis = d3.svg.axis()
                .scale(x)
                .orient("bottom");

            var yAxis = d3.svg.axis()
                .scale(y)
                .orient("left")
                .tickFormat(d3.format(".2s"));

            var x_grid = d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .tickSize(-innerheight)
                .tickFormat("") ;

            var y_grid = d3.svg.axis()
                .scale(y)
                .orient("left") 
                .tickSize(-innerwidth)
                .tickFormat("") ;

            var draw_line = d3.svg.line()
                .interpolate("basis")
                .x(function(d) { return x(d[0]); })
                .y(function(d) { return y(d[1]); }) ;

            color.domain(d3.keys(bars_data[0]).filter(function(key) { return ['Year', 'ages', 'total'].indexOf(key) < 0; }));

            bars_data.forEach(function(d) {
                var y0 = 0;
                d.ages = color.domain().map(function(name) { return {name: name, y0: y0, y1: y0 += +d[name]}; });
                d.total = d.ages[d.ages.length - 1].y1;
            });

            x.domain(bars_data.map(function(d) { return d.Year; }));
            y.domain([0, d3.max(lines_data, function(d) { return d3.max(d.y)+70;})])

            //

            var svg = d3.select(this)
                .attr("width", width)
                .attr("height", height)
              .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            svg.append("g")
                .attr("class", "x grid")
                .attr("transform", "translate(0," + innerheight + ")")
                .call(x_grid) ;

            svg.append("g")
                .attr("class", "y grid")
                .call(y_grid) ;

            // svg.on('click', bar_click);
              

              var state = svg.selectAll(".state")
                  .data(bars_data)
                .enter().append("g")
                  .attr("class", "g")
                  .attr("transform", function(d) { return "translate(" + x(d.Year) + ",0)"; })
                  .on('click', bar_click);

              state.selectAll("rect")
                  .data(function(d) { return d.ages; })
                .enter().append("rect")
                  .attr("width", x.rangeBand())
                  .attr("y", function(d) { return y(d.y1); })
                  .attr("height", function(d) { return y(d.y0) - y(d.y1); })
                  .style("fill", function(d) { return color(d.name); })
                  ;

              var legend = svg.selectAll(".legend")
                  .data(color.domain().slice().reverse())
                .enter().append("g")
                  .attr("class", "legend")
                  .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

                  svg.append("g")
                  .attr("class", "x axis")
                  .attr("transform", "translate(0," + innerheight + ")")
                  .call(xAxis)
                  .append("text")
                    .attr("dy", "-.71em")
                    .attr("x", innerwidth)
                    .style("text-anchor", "end")
                    .text(xlabel) ;

              svg.append("g")
                  .attr("class", "y axis")
                  .call(yAxis)
                .append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 6)
                  .attr("dy", ".71em")
                  .style("text-anchor", "end")
                  .text(ylabel);

              legend.append("rect")
                  .attr("x", innerwidth - 18)
                  .attr("width", 18)
                  .attr("height", 18)
                  .style("fill", color);

              legend.append("text")
                  .attr("x", innerwidth - 24)
                  .attr("y", 9)
                  .attr("dy", ".35em")
                  .style("text-anchor", "end")
                  .text(function(d) { return d; });

            // get lines data

            var data_lines = svg.selectAll(".d3_xy_chart_line")
                .data(lines_data.map(function(d) {return d3.zip(d.x, d.y);}))
                .enter().append("g")
                .attr("class", "d3_xy_chart_line") ;
            
            data_lines.append("path")
                .attr("class", "line")
                .attr("d", function(d) {return draw_line(d); })
                .attr("stroke", function(_, i) {return color(i);}) ;
            
            data_lines.append("text")
                .datum(function(d, i) { return {name: lines_data[i].label, final: d[d.length-1]}; }) 
                .attr("transform", function(d) { 
                    return ( "translate(" + x(d.final[0]) + "," + 
                             y(d.final[1]) + ")" ) ; })
                .attr("x", 3)
                .attr("dy", ".35em")
                .attr("fill", function(_, i) { return color(i); })
                .text(function(d) { return d.name; }) ;

        }) ;
    }

    chart.width = function(value) {
        if (!arguments.length) return width;
        width = value;
        return chart;
    };

    chart.height = function(value) {
        if (!arguments.length) return height;
        height = value;
        return chart;
    };

    chart.xlabel = function(value) {
        if(!arguments.length) return xlabel ;
        xlabel = value ;
        return chart ;
    } ;

    chart.ylabel = function(value) {
        if(!arguments.length) return ylabel ;
        ylabel = value ;
        return chart ;
    } ;

    return chart;
}
