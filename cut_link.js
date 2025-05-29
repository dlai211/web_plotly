// Create cut-links
const sites = ["c1", "e12", "e10"];
const instruments = ["SRS", "LPM", "SPMF", "SONIC", "WBGEONOR"];
const siteInstruments = {
c1: ["SRS", "LPM", "SPMF", "SONIC", "WBGEONOR"],
e12: ["SRS", "LPM", "SPMF", "SONIC", "WBGEONOR"],
e10: ["LPM"]
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
