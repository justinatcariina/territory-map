const svg = d3.select("#map");
const tooltip = d3.select("#tooltip");

const colorScale = d3.scaleThreshold()
  .domain([1, 5, 10])
  .range(["#ccc", "yellow", "orange", "red"]);

Promise.all([
  d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"),
  d3.json("state_metrics.json")
]).then(([us, metrics]) => {
  const states = topojson.feature(us, us.objects.states);

  const projection = d3.geoAlbersUsa().scale(1000).translate([480, 300]);
  const path = d3.geoPath().projection(projection);

  svg.append("g")
    .selectAll("path")
    .data(states.features)
    .join("path")
    .attr("d", path)
    .attr("fill", d => {
      const stateCode = d.properties.code;
      const stateMetric = metrics[stateCode];
      return stateMetric ? colorScale(stateMetric.score) : "#eee";
    })
    .attr("stroke", "#fff")
    .on("mouseover", function (event, d) {
      const code = d.properties.code;
      const m = metrics[code];
      if (!m) return;
      tooltip.style("display", "block")
        .html(`<strong>${code}</strong><br>Calls: ${m.calls}<br>Connects: ${m.connects}<br>Discos: ${m.discos}<br>Customers: ${m.customers}<br>Score: ${m.score}`)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 40) + "px");
    })
    .on("mouseout", () => tooltip.style("display", "none"));
});
