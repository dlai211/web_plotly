// Create cut-links
const sites = ["C1", "E12", "E10"];
const instruments = ["SRS", "LPM", "SPMF", "SONICWIND3D", "WBGEONOR"];
const siteInstruments = {
C1: ["SRS", "LPM", "SPMF", "SONICWIND3D"],
E12: ["SRS", "LPM", "SPMF", "SONICWIND3D", "WBGEONOR"],
E10: ["LPM"]
};

const cutLinks = document.getElementById("cut-links");

// Create site list
cutLinks.appendChild(document.createElement("li")).textContent = "Site:";
sites.forEach(site => {
const li = document.createElement("li");
const a = document.createElement("a");
a.href = "#";
a.textContent = site.toUpperCase();
a.dataset.site = site;
li.appendChild(a);
cutLinks.appendChild(li);
});

// Divider
const divider = document.createElement("li");
divider.className = "nav-divider";
cutLinks.appendChild(divider);

// Create instrument list
cutLinks.appendChild(document.createElement("li")).textContent = "Instrument:";
instruments.forEach(instr => {
const li = document.createElement("li");
const a = document.createElement("a");
a.href = "#";
a.textContent = instr;
a.dataset.instrument = instr;
li.appendChild(a);
cutLinks.appendChild(li);
});

// Divider
const dlDivider = document.createElement("li");
dlDivider.className = "nav-divider";
cutLinks.appendChild(dlDivider);

// Data Level Label
const dlLabel = document.createElement("li");
dlLabel.textContent = "Data Level:";
cutLinks.appendChild(dlLabel);

const dlItem = document.createElement("li");
const a1 = document.createElement("a");
a1.href = "#";
a1.textContent = "a1";
a1.classList.add("active");
a1.setAttribute("onclick", "return false;");
dlItem.appendChild(a1);
cutLinks.appendChild(dlItem);
