/* ═══════════════════════════════════════
   MediaTools PRO — Frontend Logic
   ═══════════════════════════════════════ */

// ── Language ──────────────────────────────────
let currentLang = 'ar';

function toggleLang() {
  currentLang = currentLang === 'ar' ? 'en' : 'ar';
  const html = document.documentElement;
  html.setAttribute('lang', currentLang);
  html.setAttribute('dir', currentLang === 'ar' ? 'rtl' : 'ltr');

  document.querySelectorAll('.lang-ar').forEach(el => {
    el.style.display = currentLang === 'ar' ? '' : 'none';
  });
  document.querySelectorAll('.lang-en').forEach(el => {
    el.style.display = currentLang === 'en' ? '' : 'none';
  });
}

// ── Tab Switching ─────────────────────────────
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + tabId).classList.add('active');
  document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
}

// ── File Storage ──────────────────────────────
const fileStore = {};

function handleFiles(input, key) {
  const files = Array.from(input.files);
  if (!files.length) return;
  fileStore[key] = files;
  renderFileList(key, files);
}

function renderFileList(key, files) {
  const container = document.getElementById(`files-${key}`);
  if (!container) return;
  container.innerHTML = '';
  files.forEach(f => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <span class="file-item-name">📄 ${f.name}</span>
      <span class="file-item-size">${formatBytes(f.size)}</span>
    `;
    container.appendChild(item);
  });
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// ── Dropzone Drag & Drop ──────────────────────
document.querySelectorAll('.dropzone').forEach(dz => {
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragging'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragging'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('dragging');
    const input = dz.querySelector('.file-input');
    const key = dz.id.replace('dz-', '');
    if (input) {
      const dt = new DataTransfer();
      Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
      input.files = dt.files;
      handleFiles(input, key);
    }
  });
});

function triggerInput(dz) {
  const input = dz.querySelector('.file-input');
  if (input) input.click();
}

// ── Toast ─────────────────────────────────────
let toastTimer;
function showToast(msg, type = 'info') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── Progress Modal ────────────────────────────
let progressInterval;
function showProgress(msg = '') {
  const modal = document.getElementById('progress-modal');
  modal.style.display = 'flex';
  document.getElementById('progress-bar').style.width = '0%';
  if (msg) {
    document.getElementById('modal-message').textContent = msg;
    document.getElementById('modal-message-en').textContent = msg;
  }
  let pct = 0;
  progressInterval = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8, 85);
    document.getElementById('progress-bar').style.width = pct + '%';
  }, 400);
}
function hideProgress() {
  clearInterval(progressInterval);
  document.getElementById('progress-bar').style.width = '100%';
  setTimeout(() => { document.getElementById('progress-modal').style.display = 'none'; }, 400);
}

// ── Task Polling ──────────────────────────────
async function pollTask(taskId, onSuccess, onError, maxWait = 900000) {
  const start = Date.now();
  const interval = setInterval(async () => {
    if (Date.now() - start > maxWait) {
      clearInterval(interval);
      hideProgress();
      onError(currentLang === 'ar' ? 'انتهت مهلة العملية' : 'Operation timed out');
      return;
    }
    try {
      const res = await fetch(`/api/task/${taskId}`);
      const data = await res.json();
      if (data.status === 'done') {
        clearInterval(interval);
        hideProgress();
        onSuccess(data.result);
      } else if (data.status === 'error') {
        clearInterval(interval);
        hideProgress();
        onError(data.error || 'Unknown error');
      }
    } catch (e) {
      clearInterval(interval);
      hideProgress();
      onError(e.message);
    }
  }, 1500);
}

// ── API Helper ────────────────────────────────
async function apiPost(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

async function apiPostJSON(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

// ── Download Result ───────────────────────────
function showDownloadLink(result, containerId) {
  const container = containerId ? document.getElementById(containerId) : null;
  let html = '<div class="result-box">';
  const files = result.files || (result.file ? [result] : []);
  files.forEach(f => {
    html += `<a href="/api/download-result/${f.file}" download="${f.file}">
      ⬇️ ${f.file}
      ${f.reduction ? `<span style="margin-right:auto;color:var(--success);font-size:0.8rem">-${f.reduction}</span>` : ''}
    </a>`;
  });
  html += '</div>';
  if (container) {
    container.insertAdjacentHTML('afterend', html);
  } else {
    showToast(currentLang === 'ar' ? 'اكتملت العملية بنجاح ✓' : 'Operation completed successfully ✓', 'success');
  }
}

// ── Generic submit ────────────────────────────
async function submitWithFile(key, apiUrl, extraFields, progressMsg, container) {
  const files = fileStore[key];
  if (!files || !files.length) {
    showToast(currentLang === 'ar' ? 'يرجى اختيار ملف أولاً' : 'Please select a file first', 'error');
    return;
  }
  const fd = new FormData();
  if (files.length === 1) {
    fd.append('file', files[0]);
  } else {
    files.forEach(f => fd.append('files', f));
  }
  Object.entries(extraFields || {}).forEach(([k, v]) => fd.append(k, v));
  showProgress(progressMsg);
  try {
    const { task_id } = await apiPost(apiUrl, fd);
    pollTask(task_id,
      result => {
        // Remove old result if any
        const old = document.querySelector(`#${container} + .result-box`);
        if (old) old.remove();
        showDownloadLink(result, container);
        showToast(currentLang === 'ar' ? '✓ اكتمل بنجاح' : '✓ Completed successfully', 'success');
      },
      err => showToast('❌ ' + err, 'error')
    );
  } catch (e) {
    hideProgress();
    showToast('❌ ' + e.message, 'error');
  }
}

