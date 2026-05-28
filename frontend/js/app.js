// ===== 红色文化智能学习平台 - 前端交互 =====

const API = '/api';

// ===== 工具函数 =====

function toast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast show ' + (type || '');
    setTimeout(() => t.classList.remove('show'), 2500);
}

async function api(method, path, data) {
    const opts = { method, headers: {} };
    if (data instanceof FormData) {
        opts.body = data;
    } else if (data) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(data);
    }
    const res = await fetch(API + path, opts);
    if (!res.ok) throw new Error((await res.json()).detail || '请求失败');
    return res.json();
}

// ===== Tab 切换 =====

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
        if (btn.dataset.tab === 'knowledge') loadKnowledge();
        if (btn.dataset.tab === 'media') loadMedia();
    });
});

// 回车触发问答
document.getElementById('qa-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') doAsk();
});

// ===== 智能问答 =====

async function doAsk() {
    const input = document.getElementById('qa-input');
    const question = input.value.trim();
    if (!question) { toast('请输入问题'); return; }

    const loading = document.getElementById('qa-loading');
    const answerBox = document.getElementById('qa-answer');
    loading.classList.add('show');
    answerBox.classList.remove('show');

    try {
        const result = await api('POST', '/ask', { question, top_k: 5 });
        document.getElementById('qa-text').innerHTML = result.answer.replace(/\n/g, '<br>');

        let srcHtml = '<strong>📖 参考来源：</strong><br>';
        result.sources.forEach(s => {
            srcHtml += `<div class="source-item">📄 ${s.source}: ${s.snippet.substring(0, 100)}...</div>`;
        });
        document.getElementById('qa-sources').innerHTML = srcHtml;

        let mediaHtml = '';
        result.related_media.forEach(m => {
            let el = '';
            if (m.type === 'images') el = `<img src="/${m.path}" alt="${m.title}" />`;
            else if (m.type === 'videos') el = `<video src="/${m.path}" controls></video>`;
            else if (m.type === 'audio') el = `<audio src="/${m.path}" controls></audio>`;
            mediaHtml += `<div class="media-card">${el}<div class="info">${m.title}<br><span class="tag">${m.type}</span></div></div>`;
        });
        document.getElementById('qa-media').innerHTML = mediaHtml;

        answerBox.classList.add('show');
    } catch (e) {
        toast('问答失败: ' + e.message);
    }
    loading.classList.remove('show');
}

// ===== 在线测验 =====

let quizState = null;

async function doQuizGenerate() {
    const topic = document.getElementById('quiz-topic').value || '红色文化';
    const qtype = document.getElementById('quiz-type').value;
    const num = document.getElementById('quiz-num').value;

    document.getElementById('quiz-loading').classList.add('show');
    document.getElementById('quiz-questions').innerHTML = '';
    document.getElementById('quiz-result').innerHTML = '';
    document.getElementById('quiz-submit').style.display = 'none';

    try {
        const form = new FormData();
        form.append('topic', topic); form.append('num', num); form.append('qtype', qtype);
        quizState = await api('POST', '/quiz/generate', form);
        renderQuiz(quizState);
        document.getElementById('quiz-submit').style.display = 'block';
    } catch (e) {
        toast('生成题目失败: ' + e.message);
    }
    document.getElementById('quiz-loading').classList.remove('show');
}

function renderQuiz(data) {
    let html = '';
    data.questions.forEach((q, i) => {
        html += `<div class="question-card" id="qc-${q.id}">
            <div class="q-stem"><span class="q-num">${i+1}</span> ${q.stem}</div>`;

        if (q.type === 'short') {
            html += `<div class="short-answer">
                <textarea placeholder="请输入你的回答..." onchange="submitOne(${q.id}, this.value)"></textarea>
            </div>`;
        } else {
            html += '<div class="options">';
            const inputType = q.type === 'multi' ? 'checkbox' : 'radio';
            q.options.forEach((opt, j) => {
                const label = String.fromCharCode(65 + j);
                html += `<label>
                    <input type="${inputType}" name="q${q.id}" value="${label}"
                    onchange="onOptionChange(${q.id}, '${q.type}')" />
                    <span>${opt}</span>
                </label>`;
            });
            html += '</div>';
        }
        html += '</div>';
    });
    document.getElementById('quiz-questions').innerHTML = html;
}

function onOptionChange(qid, qtype) {
    const card = document.getElementById('qc-' + qid);
    if (!card) return;
    if (qtype === 'multi') {
        const checked = card.querySelectorAll('input:checked');
        const answer = Array.from(checked).map(c => c.value).join(',');
        api('POST', '/quiz/answer', { question_id: qid, answer }).catch(() => {});
    } else {
        const checked = card.querySelector('input:checked');
        if (checked) {
            api('POST', '/quiz/answer', { question_id: qid, answer: checked.value }).catch(() => {});
        }
    }
    card.classList.add('answered');
}

function submitOne(qid, answer) {
    api('POST', '/quiz/answer', { question_id: qid, answer }).catch(() => {});
}

async function doQuizSubmit() {
    document.getElementById('quiz-loading').classList.add('show');
    try {
        const result = await api('POST', '/quiz/grade');
        renderResult(result);
    } catch (e) {
        toast('判分失败: ' + e.message);
    }
    document.getElementById('quiz-loading').classList.remove('show');
}

