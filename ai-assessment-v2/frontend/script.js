const API_URL = 'http://localhost:8000';

const form = document.getElementById('generateForm');
const submitBtn = document.getElementById('submitBtn');
const loadingCard = document.getElementById('loadingCard');
const resultsSection = document.getElementById('resultsSection');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const grade = parseInt(document.getElementById('grade').value);
    const topic = document.getElementById('topic').value.trim();
    const userId = document.getElementById('userId').value.trim() || null;
    
    await runPipeline(grade, topic, userId);
});

async function runPipeline(grade, topic, userId) {
    submitBtn.disabled = true;
    loadingCard.style.display = 'block';
    resultsSection.style.display = 'none';
    
    try {
        let url = `${API_URL}/generate`;
        if (userId) url += `?user_id=${encodeURIComponent(userId)}`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grade, topic })
        });
        
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        
        const artifact = await response.json();
        displayResults(artifact);
        
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        loadingCard.style.display = 'none';
    }
}

function displayResults(artifact) {
    resultsSection.style.display = 'block';
    
    // Summary
    const summaryGrid = document.getElementById('summaryGrid');
    summaryGrid.innerHTML = `
        <div class="summary-item">
            <div class="label">Status</div>
            <div class="value ${artifact.final.status}">${artifact.final.status.toUpperCase()}</div>
        </div>
        <div class="summary-item">
            <div class="label">Attempts</div>
            <div class="value">${artifact.attempts.length}</div>
        </div>
        <div class="summary-item">
            <div class="label">Duration</div>
            <div class="value">${artifact.timestamps.duration_seconds?.toFixed(1) || '?'}s</div>
        </div>
        <div class="summary-item">
            <div class="label">Run ID</div>
            <div class="value" style="font-size: 0.75rem;">${artifact.run_id.slice(0, 8)}...</div>
        </div>
    `;
    
    // Timeline
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = artifact.attempts.map((attempt, i) => `
        <div class="timeline-item ${attempt.review.pass ? 'pass' : 'fail'}">
            <h4>Attempt ${attempt.attempt} ${attempt.review.pass ? '✅ Passed' : '❌ Failed'}</h4>
            <div class="scores-grid">
                ${Object.entries(attempt.review.scores).map(([k, v]) => 
                    `<span class="score-badge ${v >= 4 ? 'high' : 'low'}">${k}: ${v}/5</span>`
                ).join('')}
            </div>
            ${attempt.review.feedback.length ? `
                <div class="feedback-list">
                    ${attempt.review.feedback.slice(0, 3).map(f => 
                        `<div class="feedback-item"><strong>${f.field}:</strong> ${f.issue}</div>`
                    ).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
    
    // Final Content
    const finalContentCard = document.getElementById('finalContentCard');
    const finalContent = document.getElementById('finalContent');
    
    if (artifact.final.status === 'approved' && artifact.final.content) {
        finalContentCard.style.display = 'block';
        const content = artifact.final.content;
        
        finalContent.innerHTML = `
            <div class="content-section">
                <h4>Explanation</h4>
                <p>${content.explanation.text}</p>
            </div>
            <div class="content-section">
                <h4>MCQs (${content.mcqs.length})</h4>
                ${content.mcqs.map((mcq, i) => `
                    <div class="mcq-item">
                        <strong>Q${i + 1}:</strong> ${mcq.question}<br>
                        ${mcq.options.map((opt, j) => 
                            `<span style="color: ${j === mcq.correct_index ? 'var(--success)' : 'inherit'}">${j === mcq.correct_index ? '✓' : '○'} ${opt}</span><br>`
                        ).join('')}
                    </div>
                `).join('')}
            </div>
            <div class="content-section">
                <h4>Teacher Notes</h4>
                <p><strong>Objective:</strong> ${content.teacher_notes.learning_objective}</p>
                <p><strong>Misconceptions:</strong> ${content.teacher_notes.common_misconceptions.join(', ')}</p>
            </div>
        `;
    } else {
        finalContentCard.style.display = 'none';
    }
    
    // Tags
    const tagsCard = document.getElementById('tagsCard');
    const tagsDiv = document.getElementById('tags');
    
    if (artifact.final.tags) {
        tagsCard.style.display = 'block';
        const tags = artifact.final.tags;
        tagsDiv.innerHTML = `
            <div class="tag-grid">
                <span class="tag primary">${tags.subject}</span>
                <span class="tag">${tags.topic}</span>
                <span class="tag">Grade ${tags.grade}</span>
                <span class="tag">${tags.difficulty}</span>
                <span class="tag">${tags.blooms_level}</span>
                ${tags.content_type.map(t => `<span class="tag">${t}</span>`).join('')}
            </div>
        `;
    } else {
        tagsCard.style.display = 'none';
    }
    
    // Raw Artifact
    document.getElementById('rawArtifact').textContent = JSON.stringify(artifact, null, 2);
}

function toggleRawArtifact() {
    const el = document.getElementById('rawArtifact');
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_URL}/history?limit=10`);
        const artifacts = await response.json();
        
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = artifacts.map(a => `
            <div class="history-item" onclick='displayResults(${JSON.stringify(a)})'>
                <strong>${a.input.topic}</strong> (Grade ${a.input.grade})<br>
                <small>Status: ${a.final?.status || 'unknown'} | ${new Date(a.timestamps.started_at).toLocaleString()}</small>
            </div>
        `).join('') || '<p>No history found</p>';
        
    } catch (error) {
        alert(`Error loading history: ${error.message}`);
    }
}