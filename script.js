// Create background particles
const background = document.getElementById('background');
const particleCount = 30;

for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.classList.add('particle');
    
    // Random size and position
    const size = Math.random() * 100 + 20;
    const posX = Math.random() * 100;
    const posY = Math.random() * 100;
    
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.left = `${posX}%`;
    particle.style.top = `${posY}%`;
    
    // Random animation duration
    particle.style.animationDuration = `${Math.random() * 30 + 15}s`;
    
    background.appendChild(particle);
}

// Create grid lines
for (let i = 0; i < 20; i++) {
    const horizontalLine = document.createElement('div');
    horizontalLine.classList.add('grid-line', 'grid-horizontal');
    horizontalLine.style.top = `${(i + 1) * 5}%`;
    background.appendChild(horizontalLine);
    
    const verticalLine = document.createElement('div');
    verticalLine.classList.add('grid-line', 'grid-vertical');
    verticalLine.style.left = `${(i + 1) * 5}%`;
    background.appendChild(verticalLine);
}

// Theme toggle
const themeToggle = document.getElementById('themeToggle');
const themeIcon = themeToggle.querySelector('i');

function setTheme(theme) {
    document.body.className = theme;
    localStorage.setItem('theme', theme);
    
    if (theme === 'light-theme') {
        themeIcon.className = 'fas fa-sun';
    } else {
        themeIcon.className = 'fas fa-moon';
    }
}

themeToggle.addEventListener('click', () => {
    if (document.body.classList.contains('light-theme')) {
        setTheme('');
    } else {
        setTheme('light-theme');
    }
});

// Check saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    setTheme(savedTheme);
}

// Splash screen animation
const splashScreen = document.getElementById('splash-screen');
setTimeout(() => {
    splashScreen.style.opacity = '0';
    splashScreen.style.pointerEvents = 'none';
    splashScreen.style.transform = 'scale(1.2)';
    
    setTimeout(() => {
        splashScreen.style.display = 'none';
    }, 1000);
}, 4000);