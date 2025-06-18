const svg = d3.select("#map");
const tooltip = d3.select("#tooltip");

const colorScale = d3.scaleThreshold()
  .domain([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
  .range([
    "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1",
    "#6baed6", "#4292c6", "#2171b5", "#084594", "#08306b"
  ]);
const dealColorScale = d3.scaleThreshold()
  .domain([1, 2, 3, 5, 8, 12, 20])
  .range([
    "#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8",
    "#807dba", "#6a51a3", "#4a1486", "#2c004a"
  ]);

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

let currentView = "aggregate";
let states, metrics;

const projection = d3.geoAlbersUsa().scale(1000).translate([480, 300]);
const path = d3.geoPath().projection(projection);

Promise.all([
  d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"),
  d3.json("state_metrics.json")
]).then(([us, loadedMetrics]) => {
  metrics = loadedMetrics;
  states = topojson.feature(us, us.objects.states).features;

  renderMap(currentView);
  renderLegend();

  document.querySelectorAll("#view-toggle button").forEach(button => {
    button.addEventListener("click", () => {
      currentView = button.dataset.view;
      renderMap(currentView);
    });
  });
});

function renderMap(view) {
  svg.selectAll("g").remove();

  svg.append("g")
    .selectAll("path")
    .data(states)
    .join("path")
    .attr("d", path)
    .attr("fill", d => {
      const fips = d.id.toString().padStart(2, "0");
      const code = fipsToState[fips];
      const m = metrics[code];
      if (!m) return "#eee";

      if (view === "deals") {
        const dealCount = (m.deal_list || []).length;
        return dealCount ? dealColorScale(dealCount) : "#eee";
      }

      const data = view === "district" ? m.district
                  : view === "charter" ? m.charter
                  : m;

      return data?.score != null ? colorScale(data.score) : "#eee";
    })
    .attr("stroke", "#000")
    .attr("stroke-width", 1)
    .on("mouseover", (event, d) => {
    const fips = d.id.toString().padStart(2, "0");
    const code = fipsToState[fips];
    const m = metrics[code];
    if (!m) return;

    if (view === "deals") {
      const deals = m.deal_list || [];
      tooltip.style("display", "block")
        .html(`
          <strong>${code}</strong><br>
          <strong>Closed Deals: ${deals.length}</strong><br>
          ${deals.map(deal => `
            <div style="margin-top: 4px">
              <em>${deal.deal_name}</em><br>
              Amount: $${deal.amount.toLocaleString()}<br>
              Contacts: ${deal.contacts}
            </div>
          `).join("<hr style='margin:4px 0;'>")}
        `)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 40) + "px");
      return;
    }

    const data = view === "district" ? m.district
                : view === "charter" ? m.charter
                : m;

    const safeRate = (num, denom) => denom ? (num / denom * 100).toFixed(1) + "%" : "N/A";

    tooltip.style("display", "block")
      .html(`
        <strong>${code}</strong><br>
        # of Calls: ${data?.calls ?? 0}<br>
        Connect Rate: ${safeRate(data?.connects, data?.calls)}<br>
        Book Rate: ${safeRate(data?.discos, data?.connects)}<br>
        Close Rate: ${safeRate(data?.customers, data?.discos)}<br>
        Score: ${((data?.score ?? 0) * 100).toFixed(1)}%
      `)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 40) + "px");
  })
  renderLegend();
}

function renderLegend() {
  const legendContainer = d3.select("#legend");
  legendContainer.html(""); // clear old

  const isDeals = currentView === "deals";
  const thresholds = isDeals ? dealColorScale.domain() : colorScale.domain();
  const colors = isDeals ? dealColorScale.range() : colorScale.range();

  const steps = isDeals ? [0, ...thresholds, Infinity] : [0, ...thresholds, 1];
  for (let i = 0; i < steps.length - 1; i++) {
    const rangeLabel = isDeals
      ? `${steps[i]}–${steps[i + 1] === Infinity ? "+" : steps[i + 1]}`
      : `${Math.round(steps[i] * 100)}–${Math.round(steps[i + 1] * 100)}%`;

    legendContainer.append("div")
      .attr("class", "legend-item")
      .html(`
        <div class="legend-color" style="background:${colors[i]}"></div>
        <div>${rangeLabel}</div>
      `);
  }
}
