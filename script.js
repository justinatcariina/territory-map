const svg = d3.select("#map");
const tooltip = d3.select("#tooltip");

const colorScale = d3.scaleThreshold()
  .domain([1, 5, 10])
  .range(["#ccc", "yellow", "orange", "red"]);

const fipsToState = {
  "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
  "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
  "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
  "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
  "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
  "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
  "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
  "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
  "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
  "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"
};

Promise.all([
  d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"),
  d3.json("state_metrics.json")
]).then(([us, metrics]) => {
  const states = topojson.feature(us, us.objects.states).features;

  const projection = d3.geoAlbersUsa().scale(1000).translate([480, 300]);
  const path = d3.geoPath().projection(projection);

  console.log("Loaded metrics:", metrics);

  svg.append("g")
    .selectAll("path")
    .data(states)
    .join("path")
    .attr("d", path)
    .attr("fill", d => {
      const fips = d.id.toString().padStart(2, "0");
      const stateCode = fipsToState[fips];
      const m = metrics[stateCode];
      console.log("FIPS:", fips, "→", stateCode, "| Metric:", m);
      return m ? colorScale(m.score) : "#eee";
    })
    .attr("stroke", "#fff")
    .on("mouseover", function(event, d) {
      const fips = d.id.toString().padStart(2, "0");
      const code = fipsToState[fips];
      const m = metrics[code];
      if (!m) return;

      tooltip.style("display", "block")
        .html(`<strong>${code}</strong><br>Calls: ${m.calls}<br>Connects: ${m.connects}<br>Discos: ${m.discos}<br>Customers: ${m.customers}<br>Score: ${m.score}`)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 40) + "px");
    })
    .on("mouseout", () => tooltip.style("display", "none"));
});