function renderResult(result) {
    let html = `<div class="score-card">
        <div class="score">${result.score}</div>
        <div class="label">分 (正确 ${result.correct}/${result.objective_total})</div>
    </div>`;

    html += '<h4 style="margin-bottom:12px;">📋 答题详情</h4>';
    result.details.forEach(d => {
        const icon = d.is_correct === true ? '✅' : d.is_correct === false ? '❌' : '⏳';
        html += `<div class="wrong-item">
            <strong>${icon} 第${d.id}题</strong>: ${d.stem}<br>
            <span style="color:var(--text-sub);">你的答案: ${d.user_answer || '未作答'}</span><br>
            <span class="correct-ans">正确答案: ${d.correct_answer}</span><br>
            <small>${d.explanation}</small>
            ${d.source ? `<br><small>📄 来源: ${d.source}</small>` : ''}
        </div>`;
    });

    html += `<button class="submit-btn" onclick="doQuizGenerate()" style="margin-top:20px;">🔄 再来一轮</button>`;
    document.getElementById('quiz-result').innerHTML = html;
    document.getElementById('quiz-submit').style.display = 'none';
}

// ===== 知识浏览 =====

async function loadKnowledge() {
    const grid = document.getElementById('kb-grid');
    const loading = document.getElementById('kb-loading');
    if (grid.children.length > 0) return;
    loading.classList.add('show');
    try {
        const docs = await api('GET', '/docs');
        grid.innerHTML = '';
        docs.forEach(d => {
            const card = document.createElement('div');
            card.className = 'knowledge-card';
            card.innerHTML = `<h4>📄 ${d.name}</h4><p>文件大小: ${(d.size/1024).toFixed(1)} KB<br>点击查看详情</p>`;
            card.onclick = () => loadDocDetail(d.name);
            grid.appendChild(card);
        });
    } catch (e) { grid.innerHTML = '<p>加载失败</p>'; }
    loading.classList.remove('show');
}

async function loadDocDetail(filename) {
    try {
        const docs = await api('GET', '/search?query=' + encodeURIComponent(filename.replace('.txt','').replace('.md','')) + '&top_k=3');
        document.getElementById('kb-title').textContent = '📖 ' + filename;
        let html = '';
        docs.results.forEach(r => {
            html += `<div style="margin-bottom:20px;padding:16px;background:var(--gold-light);border-radius:8px;">
                <p style="line-height:1.8;">${r.content.replace(/\n/g, '<br>')}</p>
                <small style="color:var(--text-sub);">📄 ${r.source}</small>
            </div>`;
        });
        document.getElementById('kb-content').innerHTML = html || '<p>暂无内容</p>';
        document.getElementById('kb-detail').style.display = 'block';
    } catch (e) { toast('加载详情失败'); }
}

// ===== 红色资源 =====

let mediaFilter = 'all';

async function loadMedia() {
    const grid = document.getElementById('media-grid');
    const loading = document.getElementById('media-loading');
    loading.classList.add('show');
    try {
        const params = mediaFilter !== 'all' ? '?type=' + mediaFilter : '';
        const media = await api('GET', '/media' + params);
        grid.innerHTML = '';
        if (media.length === 0) {
            grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:var(--text-sub);">暂无资源，请前往管理后台上传</p>';
        }
        media.forEach(m => {
            const card = document.createElement('div');
            card.className = 'media-card';
            let el = '';
            if (m.type === 'images') el = `<img src="/${m.path}" alt="${m.title}" loading="lazy" />`;
            else if (m.type === 'videos') el = `<video src="/${m.path}" controls preload="none"></video>`;
            else if (m.type === 'audio') el = `<div style="height:120px;display:flex;align-items:center;justify-content:center;background:var(--red-light);">🎵<br>${m.title}</div>`;
            card.innerHTML = `${el}<div class="info"><strong>${m.title}</strong><br>
                <span class="tag">${m.type}</span>
                ${m.tags.map(t => `<span class="tag">${t}</span>`).join('')}
            </div>`;
            grid.appendChild(card);
        });
    } catch (e) { grid.innerHTML = '<p>加载失败</p>'; }
    loading.classList.remove('show');
}

function filterMedia(type) {
    mediaFilter = type;
    document.querySelectorAll('.filter-bar button').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('media-grid').innerHTML = '';
    loadMedia();
}

// ===== 故事播报 =====

document.getElementById('narrate-story').addEventListener('change', function() {
    if (this.value) {
        document.getElementById('narrate-text').value = '请讲述关于' + this.value + '的红色故事。';
    }
});

async function doNarrate() {
    const text = document.getElementById('narrate-text').value.trim();
    if (!text) { toast('请输入或选择故事文本'); return; }

    document.getElementById('narrate-loading').classList.add('show');
    document.getElementById('narrate-result').innerHTML = '';
    try {
        const result = await api('POST', '/narrate', { text, title: '红色故事播报' });
        if (result.status === 'success' && result.audio) {
            document.getElementById('narrate-result').innerHTML =
                `<div class="audio-player">
                    <audio src="/${result.audio.path}" controls></audio>
                    <span>${result.audio.title}</span>
                </div>`;
            toast('语音生成成功', 'success');
        } else {
            toast('语音合成失败，请检查网络连接');
        }
    } catch (e) { toast('播报失败: ' + e.message); }
    document.getElementById('narrate-loading').classList.remove('show');
}