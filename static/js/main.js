/* CloudVault v4 — main.js
   Features: category accordion, image preview modal,
   dark/light theme toggle, global search, lazy image loading
*/

// ══ THEME ══
function initTheme() {
  const saved = localStorage.getItem('cv-theme') || 'dark';
  applyTheme(saved);
}

function applyTheme(theme) {
  document.body.classList.toggle('light', theme === 'light');
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = theme === 'light' ? '🌙' : '☀️';
  localStorage.setItem('cv-theme', theme);
}

function toggleTheme() {
  const isLight = document.body.classList.contains('light');
  applyTheme(isLight ? 'dark' : 'light');
}

// ══ FLASH AUTO-DISMISS ══
function initFlash() {
  document.querySelectorAll('.flash').forEach((f, i) => {
    setTimeout(() => {
      f.style.transition = 'opacity .35s ease, transform .35s ease';
      f.style.opacity = '0';
      f.style.transform = 'translateX(110%)';
      setTimeout(() => f.remove(), 370);
    }, 3500 + i * 300);
  });
}

// ══ UPLOAD ══
function initUpload() {
  const fileInput = document.getElementById('file-input');
  const dropZone  = document.getElementById('drop-zone');
  const dropInner = document.getElementById('drop-inner');
  const selFile   = document.getElementById('selected-file');
  const selName   = document.getElementById('sel-name');
  const selSize   = document.getElementById('sel-size');
  const btnUpload = document.getElementById('btn-upload');
  const progWrap  = document.getElementById('progress-wrap');
  const progFill  = document.getElementById('prog-fill');
  const progPct   = document.getElementById('prog-pct');
  const progName  = document.getElementById('prog-name');

  function fmtBytes(b) {
    if (b < 1024)        return b + ' B';
    if (b < 1024*1024)   return (b/1024).toFixed(1) + ' KB';
    return (b/(1024*1024)).toFixed(1) + ' MB';
  }

  function showPreview(file) {
    if (!file) return;
    if (file.size > 10*1024*1024) {
      alert(`"${file.name}" is too large (${fmtBytes(file.size)}). Max 10 MB.`);
      if (fileInput) fileInput.value = '';
      return;
    }
    if (selName)   selName.textContent  = file.name;
    if (selSize)   selSize.textContent  = fmtBytes(file.size);
    if (dropInner) dropInner.style.display = 'none';
    if (selFile)   selFile.style.display   = 'flex';
    if (btnUpload) btnUpload.disabled = false;
  }

  if (fileInput) fileInput.addEventListener('change', () => { if (fileInput.files[0]) showPreview(fileInput.files[0]); });

  if (dropZone) {
    dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', e => {
      e.preventDefault(); dropZone.classList.remove('dragover');
      const f = e.dataTransfer.files[0];
      if (f) { const dt = new DataTransfer(); dt.items.add(f); fileInput.files = dt.files; showPreview(f); }
    });
  }

  const uploadForm = document.getElementById('upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', () => {
      if (!btnUpload || btnUpload.disabled) return;
      const name = selName ? selName.textContent : 'file';
      if (progName) progName.textContent = 'Uploading ' + name + '…';
      if (progWrap) progWrap.style.display = 'block';
      let p = 0;
      const iv = setInterval(() => {
        p += Math.random() * 18 + 5;
        if (p >= 90) { p = 90; clearInterval(iv); }
        if (progFill) progFill.style.width = p + '%';
        if (progPct)  progPct.textContent  = Math.round(p) + '%';
      }, 130);
      btnUpload.disabled = true;
      btnUpload.textContent = 'Uploading…';
    });
  }
}

// ══ LAZY IMAGE LOADING ══
function initLazyImages() {
  const imgs = document.querySelectorAll('.lazy-img');
  if (!imgs.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        const src = img.dataset.src;
        if (!src) return;
        fetch(src)
          .then(r => r.json())
          .then(data => {
            if (data.src) { img.src = data.src; img.style.display = 'block'; }
          })
          .catch(() => {});
        observer.unobserve(img);
      }
    });
  }, { rootMargin: '100px' });

  imgs.forEach(img => observer.observe(img));
}

