
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const analyzeBtn = document.getElementById('analyze-btn');
const cityInput = document.getElementById('city-input');
const resultsSection = document.getElementById('results');
const loadingSection = document.getElementById('loading');
const errorSection = document.getElementById('error');

let selectedFile = null;

// Drag and Drop
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('active');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('active'));

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('active');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

function handleFiles(files) {
    if (files.length > 0) {
        selectedFile = files[0];
        dropZone.querySelector('p').textContent = `File selected: ${selectedFile.name}`;
    }
}

// API Interaction
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        alert("Please select or drag an ECG image first!");
        return;
    }

    const city = cityInput.value || "Kochi";
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('city', city);

    // Initial state
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');

    try {
        const response = await fetch('http://localhost:8000/analyze-ecg', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            updateUI(data.analysis);
        } else {
            showError(data.error || "Analysis failed");
        }
    } catch (err) {
        showError("Could not connect to the backend server.");
    } finally {
        loadingSection.classList.add('hidden');
    }
});

function updateUI(analysis) {
    resultsSection.classList.remove('hidden');

    // Core Stats
    document.getElementById('bpm-val').textContent = analysis.bpm;
    document.getElementById('status-val').textContent = analysis.status;

    // Secondary Info
    document.getElementById('stress-val').textContent = analysis.stress_level;
    document.getElementById('conf-val').textContent = analysis.confidence;

    // AQI Logic
    const aqiLvl = document.getElementById('aqi-level');
    aqiLvl.textContent = `AQI: ${analysis.aqi_value} (${analysis.aqi_level})`;
    aqiLvl.className = `aqi-level ${analysis.aqi_level}`;
    document.getElementById('aqi-msg').textContent = analysis.aqi_message;

    // Advisory
    document.getElementById('health-adv').textContent = analysis.health_advisory;

    // Hospital Section
    const hospSection = document.getElementById('hospital-section');
    const hospList = document.getElementById('hospital-list');
    hospList.innerHTML = '';

    if (analysis.nearest_hospitals && analysis.nearest_hospitals.length > 0) {
        hospSection.classList.remove('hidden');
        analysis.nearest_hospitals.forEach(h => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="h-name">${h.HospitalName}</span>
                <span class="h-info">Distance: <span class="h-dist">${h.Distance} km</span> | Contact: ${h.Phone}</span>
            `;
            hospList.appendChild(li);
        });
    } else {
        hospSection.classList.add('hidden');
    }
}

function showError(msg) {
    errorSection.classList.remove('hidden');
    document.getElementById('error-msg').textContent = msg;
}
