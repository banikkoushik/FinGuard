/* ============================= */
/*      DOM ELEMENTS             */
/* ============================= */
const aiOrbContainer = document.getElementById('ai-orb-container');
const chatPanel = document.getElementById('chat-panel');
const closeChatBtn = document.getElementById('close-chat');
const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');
const chatMessages = document.getElementById('chat-messages');
const loanCardsContainer = document.getElementById('loan-cards');

/* ============================= */
/*   RENDER LOAN CARDS DYNAMIC   */
/* ============================= */
async function renderLoanCards(category = 'all') {
    loanCardsContainer.innerHTML = '';
    const loanData = await fetchLoanRecommendations(category); // from api_utils.js
    loanData.forEach(loan => {
        const card = document.createElement('div');
        card.classList.add('loan-card');
        card.innerHTML = `
            <h3>${loan.type}</h3>
            <p>Vendor: ${loan.vendor}</p>
            <p>Interest: ${loan.interest}</p>
            <p>Tenure: ${loan.tenure}</p>
        `;
        card.addEventListener('click', async () => {
            addChatMessage(`Show details for ${loan.type}`, 'user');
            const aiResponse = await fetchAIPrediction(
                `Explain why ${loan.vendor} with ${loan.interest} for ${loan.tenure} is best for ${loan.type}`
            );
            addChatMessage(aiResponse, 'ai');
        });
        loanCardsContainer.appendChild(card);
    });
}

/* ============================= */
/*      CHAT FUNCTIONALITY       */
/* ============================= */
function toggleChat() {
    chatPanel.classList.toggle('hidden');
}

aiOrbContainer.addEventListener('click', toggleChat);
closeChatBtn.addEventListener('click', toggleChat);

function addChatMessage(message, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('chat-message', sender === 'user' ? 'user-message' : 'ai-message');
    msgDiv.innerText = message;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

sendBtn.addEventListener('click', async () => {
    const message = userInput.value.trim();
    if (!message) return;
    addChatMessage(message, 'user');
    userInput.value = '';

    // AI response
    const aiResponse = await fetchAIPrediction(message);
    addChatMessage(aiResponse, 'ai');
});

/* ============================= */
/*     DYNAMIC TRADING CHART     */
/* ============================= */
async function renderTradingChart() {
    const tradingData = await fetchTradingData(); // from api_utils.js
    const ctx = document.getElementById('trading-chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: tradingData.labels,
            datasets: [{
                label: 'Portfolio Value',
                data: tradingData.values,
                borderColor: '#00f0ff',
                backgroundColor: 'rgba(0, 255, 255, 0.2)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: '#00f0ff' } } },
            scales: {
                x: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(0, 255, 255, 0.1)' } },
                y: { ticks: { color: '#ffffff' }, grid: { color: 'rgba(0, 255, 255, 0.1)' } }
            }
        }
    });
}

/* ============================= */
/*      3D AI ORB ANIMATION       */
/* ============================= */
function initAIOrb3D() {
    const width = aiOrbContainer.clientWidth;
    const height = aiOrbContainer.clientHeight;

    // Three.js scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.z = 2;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    aiOrbContainer.appendChild(renderer.domElement);

    // Sphere geometry
    const geometry = new THREE.SphereGeometry(0.5, 32, 32);
    const material = new THREE.MeshStandardMaterial({
        color: 0x00ffff,
        emissive: 0x00aaff,
        metalness: 0.7,
        roughness: 0.2,
        transparent: true,
        opacity: 0.9
    });
    const orb = new THREE.Mesh(geometry, material);
    scene.add(orb);

    // Lighting
    const pointLight = new THREE.PointLight(0x00ffff, 1, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    const ambientLight = new THREE.AmbientLight(0x00ffff, 0.3);
    scene.add(ambientLight);

    // Orb floating variables
    let clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        const time = clock.getElapsedTime();

        // Rotate orb
        orb.rotation.x = time * 0.5;
        orb.rotation.y = time * 0.7;

        // Pulse scale
        const scale = 1 + 0.1 * Math.sin(time * 3);
        orb.scale.set(scale, scale, scale);

        // Floating motion (circular)
        const radius = 0.05; // small float radius
        orb.position.x = radius * Math.sin(time * 1.5);
        orb.position.y = radius * Math.cos(time * 1.2);

        renderer.render(scene, camera);
    }
    animate();

    // Handle resize
    window.addEventListener('resize', () => {
        const w = aiOrbContainer.clientWidth;
        const h = aiOrbContainer.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });
}

/* ============================= */
/*     INIT FUNCTIONS            */
/* ============================= */
async function init() {
    await renderLoanCards();
    await renderTradingChart();
    initAIOrb3D();
}

init();