// ═══ PDF ═════════════════════════════════════
function submitPdfMerge() {
  submitWithFile('pdf-merge', '/api/pdf/merge', {}, 
    currentLang === 'ar' ? 'جارٍ دمج الملفات...' : 'Merging PDFs...',
    'files-pdf-merge');
}

function submitImgToPdf() {
  submitWithFile('img-pdf', '/api/pdf/images-to-pdf', {},
    currentLang === 'ar' ? 'جارٍ تحويل الصور...' : 'Converting images...',
    'files-img-pdf');
}

function submitPdfCompress() {
  submitWithFile('pdf-compress', '/api/pdf/compress', {},
    currentLang === 'ar' ? 'جارٍ ضغط الملف...' : 'Compressing PDF...',
    'files-pdf-compress');
}

// ═══ IMAGE ═══════════════════════════════════
function submitImgConvert() {
  const fmt = document.getElementById('img-convert-fmt').value;
  submitWithFile('img-convert', '/api/image/convert', { format: fmt },
    currentLang === 'ar' ? 'جارٍ تحويل الصورة...' : 'Converting image...',
    'files-img-convert');
}

function submitImgCompress() {
  const quality = document.getElementById('img-quality').value;
  submitWithFile('img-compress', '/api/image/compress', { quality },
    currentLang === 'ar' ? 'جارٍ ضغط الصورة...' : 'Compressing image...',
    'files-img-compress');
}

function submitImgResize() {
  const w = document.getElementById('resize-w').value;
  const h = document.getElementById('resize-h').value;
  if (!w && !h) {
    showToast(currentLang === 'ar' ? 'أدخل العرض أو الارتفاع على الأقل' : 'Enter at least width or height', 'error');
    return;
  }
  submitWithFile('img-resize', '/api/image/resize', { width: w, height: h },
    currentLang === 'ar' ? 'جارٍ تغيير الحجم...' : 'Resizing...',
    'files-img-resize');
}

// ═══ VIDEO ═══════════════════════════════════
function submitVidConvert() {
  const fmt = document.getElementById('vid-fmt').value;
  const quality = document.getElementById('vid-quality').value;
  submitWithFile('vid-convert', '/api/video/convert', { format: fmt, quality },
    currentLang === 'ar' ? 'جارٍ تحويل الفيديو...' : 'Converting video...',
    'files-vid-convert');
}

function submitExtractAudio() {
  const fmt = document.getElementById('audio-extract-fmt').value;
  submitWithFile('extract-audio', '/api/video/extract-audio', { format: fmt },
    currentLang === 'ar' ? 'جارٍ استخراج الصوت...' : 'Extracting audio...',
    'files-extract-audio');
}

function submitVidTrim() {
  const start = document.getElementById('trim-start').value;
  const end = document.getElementById('trim-end').value;
  if (!end) {
    showToast(currentLang === 'ar' ? 'أدخل وقت النهاية' : 'Enter end time', 'error');
    return;
  }
  submitWithFile('vid-trim', '/api/video/trim', { start, end },
    currentLang === 'ar' ? 'جارٍ قص الفيديو...' : 'Trimming video...',
    'files-vid-trim');
}

function submitVidCompress() {
  const quality = document.getElementById('vid-compress-quality').value;
  submitWithFile('vid-compress', '/api/video/compress', { quality },
    currentLang === 'ar' ? 'جارٍ ضغط الفيديو...' : 'Compressing video...',
    'files-vid-compress');
}

// ═══ AUDIO ═══════════════════════════════════
function submitAudioConvert() {
  const fmt = document.getElementById('audio-fmt').value;
  submitWithFile('audio-convert', '/api/audio/convert', { format: fmt },
    currentLang === 'ar' ? 'جارٍ تحويل الصوت...' : 'Converting audio...',
    'files-audio-convert');
}

