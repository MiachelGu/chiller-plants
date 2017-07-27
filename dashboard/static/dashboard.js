// dashboard

// create a new time series plot
function plotNewTimeSeries(xlabel, ylabel, data, field, plotElementId) {
  var layout = {
    xaxis: {title: xlabel, showgrid: false},
    yaxis: {title: ylabel, showgrid: false},
    hovermode: "closest",
    showlegend: false,
  };

  var trace = {
    type: "scatter",
    mode: "lines+markers",
    line: {width: 1},
    x: data.map(function(i) { return new Date(i._id); }),
    y: data.map(function(i) { return i[field]; }),
  };

  Plotly.newPlot(plotElementId, [trace], layout);
}

// datetime..
Date.prototype.addDays = function(days) {
  var d = new Date(this.valueOf());
  d.setDate(d.getDate() + days);
  return d;
}

Date.prototype.addMonths = function(mo) {
  var d = new Date(this.valueOf());
  d.setMonth(d.getMonth() + mo);
  return d;
}

