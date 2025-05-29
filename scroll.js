// Scroll to section
const OFFSET = 100;
const navItems = document.querySelectorAll('#mode-nav li[data-target]');
const wrappers = document.querySelectorAll('.plot-wrapper');

navItems.forEach(li => {
li.addEventListener('click', e => {
    e.preventDefault();
    const id = li.getAttribute('data-target');
    const target = document.getElementById(id);
    const y = target.getBoundingClientRect().top + window.scrollY - OFFSET;
    window.scrollTo({ top: y, behavior: 'smooth' });
});
});

const observer = new IntersectionObserver(
entries => {
    entries.forEach(entry => {
    if (entry.isIntersecting) {
        const containerId = entry.target.getAttribute('data-container');
        navItems.forEach(li => {
        const a = li.querySelector('a');
        a.classList.toggle('active', li.getAttribute('data-target') === containerId);
        });
    }
    });
},
{
    rootMargin: `-${OFFSET + 1}px 0px -50% 0px`,
    threshold: 0.20
}
);

wrappers.forEach(w => observer.observe(w));