// ═══ DOWNLOAD ════════════════════════════════
async function submitDownloadUrl() {
  const url = document.getElementById('dl-url').value.trim();
  if (!url) { showToast(currentLang === 'ar' ? 'أدخل الرابط' : 'Enter URL', 'error'); return; }
  showProgress(currentLang === 'ar' ? 'جارٍ التنزيل...' : 'Downloading...');
  try {
    const { task_id } = await apiPostJSON('/api/download/url', { url });
    pollTask(task_id,
      result => { showDownloadResult(result, 'dl-url'); },
      err => showToast('❌ ' + err, 'error')
    );
  } catch(e) { hideProgress(); showToast('❌ ' + e.message, 'error'); }
}

async function submitYouTube() {
  const url = document.getElementById('yt-url').value.trim();
  const format = document.getElementById('yt-type').value;
  const quality = document.getElementById('yt-quality').value;
  if (!url) { showToast(currentLang === 'ar' ? 'أدخل رابط يوتيوب' : 'Enter YouTube URL', 'error'); return; }
  showProgress(currentLang === 'ar' ? 'جارٍ التنزيل من يوتيوب...' : 'Downloading from YouTube...');
  try {
    const { task_id } = await apiPostJSON('/api/download/youtube', { url, format, quality });
    pollTask(task_id,
      result => showDownloadResult(result, 'yt-url'),
      err => showToast('❌ ' + err, 'error'),
      1800000  // 30 min for playlists
    );
  } catch(e) { hideProgress(); showToast('❌ ' + e.message, 'error'); }
}

async function submitSocial() {
  const url = document.getElementById('social-url').value.trim();
  if (!url) { showToast(currentLang === 'ar' ? 'أدخل الرابط' : 'Enter URL', 'error'); return; }
  showProgress(currentLang === 'ar' ? 'جارٍ التنزيل...' : 'Downloading...');
  try {
    const { task_id } = await apiPostJSON('/api/download/social', { url });
    pollTask(task_id,
      result => showDownloadResult(result, 'social-url'),
      err => showToast('❌ ' + err, 'error')
    );
  } catch(e) { hideProgress(); showToast('❌ ' + e.message, 'error'); }
}

function showDownloadResult(result, inputId) {
  const input = document.getElementById(inputId);
  // Remove previous result
  const existing = input?.parentElement?.nextElementSibling;
  if (existing?.classList.contains('result-box')) existing.remove();

  const files = result.files || (result.file ? [result] : []);
  if (!files.length) { showToast(currentLang === 'ar' ? 'لا توجد ملفات للتنزيل' : 'No files found', 'error'); return; }

  let html = '<div class="result-box">';
  files.forEach(f => {
    html += `<a href="/api/download-result/${f.file}" download="${f.file}">⬇️ ${f.file}</a>`;
  });
  html += '</div>';
  input?.closest('.url-input-wrap')?.insertAdjacentHTML('afterend', html);
  showToast(currentLang === 'ar' ? `✓ تم تنزيل ${files.length} ملف` : `✓ Downloaded ${files.length} file(s)`, 'success');
}

// ═══ OCR ═════════════════════════════════════
async function submitOCR() {
  const files = fileStore['ocr'];
  if (!files || !files.length) {
    showToast(currentLang === 'ar' ? 'يرجى اختيار صورة' : 'Please select an image', 'error');
    return;
  }
  const lang = document.getElementById('ocr-lang').value;
  const engine = document.getElementById('ocr-engine').value;
  const fd = new FormData();
  fd.append('file', files[0]);
  fd.append('lang', lang);
  fd.append('engine', engine);
  showProgress(currentLang === 'ar' ? 'جارٍ استخراج النص...' : 'Extracting text...');
  try {
    const { task_id } = await apiPost('/api/ocr/extract', fd);
    pollTask(task_id,
      result => {
        document.getElementById('ocr-text').value = result.full_text || '';
        document.getElementById('ocr-stats').textContent =
          `${result.engine} | ${currentLang === 'ar' ? 'كتل نصية' : 'text blocks'}: ${result.block_count}`;
        document.getElementById('ocr-result').style.display = 'block';
        showToast(currentLang === 'ar' ? '✓ تم الاستخراج بنجاح' : '✓ Extraction complete', 'success');
      },
      err => showToast('❌ ' + err, 'error')
    );
  } catch(e) { hideProgress(); showToast('❌ ' + e.message, 'error'); }
}

function copyOCR() {
  const text = document.getElementById('ocr-text').value;
  navigator.clipboard.writeText(text).then(() => {
    showToast(currentLang === 'ar' ? '✓ تم النسخ' : '✓ Copied!', 'success');
  });
}

// ── Init stagger animations ────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.tool-card');
  cards.forEach((card, i) => {
    card.style.animationDelay = `${i * 0.08}s`;
    card.style.opacity = '0';
    card.style.animation = `fade-up 0.5s ease ${i * 0.08}s both`;
  });
});
