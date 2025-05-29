/*
Step 1. Click on site, all instruments <a> disabled. Then, need to click on Instrument to navigate.
Step 1. Click on instrument, navigate to [same]site/instrument.
*/


let currentSite = null;
let currentInstrument = null;

const siteLinks = document.querySelectorAll('[data-site]');
const instrLinks = document.querySelectorAll('[data-instrument]');

// --- On page load: parse URL and set active states ---
(function initializeFromPath() {
  const parts = window.location.pathname.split('/');
  if (parts.length >= 3) {
    currentSite = parts[parts.length - 2];
    currentInstrument = parts[parts.length - 1].replace('.html', '');
    updateNavState();
  }
})();

function updateNavState() {
  siteLinks.forEach(link => {
    link.classList.toggle('active', link.dataset.site === currentSite);
  });

  instrLinks.forEach(link => {
    const instr = link.dataset.instrument;
    const isActive = instr === currentInstrument;
    const isValid = siteInstruments[currentSite]?.includes(instr);
    link.classList.toggle('active', isActive);
    link.classList.toggle('disabled', !isValid);

    link.parentElement.style.display = isValid ? 'list-item' : 'none';
  });
}

// --- On user click: update state and navigate ---
siteLinks.forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const newSite = link.dataset.site;
    if (newSite !== currentSite) {
      currentSite = newSite;
      currentInstrument = null;
      updateNavState();
    }
  });
});

instrLinks.forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const selectedInstrument = link.dataset.instrument;
    if (currentSite && siteInstruments[currentSite].includes(selectedInstrument)) {
      currentInstrument = selectedInstrument;
      updateNavState();
      window.location.href = `/plots/${currentSite}/${currentInstrument}.html`;
    }
  });
});