// ══ IMAGE PREVIEW MODAL ══
function previewImage(fileId, filename) {
  const modal = document.getElementById('preview-modal');
  const img   = document.getElementById('modal-img');
  const spin  = document.getElementById('modal-spinner');
  const name  = document.getElementById('modal-name');
  const meta  = document.getElementById('modal-meta');

  if (!modal) return;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';

  img.style.display = 'none';
  if (spin) spin.style.display = 'block';
  if (name) name.textContent   = filename;
  if (meta) meta.textContent   = '';

  fetch(`/preview/${fileId}`)
    .then(r => r.json())
    .then(data => {
      if (data.src) {
        img.src = data.src;
        img.style.display = 'block';
        if (spin) spin.style.display = 'none';
        if (meta) meta.textContent = `${data.size} · ${data.date}`;
      }
    })
    .catch(() => { if (spin) spin.textContent = '⚠ Failed to load'; });
}

function closeModal() {
  const modal = document.getElementById('preview-modal');
  if (modal) modal.classList.remove('open');
  document.body.style.overflow = '';
}

function closePreview(e) {
  if (e.target === e.currentTarget) closeModal();
}

// ══ CATEGORY ACCORDION ══
function toggleSection(cat) {
  const grid   = document.getElementById('grid-' + cat);
  const toggle = document.getElementById('toggle-' + cat);
  if (!grid) return;
  const isCollapsed = grid.classList.toggle('collapsed');
  if (toggle) toggle.classList.toggle('collapsed', isCollapsed);
  // Save state
  const states = JSON.parse(localStorage.getItem('cv-sections') || '{}');
  states[cat] = isCollapsed ? 'collapsed' : 'open';
  localStorage.setItem('cv-sections', JSON.stringify(states));
}

function restoreSectionStates() {
  const states = JSON.parse(localStorage.getItem('cv-sections') || '{}');
  Object.entries(states).forEach(([cat, state]) => {
    if (state === 'collapsed') {
      const grid   = document.getElementById('grid-' + cat);
      const toggle = document.getElementById('toggle-' + cat);
      if (grid)   grid.classList.add('collapsed');
      if (toggle) toggle.classList.add('collapsed');
    }
  });
}

function scrollToCategory(id) {
  const el = document.getElementById(id);
  if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
}

// ══ GLOBAL SEARCH ══
function globalSearch() {
  const input     = document.getElementById('search-input');
  const clearBtn  = document.getElementById('search-clear');
  const catsArea  = document.getElementById('categories-area');
  const srchArea  = document.getElementById('search-results-area');
  const srchGrid  = document.getElementById('search-results-grid');
  const noResults = document.getElementById('no-results');
  const resCount  = document.getElementById('results-count');

  const term = input.value.trim().toLowerCase();

  if (clearBtn) clearBtn.classList.toggle('visible', term.length > 0);

  if (!term) {
    if (catsArea)  catsArea.style.display  = '';
    if (srchArea)  srchArea.style.display  = 'none';
    return;
  }

  if (catsArea)  catsArea.style.display  = 'none';
  if (srchArea)  srchArea.style.display  = '';

  // Collect all file cards from all grids
  const allCards = document.querySelectorAll('#categories-area .file-card');
  const matched  = [];

  allCards.forEach(card => {
    const name = card.dataset.name || '';
    const type = card.dataset.type || '';
    if (name.includes(term) || type.includes(term)) matched.push(card.cloneNode(true));
  });

  if (srchGrid) {
    srchGrid.innerHTML = '';
    matched.forEach(card => srchGrid.appendChild(card));
  }

  if (resCount) resCount.textContent = `${matched.length} result${matched.length !== 1 ? 's' : ''}`;
  if (noResults) noResults.style.display = matched.length === 0 ? 'block' : 'none';
}

function clearSearch() {
  const input = document.getElementById('search-input');
  if (input) { input.value = ''; globalSearch(); input.focus(); }
}

// ══ UPLOAD PANEL HELPERS ══
function toggleUpload() { document.getElementById('upload-panel')?.classList.toggle('open'); }
function closeUpload()  { document.getElementById('upload-panel')?.classList.remove('open'); }
function confirmDelete(name) { return confirm(`Move "${name}" to Trash?`); }

// ══ KEYBOARD SHORTCUTS ══
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
  if (e.key === '/' && e.target.tagName !== 'INPUT') {
    e.preventDefault();
    document.getElementById('search-input')?.focus();
  }
});

// ══ BOOT ══
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initFlash();
  initUpload();
  initLazyImages();
  restoreSectionStates();

  // Animate file cards
  document.querySelectorAll('.file-card').forEach((card, i) => {
    card.style.opacity   = '0';
    card.style.transform = 'translateY(8px)';
    card.style.transition = `opacity .22s ease ${i*0.03}s, transform .22s ease ${i*0.03}s`;
    requestAnimationFrame(() => { card.style.opacity = '1'; card.style.transform = 'translateY(0)'; });
  });
});
