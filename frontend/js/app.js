// ===== 红色文化智能学习平台 v3 =====
var API = '/api';

function toast(m, t) {
    var el = document.getElementById('toast');
    if (!el) return;
    el.textContent = m; el.className = 'toast show ' + (t || '');
    setTimeout(function(){ el.classList.remove('show'); }, 2500);
}

async function api(method, path, data) {
    var opts = { method: method, headers: {} };
    if (data instanceof FormData) opts.body = data;
    else if (data) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(data); }
    var res = await fetch(API + path, opts);
    if (!res.ok) { var e = await res.json(); throw new Error(e.detail || '请求失败'); }
    return res.json();
}

// ========== 页面初始化 ==========
document.addEventListener('DOMContentLoaded', function() {

// ===== Tab 切换 =====
var tabs = document.querySelectorAll('.tab-btn');
tabs.forEach(function(btn) {
    btn.onclick = function() {
        document.querySelectorAll('.tab-btn').forEach(function(b){ b.classList.remove('active'); });
        document.querySelectorAll('.tab-content').forEach(function(c){ c.classList.remove('active'); });
        btn.classList.add('active');
        var panel = document.getElementById('tab-' + btn.getAttribute('data-tab'));
        if (panel) panel.classList.add('active');
        if (btn.getAttribute('data-tab') === 'knowledge') loadKnowledge();
        if (btn.getAttribute('data-tab') === 'media') loadMedia();
    };
});

// 回车触发问答
var qaInput = document.getElementById('qa-input');
if (qaInput) qaInput.onkeydown = function(e) { if (e.key === 'Enter') doAsk(); };

// ===== 智能问答 =====
window.doAsk = async function() {
    var input = document.getElementById('qa-input');
    var q = (input && input.value || '').trim();
    if (!q) { toast('请输入问题'); return; }
    var loading = document.getElementById('qa-loading');
    var box = document.getElementById('qa-answer');
    loading.classList.add('show'); box.classList.remove('show');
    try {
        var r = await api('POST', '/ask', { question: q, top_k: 5 });
        document.getElementById('qa-text').innerHTML = (r.answer || '').replace(/\n/g, '<br>');
        var srcs = '<strong>📖 参考来源：</strong><br>';
        (r.sources || []).forEach(function(s){ srcs += '<div class="source-item">📄 '+s.source+': '+(s.snippet||'').substring(0,100)+'...</div>'; });
        document.getElementById('qa-sources').innerHTML = srcs;
        var mh = '';
        (r.related_media || []).forEach(function(m){
            var el = '';
            if (m.type==='images') el = '<img src="/'+m.path+'" alt="'+m.title+'" />';
            else if (m.type==='videos') el = '<video src="/'+m.path+'" controls></video>';
            else if (m.type==='audio') el = '<audio src="/'+m.path+'" controls></audio>';
            mh += '<div class="media-card">'+el+'<div class="info">'+m.title+'<br><span class="tag">'+m.type+'</span></div></div>';
        });
        document.getElementById('qa-media').innerHTML = mh;
        box.classList.add('show');
    } catch(e) { toast('问答失败: '+e.message); }
    loading.classList.remove('show');
};

// ===== 在线测验 =====
var quizState = null;

window.doQuizGenerate = async function() {
    var topic = document.getElementById('quiz-topic').value || '红色文化';
    var qtype = document.getElementById('quiz-type').value;
    var num = document.getElementById('quiz-num').value;
    document.getElementById('quiz-loading').classList.add('show');
    document.getElementById('quiz-questions').innerHTML = '';
    document.getElementById('quiz-result').innerHTML = '';
    document.getElementById('quiz-submit').style.display = 'none';
    try {
        var form = new FormData();
        form.append('topic', topic); form.append('num', num); form.append('qtype', qtype);
        quizState = await api('POST', '/quiz/generate', form);
        renderQuiz(quizState);
        document.getElementById('quiz-submit').style.display = 'block';
    } catch(e) { toast('生成失败: '+e.message); }
    document.getElementById('quiz-loading').classList.remove('show');
};

function renderQuiz(data) {
    var html = '';
    (data.questions || []).forEach(function(q, i){
        html += '<div class="question-card" id="qc-'+q.id+'"><div class="q-stem"><span class="q-num">'+(i+1)+'</span>'+q.stem+'</div>';
        if (q.type === 'short') {
            html += '<div class="short-answer"><textarea placeholder="请输入回答..." onchange="submitOne('+q.id+',this.value)"></textarea></div>';
        } else {
            html += '<div class="options">';
            var itype = q.type==='multi' ? 'checkbox' : 'radio';
            (q.options||[]).forEach(function(o,j){
                var L = String.fromCharCode(65+j);
                html += '<label><input type="'+itype+'" name="q'+q.id+'" value="'+L+'" onchange="onOptionChange('+q.id+',\''+q.type+'\')" /><span>'+o+'</span></label>';
            });
            html += '</div>';
        }
        html += '</div>';
    });
    document.getElementById('quiz-questions').innerHTML = html;
}

window.onOptionChange = function(qid, qtype) {
    var card = document.getElementById('qc-'+qid);
    if (!card) return;
    if (qtype === 'multi') {
        var cbs = card.querySelectorAll('input:checked');
        var ans = Array.from(cbs).map(function(c){return c.value;}).join(',');
        api('POST','/quiz/answer',{question_id:qid,answer:ans}).catch(function(){});
    } else {
        var cb = card.querySelector('input:checked');
        if (cb) api('POST','/quiz/answer',{question_id:qid,answer:cb.value}).catch(function(){});
    }
    card.classList.add('answered');
};

window.submitOne = function(qid, ans) { api('POST','/quiz/answer',{question_id:qid,answer:ans}).catch(function(){}); };

window.doQuizSubmit = async function() {
    document.getElementById('quiz-loading').classList.add('show');
    try { renderResult(await api('POST','/quiz/grade')); }
    catch(e) { toast('判分失败: '+e.message); }
    document.getElementById('quiz-loading').classList.remove('show');
};

function renderResult(r) {
    var html = '<div class="score-card"><div class="score">'+r.score+'</div><div class="label">分 (正确 '+r.correct+'/'+r.objective_total+')</div></div>';
    html += '<h4 style="margin-bottom:12px;">📋 答题详情</h4>';
    (r.details||[]).forEach(function(d){
        var icon = d.is_correct===true ? '✅' : d.is_correct===false ? '❌' : '⏳';
        html += '<div class="wrong-item"><strong>'+icon+' 第'+d.id+'题</strong>: '+d.stem+'<br><span style="color:var(--text-sub);">你的答案: '+(d.user_answer||'未作答')+'</span><br><span class="correct-ans">正确答案: '+d.correct_answer+'</span><br><small>'+d.explanation+'</small>'+(d.source?'<br><small>📄 来源: '+d.source+'</small>':'')+'</div>';
    });
    html += '<button class="submit-btn" onclick="doQuizGenerate()" style="margin-top:20px;">🔄 再来一轮</button>';
    document.getElementById('quiz-result').innerHTML = html;
    document.getElementById('quiz-submit').style.display = 'none';
}

// ===== 知识浏览 =====
window.loadKnowledge = async function() {
    var grid = document.getElementById('kb-grid');
    if (grid.children.length > 0) return;
    document.getElementById('kb-loading').classList.add('show');
    try {
        var docs = await api('GET','/docs');
        grid.innerHTML = '';
        docs.forEach(function(d){
            var c = document.createElement('div'); c.className = 'knowledge-card';
            c.innerHTML = '<h4>📄 '+d.name+'</h4><p>文件大小: '+(d.size/1024).toFixed(1)+' KB<br>点击查看详情</p>';
            c.onclick = function(){ loadDocDetail(d.name); };
            grid.appendChild(c);
        });
    } catch(e) { grid.innerHTML = '<p>加载失败</p>'; }
    document.getElementById('kb-loading').classList.remove('show');
};

window.loadDocDetail = async function(name) {
    try {
        var docs = await api('GET','/search?query='+encodeURIComponent(name.replace('.txt',''))+'&top_k=3');
        document.getElementById('kb-title').textContent = '📖 '+name;
        var html = '';
        (docs.results||[]).forEach(function(r){ html += '<div style="margin-bottom:20px;padding:16px;background:var(--gold-light);border-radius:8px;"><p style="line-height:1.8;">'+r.content.replace(/\n/g,'<br>')+'</p><small style="color:var(--text-sub);">📄 '+r.source+'</small></div>'; });
        document.getElementById('kb-content').innerHTML = html || '<p>暂无内容</p>';
        document.getElementById('kb-detail').style.display = 'block';
    } catch(e) { toast('加载失败'); }
};

// ===== 红色资源 =====
var mediaFilter = 'all';
window.loadMedia = async function() {
    var grid = document.getElementById('media-grid');
    document.getElementById('media-loading').classList.add('show');
    try {
        var params = mediaFilter!=='all' ? '?type='+mediaFilter : '';
        var media = await api('GET','/media'+params);
        grid.innerHTML = '';
        if (media.length===0) { grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:var(--text-sub);">暂无资源</p>'; }
        media.forEach(function(m){
            var c = document.createElement('div'); c.className = 'media-card';
            var el = '';
            if (m.type==='images') el = '<img src="/'+m.path+'" alt="'+m.title+'" loading="lazy" />';
            else if (m.type==='videos') el = '<video src="/'+m.path+'" controls preload="none"></video>';
            else if (m.type==='audio') el = '<div style="height:120px;display:flex;align-items:center;justify-content:center;background:var(--red-light);">🎵<br>'+m.title+'</div>';
            c.innerHTML = el+'<div class="info"><strong>'+m.title+'</strong><br><span class="tag">'+m.type+'</span>'+(m.tags||[]).map(function(t){return '<span class="tag">'+t+'</span>';}).join('')+'</div>';
            grid.appendChild(c);
        });
    } catch(e) { grid.innerHTML = '<p>加载失败</p>'; }
    document.getElementById('media-loading').classList.remove('show');
};

window.filterMedia = function(type) {
    mediaFilter = type;
    document.querySelectorAll('.filter-bar button').forEach(function(b){ b.classList.remove('active'); });
    event.target.classList.add('active');
    document.getElementById('media-grid').innerHTML = '';
    loadMedia();
};

// ===== 故事播报 =====
window.toggleNarrateMode = function() {
    var modeEl = document.querySelector('input[name="narrate-mode"]:checked');
    if (!modeEl) return;
    var mode = modeEl.value;
    var aiArea = document.getElementById('narrate-ai-area');
    var manualArea = document.getElementById('narrate-manual-area');
    var desc = document.getElementById('narrate-desc');
    if (!aiArea || !manualArea) return;
    var result = document.getElementById('narrate-result');
    if (result) result.innerHTML = '';
    if (mode === 'ai') {
        aiArea.style.display = 'flex'; manualArea.style.display = 'none';
        if (desc) desc.textContent = '输入主题，AI 自动撰写文稿并合成语音播报';
    } else {
        aiArea.style.display = 'none'; manualArea.style.display = 'block';
        if (desc) desc.textContent = '自行编辑文稿内容，一键合成语音播报';
    }
};

window.doGenerateNarration = async function() {
    var input = document.getElementById('narrate-topic');
    var topic = (input && input.value || '').trim();
    if (!topic) { toast('请输入红色故事主题'); return; }
    var btn = document.getElementById('narrate-gen-btn');
    var loading = document.getElementById('narrate-loading');
    if (!btn) return;
    btn.disabled = true; btn.textContent = '生成中...';
    loading.classList.add('show');
    try {
        var r = await api('POST','/explain',{question:'请以生动叙事的方式撰写一段关于"'+topic+'"的红色故事播报文稿，约150字，语言口语化、适合朗读、富有感情。',top_k:3});
        var text = r.explanation || '';
        if (!text) { toast('AI 文稿生成失败'); loading.classList.remove('show'); btn.disabled=false; btn.textContent='✍️ AI 生成播报'; return; }
        var audio = await api('POST','/narrate',{text:text,title:topic+' · 红色故事'});
        loading.classList.remove('show');
        if (audio.status==='success' && audio.audio) {
            document.getElementById('narrate-result').innerHTML = '<div class="audio-player"><audio src="/'+audio.audio.path+'" controls></audio><span>'+audio.audio.title+'</span></div>';
            toast('AI 播报生成成功！','success');
        } else { toast('语音合成失败'); }
    } catch(e) { toast('生成失败: '+e.message); loading.classList.remove('show'); }
    btn.disabled = false; btn.textContent = '✍️ AI 生成播报';
};

window.doNarrate = async function() {
    var ta = document.getElementById('narrate-text');
    var text = (ta && ta.value || '').trim();
    if (!text) { toast('请输入播报文稿'); return; }
    var loading = document.getElementById('narrate-loading');
    loading.classList.add('show');
    document.getElementById('narrate-result').innerHTML = '';
    try {
        var r = await api('POST','/narrate',{text:text,title:'自定义播报'});
        if (r.status==='success' && r.audio) {
            document.getElementById('narrate-result').innerHTML = '<div class="audio-player"><audio src="/'+r.audio.path+'" controls></audio><span>'+r.audio.title+'</span></div>';
            toast('语音生成成功','success');
        } else { toast('语音合成失败'); }
    } catch(e) { toast('播报失败: '+e.message); }
    loading.classList.remove('show');
};

// 回车触发 AI 生成
var nt = document.getElementById('narrate-topic');
if (nt) nt.onkeydown = function(e) { if (e.key==='Enter') doGenerateNarration(); };

// 初始化
try { toggleNarrateMode(); } catch(e) {}

}); // end DOMContentLoaded