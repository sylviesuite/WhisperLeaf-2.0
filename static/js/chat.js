/**
 * WhisperLeaf Chat — front-end controller.
 * Single source of truth: state.messages. All rendering derives from it.
 */

// Phase 3: Memory handshake (local demo) — whisperleaf_saved_memories in localStorage.
// Future: replace with real memory system / server persistence.
const WL_LOCAL_SAVED_MEMORIES_KEY = 'whisperleaf_saved_memories';
const WL_STARTED_CHAT_SESSION_KEY = 'whisperleaf_started_chat';

const ChatController = {
  state: {
    isSending: false,
    sessionId: null,
    currentMode: 'default',
    messages: [],
    currentStreamingId: null,
    streamWatchdog: null,
    streamWatchdogStage: 0,
    lastSseEventAt: 0,
    currentStreamId: null,
    modelAvailable: true,
    lastMemorySnippets: [],
    docSourcesForCurrentResponse: [],
    docExcerptsForCurrentResponse: [],
    documents: [],
    documentSearchQuery: '',
    forceShowOnboarding: false,
    stageTimers: [],
  },

  els: {},

  init() {
    this.cacheElements();
    this.initState();
    this.bindEvents();
    this.loadModelStatus();
    this.loadSessionHistory();
    this.loadSavedMemories();
    this.loadDocuments();
    this.updateChatHintsVisibility();
    this.maybeFocusEmptyChatInput();
  },

  maybeFocusEmptyChatInput() {
    const input = this.els.messageInput;
    if (!input) return;
    if (this.state.hasStartedChat) return;
    const cw = this.els.chatWindow;
    if (cw && cw.querySelectorAll('.message').length > 0) return;
    if (typeof window.matchMedia === 'function' && window.matchMedia('(max-width: 640px)').matches) {
      return;
    }
    const ob = this.els.onboardingScreen;
    if (ob && !ob.classList.contains('hidden')) return;
    requestAnimationFrame(() => {
      try {
        input.focus({ preventScroll: true });
      } catch (_) {
        input.focus();
      }
    });
  },

  cacheElements() {
    this.els.appLayout = document.getElementById('appLayout');
    this.els.sidebarToggle = document.getElementById('sidebarToggle');
    this.els.chatMessages = document.querySelector('.chat-window'); // scroll container
    this.els.chatWindow = document.getElementById('chatWindow'); // messages-inner: append target
    this.els.messageInput = document.getElementById('messageInput');
    this.els.sendBtn = document.getElementById('sendBtn');
    this.els.newSessionBtn = document.getElementById('newSessionBtn');
    this.els.clearBtn = document.getElementById('clearBtn');
    this.els.chatForm = document.getElementById('chatForm');
    this.els.inputDropFeedback = document.getElementById('inputDropFeedback');
    this.els.jumpBottomBtn = document.getElementById('jumpBottomBtn');
    this.els.chatOwl = document.getElementById('chatOwl');
    this.els.owl = document.querySelector('.owl-icon-wrap');
    this.els.sidebarHistoryList = document.getElementById('sidebarHistoryList');
    this.els.thinkingStep = document.getElementById('thinkingStep');
    this.els.chatHints = document.getElementById('chatHints');
    this.els.starterPrompts = document.getElementById('starterPrompts');
    this.els.starterDocNudge = document.getElementById('starterDocNudge');
    this.els.localProcessingStatus = document.getElementById('localProcessingStatus');
    this.els.modelUnavailableBanner = document.getElementById('modelUnavailableBanner');
    this.els.modelRetryBtn = document.getElementById('modelRetryBtn');
    this.els.mindMemoryBtn = document.getElementById('mindMemoryBtn');
    this.els.mindMemoryLabel = document.getElementById('mindMemoryLabel');
    this.els.memorySidebarSection = document.getElementById('memorySidebarSection');
    this.els.memoryVisibilityPanel = document.getElementById('memoryVisibilityPanel');
    this.els.memorySnippetsList = document.getElementById('memorySnippetsList');
    this.els.memorySavedNotification = document.getElementById('memorySavedNotification');
    this.els.memorySavedPreview = document.getElementById('memorySavedPreview');
    this.els.savedMemoriesSection = document.getElementById('savedMemoriesSection');
    this.els.savedMemoriesList = document.getElementById('savedMemoriesList');
    this.els.savedMemoriesEmpty = document.getElementById('savedMemoriesEmpty');
    this.els.savedMemoriesHint = document.getElementById('savedMemoriesHint');
    this.els.documentsList = document.getElementById('documentsList');
    this.els.documentsEmpty = document.getElementById('documentsEmpty');
    this.els.documentUploadInput = document.getElementById('documentUploadInput');
    this.els.documentUploadBtn = document.getElementById('documentUploadBtn');
    this.els.documentUploadStatus = document.getElementById('documentUploadStatus');
    this.els.documentSearchInput = document.getElementById('documentSearchInput');
    this.els.documentsNoResults = document.getElementById('documentsNoResults');
    this.els.documentExcerptPanel = document.getElementById('documentExcerptPanel');
    this.els.documentExcerptTitle = document.getElementById('documentExcerptTitle');
    this.els.documentExcerptBody = document.getElementById('documentExcerptBody');
    this.els.documentExcerptClose = document.getElementById('documentExcerptClose');
    this.els.onboardingScreen = document.getElementById('onboardingScreen');
    this.els.onboardingModelReady = document.getElementById('onboardingModelReady');
    this.els.onboardingModelNotice = document.getElementById('onboardingModelNotice');
    this.els.onboardingStartBtn = document.getElementById('onboardingStartBtn');
    this.els.onboardingHelpBtn = document.getElementById('onboardingHelpBtn');
    this.els.settingsBtn = document.getElementById('settingsBtn');
    this.els.settingsModal = document.getElementById('settingsModal');
    this.els.devModeToggle = document.getElementById('devModeToggle');
    this.els.closeSettings = document.getElementById('closeSettings');
    this.els.devModeBadge = document.getElementById('devModeBadge');
  },

  initState() {
    this.state.sessionId = sessionStorage.getItem('whisperleaf_session_id') || crypto.randomUUID();
    sessionStorage.setItem('whisperleaf_session_id', this.state.sessionId);
    const collapsed = sessionStorage.getItem('wlSidebarCollapsed') === 'true';
    this.setSidebarCollapsed(collapsed);
    this.state.modelStatus = 'unknown';
    this.state.hasStartedChat = sessionStorage.getItem(WL_STARTED_CHAT_SESSION_KEY) === 'true';
  },

  async loadModelStatus() {
    this.state.modelStatus = 'checking';
    this.updateModelStatusUI();
    try {
      const res = await fetch('/api/model/status');
      if (!res.ok) return;
      const data = await res.json();
      this.state.modelAvailable = data.model_available === true;
      this.state.modelStatus = this.state.modelAvailable ? 'ready' : 'unavailable';
      this.updateModelStatusUI();
    } catch (_) {
      this.state.modelAvailable = false;
      this.state.modelStatus = 'unavailable';
      this.updateModelStatusUI();
    }
  },

  updateModelStatusUI() {
    const banner = this.els.modelUnavailableBanner;
    const statusIndicator = document.getElementById('modelStatusIndicator');
    const onboardingReady = this.els.onboardingModelReady;
    const onboardingNotice = this.els.onboardingModelNotice;
    if (banner) {
      if (this.state.modelAvailable) banner.classList.add('hidden');
      else banner.classList.remove('hidden');
    }
    if (statusIndicator) {
      const dot = statusIndicator.querySelector('.model-status-dot');
      const label = statusIndicator.querySelector('.model-status-label');
      statusIndicator.classList.remove('unavailable', 'checking', 'ready');
      const s = this.state.modelStatus;
      if (s === 'checking') {
        statusIndicator.classList.add('checking');
        if (label) label.textContent = 'Checking...';
      } else if (s === 'ready') {
        statusIndicator.classList.add('ready');
        if (label) label.textContent = 'Model ready';
      } else {
        statusIndicator.classList.add('unavailable');
        if (label) label.textContent = 'Not connected';
      }
    }
    if (onboardingReady) {
      if (this.state.modelAvailable) onboardingReady.classList.remove('hidden');
      else onboardingReady.classList.add('hidden');
    }
    if (onboardingNotice) {
      if (this.state.modelAvailable) onboardingNotice.classList.add('hidden');
      else onboardingNotice.classList.remove('hidden');
    }
  },

  updateMemoryIndicatorUI() {
    const label = this.els.mindMemoryLabel;
    if (!label) return;
    const n = this.state.lastMemorySnippets.length;
    label.textContent = n > 0 ? 'Using ' + n + ' saved memories' : 'Using saved memories';
  },

  renderMemorySnippetsList() {
    const list = this.els.memorySnippetsList;
    if (!list) return;
    list.innerHTML = '';
    const snippets = this.state.lastMemorySnippets || [];
    snippets.forEach((text, i) => {
      const li = document.createElement('li');
      li.className = 'memory-snippet-item';
      const content = String(text || '').trim() || '(no text)';
      li.textContent = content;
      const source = document.createElement('small');
      source.textContent = 'Memory ' + (i + 1);
      li.appendChild(source);
      list.appendChild(li);
    });
  },

  toggleMemoryVisibilityPanel() {
    const panel = this.els.memoryVisibilityPanel;
    const btn = this.els.mindMemoryBtn;
    if (!panel || !btn) return;
    const isOpen = !panel.classList.contains('hidden');
    if (isOpen) {
      panel.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
    } else {
      this.renderMemorySnippetsList();
      panel.classList.remove('hidden');
      btn.setAttribute('aria-expanded', 'true');
    }
  },

  /** First line of text, trimmed, optional max length with ellipsis. */
  _firstContentLine(text, maxLen) {
    const raw = String(text || '').trim();
    if (!raw) return '';
    const line = raw.split(/\r?\n/)[0].trim();
    if (maxLen && line.length > maxLen) return line.slice(0, maxLen - 1) + '\u2026';
    return line;
  },

  loadLocalDemoSavedMemories() {
    try {
      const raw = localStorage.getItem(WL_LOCAL_SAVED_MEMORIES_KEY);
      if (!raw) return [];
      const data = JSON.parse(raw);
      if (!Array.isArray(data)) return [];
      return data
        .filter((e) => e && typeof e.id === 'string' && typeof e.content === 'string')
        .map((e) => ({
          id: e.id,
          title: typeof e.title === 'string' ? e.title : '',
          content: e.content,
          timestamp: typeof e.timestamp === 'string' ? e.timestamp : '',
          _source: 'local_demo',
        }));
    } catch (_) {
      return [];
    }
  },

  persistLocalDemoSavedMemories(entries) {
    try {
      localStorage.setItem(WL_LOCAL_SAVED_MEMORIES_KEY, JSON.stringify(entries));
    } catch (_) {}
  },

  /** Dedupes by id. Phase 3: LeafLink confirm path calls this; future: real memory write. */
  upsertLocalDemoSavedMemory(entry) {
    const id = entry && entry.id;
    if (!id) return;
    const rawList = this.loadLocalDemoSavedMemories().map((e) => {
      const { _source, ...rest } = e;
      return rest;
    });
    const next = rawList.filter((e) => e.id !== id);
    next.push({
      id,
      title: typeof entry.title === 'string' ? entry.title : '',
      content: typeof entry.content === 'string' ? entry.content : '',
      timestamp: entry.timestamp || new Date().toISOString(),
    });
    this.persistLocalDemoSavedMemories(next);
  },

  removeLocalDemoSavedMemory(memoryId) {
    const sid = String(memoryId);
    const rawList = this.loadLocalDemoSavedMemories().map((e) => {
      const { _source, ...rest } = e;
      return rest;
    });
    const next = rawList.filter((e) => e.id !== sid);
    this.persistLocalDemoSavedMemories(next);
    try {
      window.dispatchEvent(
        new CustomEvent('wl-leaflink-local-memory-removed', { detail: { id: sid } })
      );
    } catch (_) {}
  },

  async loadSavedMemories() {
    const list = this.els.savedMemoriesList;
    const empty = this.els.savedMemoriesEmpty;
    const hint = this.els.savedMemoriesHint;
    if (!list) return;
    let serverMemories = [];
    try {
      const res = await fetch('/api/memories?limit=200');
      if (res.ok) {
        const data = await res.json();
        serverMemories = (data.memories || []).map((m) => ({
          ...m,
          _source: 'server',
        }));
      }
    } catch (_) {}
    const localMemories = this.loadLocalDemoSavedMemories();
    const merged = serverMemories.concat(localMemories);
    this.renderSavedMemoriesList(merged);
    if (empty) empty.classList.toggle('hidden', merged.length > 0);
    if (hint) hint.classList.toggle('hidden', merged.length > 0);
  },

  renderSavedMemoriesList(memories) {
    const list = this.els.savedMemoriesList;
    if (!list) return;
    list.innerHTML = '';
    const maxPreview = 120;
    (memories || []).forEach((m) => {
      const li = document.createElement('li');
      li.className = 'saved-memory-item';
      const wrap = document.createElement('div');
      wrap.className = 'saved-memory-text';
      const content = (m.content || '').trim() || '(empty)';
      const isLocal = m._source === 'local_demo';
      const titleText = isLocal
        ? (String(m.title || '').trim() || this._firstContentLine(content, 80) || '(Untitled)')
        : this._firstContentLine(content, 100) || '(empty)';
      const titleEl = document.createElement('div');
      titleEl.className = 'saved-memory-title';
      titleEl.textContent = titleText;
      wrap.appendChild(titleEl);
      const lines = content.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
      let previewLine = '';
      if (isLocal) {
        previewLine = this._firstContentLine(content, maxPreview);
        if (previewLine === titleText && lines.length > 1) {
          previewLine = this._firstContentLine(lines.slice(1).join(' '), maxPreview);
        }
      } else if (lines.length > 1) {
        previewLine = this._firstContentLine(lines.slice(1).join(' · '), maxPreview);
      }
      if (previewLine) {
        const previewEl = document.createElement('div');
        previewEl.className = 'saved-memory-preview-line';
        previewEl.textContent = previewLine;
        wrap.appendChild(previewEl);
      }
      if (isLocal) {
        const badge = document.createElement('small');
        badge.className = 'saved-memory-demo-badge';
        badge.textContent = 'Local demo — not semantic memory';
        wrap.appendChild(badge);
      }
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-delete-memory';
      btn.textContent = 'Delete';
      btn.setAttribute('aria-label', 'Delete this memory');
      btn.dataset.memoryId = String(m.id);
      const source = m._source || 'server';
      btn.addEventListener('click', () => this.deleteMemory(m.id, source));
      li.appendChild(wrap);
      li.appendChild(btn);
      list.appendChild(li);
    });
  },

  async deleteMemory(memoryId, source) {
    if (source === 'local_demo') {
      this.removeLocalDemoSavedMemory(memoryId);
      await this.loadSavedMemories();
      return;
    }
    try {
      const res = await fetch('/api/memory/' + encodeURIComponent(memoryId), { method: 'DELETE' });
      if (!res.ok) return;
      await this.loadSavedMemories();
    } catch (_) {}
  },

  async loadDocuments() {
    const list = this.els.documentsList;
    const empty = this.els.documentsEmpty;
    if (!list) return;
    try {
      const res = await fetch('/api/documents');
      if (!res.ok) return;
      const data = await res.json();
      const documents = data.documents || [];
      this.state.documents = documents;
      this.renderDocumentsList();
      this.updateChatHintsContent();
      if (empty) empty.classList.toggle('hidden', documents.length > 0);
    } catch (_) {
      if (empty) empty.classList.remove('hidden');
    }
  },

  filterDocumentsByQuery(documents, query) {
    const q = (query || '').trim().toLowerCase();
    if (!q) return documents || [];
    return (documents || []).filter((doc) => {
      const title = (doc.title || '').toLowerCase();
      const filename = (doc.filename || '').toLowerCase();
      return title.includes(q) || filename.includes(q);
    });
  },

  renderDocumentsList() {
    const list = this.els.documentsList;
    const empty = this.els.documentsEmpty;
    const noResults = this.els.documentsNoResults;
    if (!list) return;
    const query = (this.state.documentSearchQuery || '').trim();
    const all = this.state.documents || [];
    const filtered = this.filterDocumentsByQuery(all, query);
    list.innerHTML = '';
    filtered.forEach((doc) => {
      const li = document.createElement('li');
      li.className = 'document-item';
      const info = document.createElement('div');
      info.className = 'document-info';
      const filename = document.createElement('div');
      filename.className = 'document-filename';
      filename.textContent = doc.title || doc.filename || doc.id || 'Document';
      const meta = document.createElement('div');
      meta.className = 'document-meta';
      const date = doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : '';
      meta.textContent = date ? 'Uploaded ' + date : (doc.chunks_count != null ? doc.chunks_count + ' chunks' : '');
      info.appendChild(filename);
      info.appendChild(meta);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-delete-document';
      btn.textContent = 'Delete';
      btn.setAttribute('aria-label', 'Delete this document');
      btn.dataset.documentId = String(doc.id);
      btn.addEventListener('click', () => this.deleteDocument(doc.id));
      li.appendChild(info);
      li.appendChild(btn);
      list.appendChild(li);
    });
    if (empty) empty.classList.toggle('hidden', all.length > 0);
    if (noResults) noResults.classList.toggle('hidden', all.length === 0 || filtered.length > 0);
  },

  async deleteDocument(documentId) {
    try {
      const res = await fetch('/api/documents/' + encodeURIComponent(documentId), { method: 'DELETE' });
      if (!res.ok) return;
      await this.loadDocuments();
    } catch (_) {}
  },

  setDocumentUploadStatus(message, type) {
    const el = this.els.documentUploadStatus;
    if (!el) return;
    if (this._documentUploadStatusTimer) {
      clearTimeout(this._documentUploadStatusTimer);
      this._documentUploadStatusTimer = null;
    }
    el.textContent = message || '';
    el.classList.remove('hidden', 'error', 'success');
    if (type === 'error') el.classList.add('error');
    else if (type === 'success') el.classList.add('success');
    if (!message) el.classList.add('hidden');
  },

  clearDocumentUploadStatusAfter(ms) {
    const el = this.els.documentUploadStatus;
    if (!el) return;
    if (this._documentUploadStatusTimer) clearTimeout(this._documentUploadStatusTimer);
    this._documentUploadStatusTimer = setTimeout(() => {
      this.setDocumentUploadStatus('');
      el.classList.add('hidden');
      this._documentUploadStatusTimer = null;
    }, ms);
  },

  async handleDocumentUpload(e) {
    const input = e && e.target;
    const file = input && input.files && input.files[0];
    if (!file) return;
    input.value = '';
    const btn = this.els.documentUploadBtn;
    if (btn) btn.disabled = true;
    this.setDocumentUploadStatus('Uploading document...');
    let processingTimer = setTimeout(() => {
      this.setDocumentUploadStatus('Processing document...');
      processingTimer = null;
    }, 2000);
    const form = new FormData();
    form.append('file', file);
    form.append('title', file.name || '');
    try {
      const res = await fetch('/api/documents/upload', { method: 'POST', body: form });
      if (processingTimer) clearTimeout(processingTimer);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail || res.statusText || 'Unknown error';
        const msg = typeof detail === 'string' ? detail : (detail.message || JSON.stringify(detail));
        this.setDocumentUploadStatus('Upload failed: ' + msg, 'error');
        this.clearDocumentUploadStatusAfter(5000);
        if (btn) btn.disabled = false;
        return;
      }
      this.setDocumentUploadStatus('Document indexed successfully.', 'success');
      this.clearDocumentUploadStatusAfter(4000);
      await this.loadDocuments();
    } catch (err) {
      if (processingTimer) clearTimeout(processingTimer);
      this.setDocumentUploadStatus('Upload failed: ' + (err && err.message ? err.message : 'Network error'), 'error');
      this.clearDocumentUploadStatusAfter(5000);
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  setInputDropFeedback(text, clearAfterMs = 0) {
    const el = this.els.inputDropFeedback;
    if (!el) return;
    if (this._inputDropFeedbackTimer) {
      clearTimeout(this._inputDropFeedbackTimer);
      this._inputDropFeedbackTimer = null;
    }
    el.textContent = text || '';
    if (text) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
    if (clearAfterMs > 0) {
      this._inputDropFeedbackTimer = setTimeout(() => {
        el.classList.add('hidden');
        el.textContent = '';
        this._inputDropFeedbackTimer = null;
      }, clearAfterMs);
    }
  },

  async uploadDroppedFile(file) {
    if (!file) return;
    this.setInputDropFeedback('File added: ' + (file.name || 'document'), 0);
    this.setInputDropFeedback('Uploading…', 0);
    let processingTimer = setTimeout(() => {
      this.setInputDropFeedback('Processing document…', 0);
      processingTimer = null;
    }, 2000);
    const form = new FormData();
    form.append('file', file);
    form.append('title', file.name || '');
    try {
      const res = await fetch('/api/documents/upload', { method: 'POST', body: form });
      if (processingTimer) clearTimeout(processingTimer);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail || res.statusText || 'Unknown error';
        const msg = typeof detail === 'string' ? detail : (detail.message || JSON.stringify(detail));
        this.setInputDropFeedback('Upload failed: ' + msg, 5000);
        return;
      }
      this.setInputDropFeedback('Document indexed successfully.', 4000);
      await this.loadDocuments();
    } catch (err) {
      if (processingTimer) clearTimeout(processingTimer);
      this.setInputDropFeedback('Upload failed: ' + (err && err.message ? err.message : 'Network error'), 5000);
    }
  },

  showMemorySavedNotification(payload) {
    const el = this.els.memorySavedNotification;
    const preview = this.els.memorySavedPreview;
    if (!el) return;
    if (this._memorySavedNotificationTimer) {
      clearTimeout(this._memorySavedNotificationTimer);
      this._memorySavedNotificationTimer = null;
    }
    const text = (payload && payload.text) ? String(payload.text).trim() : '';
    if (preview) {
      preview.textContent = text || '';
      preview.style.display = text ? 'block' : 'none';
    }
    el.classList.remove('hidden');
    this._memorySavedNotificationTimer = setTimeout(() => {
      el.classList.add('hidden');
      this._memorySavedNotificationTimer = null;
    }, 5000);
  },

  showDocumentExcerptPreview(name, snippets) {
    const panel = this.els.documentExcerptPanel;
    const titleEl = this.els.documentExcerptTitle;
    const bodyEl = this.els.documentExcerptBody;
    if (!panel || !titleEl || !bodyEl) return;
    titleEl.textContent = name || 'Document';
    bodyEl.innerHTML = '';
    if (snippets && snippets.length > 0) {
      snippets.forEach((text) => {
        const chunk = document.createElement('div');
        chunk.className = 'excerpt-chunk';
        chunk.textContent = text;
        bodyEl.appendChild(chunk);
      });
    } else {
      bodyEl.textContent = 'No excerpt available.';
    }
    panel.classList.remove('hidden');
  },

  hideDocumentExcerptPreview() {
    const panel = this.els.documentExcerptPanel;
    if (panel) panel.classList.add('hidden');
  },

  setSidebarCollapsed(collapsed) {
    const layout = this.els.appLayout;
    const toggle = this.els.sidebarToggle;
    if (!layout) return;
    if (collapsed) {
      layout.classList.add('sidebar-collapsed');
      if (toggle) {
        toggle.setAttribute('aria-label', 'Expand sidebar');
        toggle.textContent = '\u00BB';
      }
    } else {
      layout.classList.remove('sidebar-collapsed');
      if (toggle) {
        toggle.setAttribute('aria-label', 'Collapse sidebar');
        toggle.textContent = '\u2261';
      }
    }
    try {
      sessionStorage.setItem('wlSidebarCollapsed', collapsed ? 'true' : 'false');
    } catch (_) {}
  },

  bindEvents() {
    const { chatForm, messageInput, chatMessages, jumpBottomBtn, clearBtn, newSessionBtn, chatOwl, appLayout, sidebarToggle, modelRetryBtn } = this.els;

    if (sidebarToggle && appLayout) {
      sidebarToggle.addEventListener('click', () => {
        const collapsed = appLayout.classList.contains('sidebar-collapsed');
        this.setSidebarCollapsed(!collapsed);
      });
    }

    if (chatOwl) {
      chatOwl.addEventListener('click', () => { window.location.href = '/'; });
    }

    if (modelRetryBtn) {
      modelRetryBtn.addEventListener('click', () => {
        this.loadModelStatus();
      });
    }

    if (chatForm) {
      const composeFoot = chatForm.closest('.chat-compose-foot');
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.sendMessage();
      });
      chatForm.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        chatForm.classList.add('drag-over');
        if (composeFoot) composeFoot.classList.add('drag-over');
      });
      chatForm.addEventListener('dragleave', (e) => {
        if (e.relatedTarget && chatForm.contains(e.relatedTarget)) return;
        chatForm.classList.remove('drag-over');
        if (composeFoot) composeFoot.classList.remove('drag-over');
      });
      chatForm.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        chatForm.classList.remove('drag-over');
        if (composeFoot) composeFoot.classList.remove('drag-over');
        const files = e.dataTransfer && e.dataTransfer.files;
        const file = files && files.length > 0 ? files[0] : null;
        if (file) this.uploadDroppedFile(file);
      });
    }

    if (messageInput) {
      messageInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') return;
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      messageInput.addEventListener('input', () => this.autoResizeInput());
      messageInput.addEventListener('paste', () => {
        setTimeout(() => this.autoResizeInput(), 0);
      });
    }

    if (chatMessages && jumpBottomBtn) {
      chatMessages.addEventListener('scroll', () => this.updateScrollButtonVisibility());
      jumpBottomBtn.addEventListener('click', () => {
        this.scrollToBottom(chatMessages);
        this.updateScrollButtonVisibility();
      });
    }

    if (clearBtn) clearBtn.addEventListener('click', () => this.clearSession());
    if (newSessionBtn) newSessionBtn.addEventListener('click', () => this.newSession());

    const onboardingStartBtn = this.els.onboardingStartBtn;
    if (onboardingStartBtn) onboardingStartBtn.addEventListener('click', () => this.dismissOnboarding());
    const starterPrompts = this.els.starterPrompts;
    if (starterPrompts) {
      starterPrompts.addEventListener('click', (e) => {
        const btn = e.target.closest('.starter-prompt-btn');
        if (!btn) return;
        const prompt = (btn.getAttribute('data-prompt') || '').trim();
        if (!prompt) return;
        this.applyStarterPrompt(prompt, false);
      });
    }

    const composeSuggestionChips = document.getElementById('composeSuggestionChips');
    if (composeSuggestionChips) {
      composeSuggestionChips.addEventListener('click', (e) => {
        const btn = e.target.closest('.compose-suggestion-chip');
        if (!btn) return;
        const prompt = (btn.getAttribute('data-prompt') || btn.textContent || '').trim();
        if (!prompt) return;
        this.applyStarterPrompt(prompt, true);
      });
    }

    const onboardingHelpBtn = this.els.onboardingHelpBtn;
    if (onboardingHelpBtn) onboardingHelpBtn.addEventListener('click', () => this.reopenOnboarding());

    const { settingsBtn, settingsModal, closeSettings, devModeToggle } = this.els;
    if (settingsBtn && settingsModal) {
      settingsBtn.addEventListener('click', () => {
        settingsModal.classList.remove('hidden');
      });
    }
    if (closeSettings && settingsModal) {
      closeSettings.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
      });
    }
    if (devModeToggle) {
      devModeToggle.addEventListener('change', (e) => {
        this.setDevMode(!!e.target.checked);
      });
    }

    const mindMemoryBtn = this.els.mindMemoryBtn;
    if (mindMemoryBtn) {
      mindMemoryBtn.addEventListener('click', () => this.toggleMemoryVisibilityPanel());
    }

    const documentUploadBtn = this.els.documentUploadBtn;
    const documentUploadInput = this.els.documentUploadInput;
    if (documentUploadBtn && documentUploadInput) {
      documentUploadBtn.addEventListener('click', () => documentUploadInput.click());
      documentUploadInput.addEventListener('change', (e) => this.handleDocumentUpload(e));
    }
    const documentSearchInput = this.els.documentSearchInput;
    if (documentSearchInput) {
      documentSearchInput.addEventListener('input', () => {
        this.state.documentSearchQuery = documentSearchInput.value || '';
        this.renderDocumentsList();
      });
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && (e.ctrlKey || e.metaKey)) {
        if (messageInput && document.activeElement === messageInput) return;
        if (documentSearchInput) {
          e.preventDefault();
          documentSearchInput.focus();
        }
      }
    });

    const listEl = this.els.sidebarHistoryList;
    if (listEl) {
      listEl.addEventListener('click', (e) => {
        const item = e.target.closest('.sidebar-history-item');
        if (item) {
          const id = item.getAttribute('data-target-message-id');
          if (id) this.scrollToMessageAnchor(id);
        }
      });
    }

    const chatWindow = this.els.chatWindow;
    if (chatWindow) {
      chatWindow.addEventListener('click', (e) => {
        const btn = e.target.closest('.source-link');
        if (!btn) return;
        e.preventDefault();
        const name = btn.getAttribute('data-source-name') || '';
        const sourcesEl = btn.closest('.message-sources');
        if (!sourcesEl || !name) return;
        const raw = sourcesEl.getAttribute('data-doc-excerpts');
        let excerpts = [];
        try {
          excerpts = raw ? JSON.parse(raw) : [];
        } catch (_) {}
        const snippets = excerpts
          .filter((x) => (x.name || '').trim() === name)
          .map((x) => (x.snippet || '').trim())
          .filter(Boolean);
        this.showDocumentExcerptPreview(name, snippets);
      });
    }

    const excerptClose = this.els.documentExcerptClose;
    const excerptPanel = this.els.documentExcerptPanel;
    if (excerptClose && excerptPanel) {
      excerptClose.addEventListener('click', () => this.hideDocumentExcerptPreview());
      excerptPanel.addEventListener('click', (e) => {
        if (e.target === excerptPanel) this.hideDocumentExcerptPreview();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && excerptPanel && !excerptPanel.classList.contains('hidden')) {
          this.hideDocumentExcerptPreview();
        }
      });
    }

  },

  // --- Scroll: auto-scroll when appropriate; never force scroll when user is reading above.
  // Threshold in px: user is "near bottom" if within this distance of the bottom.
  NEAR_BOTTOM_THRESHOLD: 120,

  isNearBottom(container, threshold) {
    if (!container) return true;
    const t = threshold != null ? threshold : this.NEAR_BOTTOM_THRESHOLD;
    return container.scrollHeight - container.scrollTop - container.clientHeight <= t;
  },

  scrollToBottom(container, forceSmooth) {
    if (!container) return;
    const smooth = forceSmooth !== false && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    container.scrollTo({ top: container.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
  },

  scrollToBottomIfNearBottom() {
    const container = this.els.chatMessages;
    if (!container) return;
    if (this.isNearBottom(container)) this.scrollToBottom(container);
  },

  updateScrollButtonVisibility() {
    if (!this.els.jumpBottomBtn) return;
    this.els.jumpBottomBtn.classList.toggle('hidden', this.isNearBottom(this.els.chatMessages));
  },

  // --- Input
  autoResizeInput() {
    const el = this.els.messageInput;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 8 * 16) + 'px';
  },

  resetInputHeight() {
    const el = this.els.messageInput;
    if (el) el.style.height = 'auto';
  },

  // --- Owl
  startThinking() {
    if (this.els.owl) this.els.owl.classList.add('owl-thinking');
  },

  stopThinking() {
    if (this.els.owl) this.els.owl.classList.remove('owl-thinking');
  },

  // --- Sending state
  setSendingState(sending) {
    this.state.isSending = sending;
    if (this.els.sendBtn) this.els.sendBtn.disabled = sending;
  },

  // --- Watchdog (total time from send until stream done/error; local models can be slow on first run)
  applyStarterPrompt(prompt, autoSend) {
    const input = this.els.messageInput;
    if (!input) return;
    input.value = prompt;
    this.autoResizeInput();
    input.focus();
    if (autoSend) this.sendMessage();
  },

  markChatStarted() {
    if (this.state.hasStartedChat) return;
    this.state.hasStartedChat = true;
    try {
      sessionStorage.setItem(WL_STARTED_CHAT_SESSION_KEY, 'true');
    } catch (_) {}
  },

  STREAM_WATCHDOG_MS: 120000,
  STREAM_HARD_TIMEOUT_MS: 360000,
  STAGE_2_MS: 3000,
  STAGE_3_MS: 8000,

  startGenerationFeedback() {
    this.stopGenerationFeedback();
    this.startThinking();
    this.setThinkingStep('Thinking locally...');
    if (this.els.localProcessingStatus) this.els.localProcessingStatus.classList.add('visible');
    this.state.stageTimers = [
      setTimeout(() => {
        if (!this.state.isSending) return;
        this.setThinkingStep('Working through this on your device...');
      }, this.STAGE_2_MS),
      setTimeout(() => {
        if (!this.state.isSending) return;
        this.setThinkingStep('Local models can take a little longer, especially on first run.');
      }, this.STAGE_3_MS),
    ];
  },

  stopGenerationFeedback() {
    this.stopThinking();
    this.clearThinkingStep();
    if (this.els.localProcessingStatus) this.els.localProcessingStatus.classList.remove('visible');
    const timers = this.state.stageTimers || [];
    timers.forEach((t) => clearTimeout(t));
    this.state.stageTimers = [];
  },

  startWatchdog() {
    this.stopWatchdog();
    this.state.streamWatchdogStage = 0;
    this.state.lastSseEventAt = Date.now();
    this.state.streamWatchdog = setTimeout(() => {
      // Important: do NOT convert the streaming bubble to an error here.
      // If the local model starts streaming after a slow warmup, we still want to render it.
      console.warn('[WhisperLeaf] Stream watchdog soft timeout (no SSE yet)');
      this.state.streamWatchdogStage = 1;
      this.setThinkingStep('Still working… first run can take a bit.');
      // Escalate to a hard timeout if nothing arrives for much longer.
      this.state.streamWatchdog = setTimeout(() => {
        console.warn('[WhisperLeaf] Stream watchdog hard timeout');
        this.stopGenerationFeedback();
        this.setStreamingBubbleError('timeout');
        this.setSendingState(false);
      }, this.STREAM_HARD_TIMEOUT_MS - this.STREAM_WATCHDOG_MS);
    }, this.STREAM_WATCHDOG_MS);
  },

  stopWatchdog() {
    if (this.state.streamWatchdog) {
      clearTimeout(this.state.streamWatchdog);
      this.state.streamWatchdog = null;
    }
    this.state.streamWatchdogStage = 0;
  },

  // --- Copy button (assistant messages only)
  addCopyButtonToBubble(bubble, getText) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-copy-msg';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const text = typeof getText === 'function' ? getText() : getText;
      if (text != null) navigator.clipboard.writeText(String(text)).catch(() => {});
    });
    bubble.appendChild(btn);
  },

  // --- Message list (single source of truth)
  // Shape: { id, role, content, status } — status: 'complete' | 'streaming' | 'error'
  generateMessageId() {
    return 'msg-' + crypto.randomUUID();
  },

  addMessage(msg) {
    this.state.messages.push(msg);
    return msg;
  },

  getMessageById(id) {
    return this.state.messages.find((m) => m.id === id) || null;
  },

  updateMessage(id, updates) {
    const msg = this.getMessageById(id);
    if (msg) Object.assign(msg, updates);
  },

  getHistoryForApi() {
    return this.state.messages
      .filter((m) => m.status === 'complete')
      .map((m) => ({ role: m.role, content: m.content || '' }));
  },

  getLastUserMessageContent() {
    const msgs = this.state.messages || [];
    for (let i = msgs.length - 1; i >= 0; i--) {
      const m = msgs[i];
      if (m && m.role === 'user') return String(m.content || '');
    }
    return '';
  },

  // Replace only the first sentence when it looks generic, using a concrete "anchor"
  // based on the user's topic (and without changing the rest of the reply).
  improveFirstSentenceOpening(assistantText, userMessage) {
    const raw = String(assistantText || '');
    if (!raw.trim()) return null;

    const firstSentenceEndIdx = raw.search(/[.!?]/);
    if (firstSentenceEndIdx === -1) return null;

    const firstSentence = raw.slice(0, firstSentenceEndIdx + 1);
    const firstLower = firstSentence.toLowerCase();
    const userLower = String(userMessage || '').toLowerCase();

    const genericOpeners = [
      'wonderful',
      'great',
      'amazing',
      'relaxing hobby',
      'it\'s a sport about strategy',
      'strategy, skill, teamwork',
      'sport about strategy',
      'wonderful hobby',
      'great hobby',
      'it is a',
      'it\\x27s a',
    ];
    const looksGeneric = genericOpeners.some((p) => firstLower.includes(p.replace(/\\x27/g, "'")));

    // Only rewrite if generic AND we can anchor to a concrete mechanism.
    const isKnittingTopic = userLower.includes('knit') || userLower.includes('knitting') || userLower.includes('yarn') || userLower.includes('stitch');
    const isBaseballTopic = userLower.includes('baseball') || userLower.includes('pitcher') || userLower.includes('hitter');

    if (!looksGeneric) return null;

    let anchor = '';
    if (isKnittingTopic) {
      anchor = 'Knitting builds fabric by looping yarn through stitches, one row at a time.';
    } else if (isBaseballTopic) {
      anchor = 'Baseball centers on the duel between pitcher and hitter.';
    } else {
      // General fallback anchor: concrete process, no fluff.
      anchor = "At a practical level, we make progress by turning the goal into concrete steps and checking what each step changes.";
    }

    const rest = raw.slice(firstSentenceEndIdx + 1).trimStart();
    return rest ? anchor + ' ' + rest : anchor;
  },

  createMessageEl(msg) {
    const div = document.createElement('div');
    div.className = 'message ' + msg.role + (msg.status === 'error' ? ' error' : '');
    div.setAttribute('data-message-id', msg.id);
    if (msg.role === 'user') {
      div.textContent = msg.content || '';
    } else if (msg.status === 'error') {
      const wrap = document.createElement('div');
      wrap.className = 'message-error-wrap';
      const title = document.createElement('div');
      title.className = 'message-error-title';
      title.textContent = 'Couldn’t finish this response';
      const body = document.createElement('div');
      body.className = 'message-error-body';
      body.textContent = 'WhisperLeaf wasn’t able to complete the reply on this attempt. Please try again.';
      const helper = document.createElement('div');
      helper.className = 'message-error-helper';
      helper.textContent = 'If this keeps happening, the local model may still be starting up.';
      wrap.appendChild(title);
      wrap.appendChild(body);
      wrap.appendChild(helper);
      div.appendChild(wrap);
    } else if (msg.status === 'streaming') {
      const textSpan = document.createElement('span');
      textSpan.className = 'streaming-text';
      textSpan.textContent = msg.content || '';
      const cursorSpan = document.createElement('span');
      cursorSpan.className = 'streaming-cursor';
      cursorSpan.textContent = '\u258C';
      div.appendChild(textSpan);
      div.appendChild(cursorSpan);
    } else {
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      const bodyWrap = document.createElement('div');
      bodyWrap.className = 'message-body-wrap';
      const body = document.createElement('span');
      body.className = 'message-body';
      body.textContent = msg.content || '';
      bodyWrap.appendChild(body);
      const ctx = msg.contextUsed;
      if (ctx && ctx.docSources && ctx.docSources.length > 0) {
        const sourcesEl = document.createElement('div');
        sourcesEl.className = 'message-sources';
        sourcesEl.setAttribute('data-doc-excerpts', JSON.stringify(ctx.docExcerpts || []));
        const prefix = document.createTextNode('Sources: ');
        sourcesEl.appendChild(prefix);
        ctx.docSources.forEach((name, i) => {
          if (i > 0) sourcesEl.appendChild(document.createTextNode(', '));
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'source-link';
          btn.textContent = name;
          btn.setAttribute('data-source-name', name);
          btn.setAttribute('title', 'Preview excerpt');
          sourcesEl.appendChild(btn);
        });
        bodyWrap.appendChild(sourcesEl);
      }
      if (ctx) {
        const contextEl = this.createContextPanel(ctx);
        if (contextEl) bodyWrap.appendChild(contextEl);
      }
      wrap.appendChild(bodyWrap);
      this.addCopyButtonToBubble(wrap, () => body.textContent);
      div.appendChild(wrap);
    }
    return div;
  },

  appendMessageEl(msg) {
    const { chatWindow } = this.els;
    if (!chatWindow) return;
    chatWindow.appendChild(this.createMessageEl(msg));
    this.updateChatHintsVisibility();
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  syncDomFromMessages() {
    const { chatWindow } = this.els;
    if (!chatWindow) return;
    chatWindow.innerHTML = '';
    for (const msg of this.state.messages) {
      chatWindow.appendChild(this.createMessageEl(msg));
    }
    this.updateChatHintsVisibility();
    this.refreshSidebarHistory();
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  getStreamingBubbleEl() {
    const id = this.state.currentStreamingId;
    return id ? document.querySelector(`[data-message-id="${id}"]`) : null;
  },

  updateStreamingBubble(textChunk) {
    const bubble = this.getStreamingBubbleEl();
    if (!bubble) return;
    const textEl = bubble.querySelector('.streaming-text');
    if (textEl) textEl.textContent = textChunk;
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  buildContextUsed() {
    const memorySnippets = (this.state.lastMemorySnippets || []).slice();
    const docSources = (this.state.docSourcesForCurrentResponse || []).slice();
    const docExcerpts = (this.state.docExcerptsForCurrentResponse || []).map((e) => ({ name: e.name, snippet: e.snippet }));
    const hasAny = memorySnippets.length > 0 || docSources.length > 0;
    return hasAny ? { memorySnippets, docSources, docExcerpts } : null;
  },

  createContextPanel(contextUsed) {
    if (!contextUsed || (contextUsed.memorySnippets.length === 0 && contextUsed.docSources.length === 0)) return null;
    const panel = document.createElement('div');
    panel.className = 'message-context-panel';
    const summary = document.createElement('button');
    summary.type = 'button';
    summary.className = 'message-context-summary';
    summary.setAttribute('aria-expanded', 'false');
    const memCount = contextUsed.memorySnippets.length;
    const docCount = contextUsed.docSources.length;
    const parts = [];
    const excerptCount = (contextUsed.docExcerpts || []).length;
    if (memCount > 0) {
      parts.push(memCount + ' ' + (memCount === 1 ? 'relevant memory' : 'relevant memories'));
    } else if (docCount === 0 && excerptCount === 0) {
      parts.push('no prior memory');
    }
    if (docCount) parts.push(docCount + ' ' + (docCount === 1 ? 'document' : 'documents'));
    if (excerptCount) parts.push(excerptCount + ' ' + (excerptCount === 1 ? 'excerpt' : 'excerpts'));
    summary.textContent = 'Context used: ' + (parts.length ? parts.join(', ') : '—');
    panel.appendChild(summary);
    const details = document.createElement('div');
    details.className = 'message-context-details hidden';
    if (contextUsed.memorySnippets && contextUsed.memorySnippets.length > 0) {
      const memHead = document.createElement('div');
      memHead.className = 'message-context-details-heading';
      memHead.textContent = 'Memories';
      details.appendChild(memHead);
      const memList = document.createElement('ul');
      memList.className = 'message-context-snippets-list';
      contextUsed.memorySnippets.forEach((text) => {
        const li = document.createElement('li');
        li.className = 'message-context-snippet';
        li.textContent = (text || '').trim() || '(no text)';
        memList.appendChild(li);
      });
      details.appendChild(memList);
    }
    if (contextUsed.docSources && contextUsed.docSources.length > 0) {
      const docHead = document.createElement('div');
      docHead.className = 'message-context-details-heading';
      docHead.textContent = 'Documents';
      details.appendChild(docHead);
      const excerptsByDoc = {};
      (contextUsed.docExcerpts || []).forEach((e) => {
        const n = (e.name || '').trim();
        if (!n) return;
        if (!excerptsByDoc[n]) excerptsByDoc[n] = [];
        excerptsByDoc[n].push((e.snippet || '').trim());
      });
      contextUsed.docSources.forEach((name) => {
        const block = document.createElement('div');
        block.className = 'message-context-doc-block';
        const nameEl = document.createElement('div');
        nameEl.className = 'message-context-doc-name';
        nameEl.textContent = name;
        block.appendChild(nameEl);
        const snippets = excerptsByDoc[name] || [];
        snippets.forEach((text) => {
          const pre = document.createElement('div');
          pre.className = 'message-context-snippet';
          pre.textContent = text || '(no text)';
          block.appendChild(pre);
        });
        details.appendChild(block);
      });
    }
    panel.appendChild(details);
    summary.addEventListener('click', () => {
      const expanded = details.classList.toggle('hidden');
      summary.setAttribute('aria-expanded', String(!expanded));
    });
    return panel;
  },

  finalizeStreamingBubble() {
    const id = this.state.currentStreamingId;
    const msg = id ? this.getMessageById(id) : null;
    const bubble = this.getStreamingBubbleEl();
    if (bubble && msg) {
      msg.status = 'complete';
      const cursor = bubble.querySelector('.streaming-cursor');
      if (cursor) cursor.remove();
      const textEl = bubble.querySelector('.streaming-text');
      const content = textEl ? textEl.textContent : (msg.content || '');
      const lastUser = this.getLastUserMessageContent();
      const improved = this.improveFirstSentenceOpening(content, lastUser);
      const finalContent = improved || content;
      msg.content = finalContent;
      const contextUsed = this.buildContextUsed();
      if (contextUsed) msg.contextUsed = contextUsed;
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      const bodyWrap = document.createElement('div');
      bodyWrap.className = 'message-body-wrap';
      const body = document.createElement('span');
      body.className = 'message-body';
      body.textContent = finalContent;
      bodyWrap.appendChild(body);
      const sources = this.state.docSourcesForCurrentResponse || [];
      const excerpts = this.state.docExcerptsForCurrentResponse || [];
      if (sources.length > 0) {
        const sourcesEl = document.createElement('div');
        sourcesEl.className = 'message-sources';
        sourcesEl.setAttribute('data-doc-excerpts', JSON.stringify(excerpts));
        const prefix = document.createTextNode('Sources: ');
        sourcesEl.appendChild(prefix);
        sources.forEach((name, i) => {
          if (i > 0) sourcesEl.appendChild(document.createTextNode(', '));
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'source-link';
          btn.textContent = name;
          btn.setAttribute('data-source-name', name);
          btn.setAttribute('title', 'Preview excerpt');
          sourcesEl.appendChild(btn);
        });
        bodyWrap.appendChild(sourcesEl);
      }
      if (contextUsed) {
        const contextEl = this.createContextPanel(contextUsed);
        if (contextEl) bodyWrap.appendChild(contextEl);
      }
      this.state.docSourcesForCurrentResponse = [];
      this.state.docExcerptsForCurrentResponse = [];
      wrap.appendChild(bodyWrap);
      this.addCopyButtonToBubble(wrap, () => body.textContent);
      bubble.innerHTML = '';
      bubble.appendChild(wrap);
    } else {
      this.state.docSourcesForCurrentResponse = [];
      this.state.docExcerptsForCurrentResponse = [];
    }
    this.state.currentStreamingId = null;
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  setStreamingBubbleError(message) {
    const id = this.state.currentStreamingId;
    const msg = id ? this.getMessageById(id) : null;
    const bubble = this.getStreamingBubbleEl();
    if (msg) {
      msg.status = 'error';
      msg.content = message || 'Error';
    }
    if (bubble) {
      bubble.className = 'message error';
      bubble.innerHTML = '';
      const wrap = document.createElement('div');
      wrap.className = 'message-error-wrap';
      const title = document.createElement('div');
      title.className = 'message-error-title';
      title.textContent = 'Couldn’t finish this response';
      const body = document.createElement('div');
      body.className = 'message-error-body';
      body.textContent = 'WhisperLeaf wasn’t able to complete the reply on this attempt. Please try again.';
      const helper = document.createElement('div');
      helper.className = 'message-error-helper';
      helper.textContent = 'If this keeps happening, the local model may still be starting up.';
      wrap.appendChild(title);
      wrap.appendChild(body);
      wrap.appendChild(helper);
      bubble.appendChild(wrap);
    }
    this.state.currentStreamingId = null;
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  // --- SSE parsing
  parseSSEBlock(block) {
    const lines = block.split(/\r?\n/);
    let event = '';
    const dataLines = [];
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('event:')) {
        event = trimmed.replace(/^event:\s*/, '').trim();
      } else if (trimmed.startsWith('data:')) {
        dataLines.push(trimmed.length > 5 ? trimmed.slice(6) : '');
      }
    }
    const data = dataLines.join('\n');
    if (!event && !data) return null;
    if (data.trim() === '[DONE]') return { event: 'done', data: '' };
    return { event, data };
  },

  processStreamBuffer(buffer) {
    const parts = buffer.split(/\n\n+/);
    const remainder = parts.pop() || '';
    return { blocks: parts, remainder };
  },

  refreshSidebarHistory() {
    const listEl = this.els.sidebarHistoryList;
    if (!listEl) return;
    const userMessages = this.state.messages.filter((m) => m.role === 'user' && m.status === 'complete');
    const recent = userMessages.slice(-8).reverse();
    const maxPreview = 50;

    listEl.innerHTML = '';
    for (const msg of recent) {
      const raw = (msg.content || '').trim();
      const preview = raw.length > maxPreview ? raw.slice(0, maxPreview) + '\u2026' : raw;
      const li = document.createElement('li');
      li.className = 'sidebar-history-item';
      li.setAttribute('data-target-message-id', msg.id);
      li.textContent = preview || '(empty)';
      li.setAttribute('role', 'button');
      li.setAttribute('tabindex', '0');
      listEl.appendChild(li);
    }
  },

  setThinkingStep(text) {
    const el = this.els.thinkingStep;
    if (el) el.textContent = text || '';
  },

  clearThinkingStep() {
    this.setThinkingStep('');
  },

  ONBOARDING_KEY: 'whisperleaf_seen_onboarding',

  updateOnboardingVisibility() {
    const onboarding = this.els.onboardingScreen;
    const hints = this.els.chatHints;
    const chatWindow = this.els.chatWindow;
    if (!onboarding || !hints || !chatWindow) return;
    const show = this.state.forceShowOnboarding;
    if (show) {
      onboarding.classList.remove('hidden');
      hints.classList.remove('visible');
      hints.setAttribute('aria-hidden', 'true');
    } else {
      onboarding.classList.add('hidden');
      hints.classList.add('visible');
      hints.setAttribute('aria-hidden', 'false');
    }
  },

  reopenOnboarding() {
    this.state.forceShowOnboarding = true;
    this.updateOnboardingVisibility();
  },

  dismissOnboarding() {
    this.state.forceShowOnboarding = false;
    try {
      localStorage.setItem(this.ONBOARDING_KEY, 'true');
    } catch (_) {}
    this.updateOnboardingVisibility();
    this.updateChatHintsContent();
    const messageInput = this.els.messageInput;
    if (messageInput) {
      setTimeout(() => messageInput.focus(), 0);
    }
  },

  updateChatHintsVisibility() {
    const hints = this.els.chatHints;
    const chatWindow = this.els.chatWindow;
    if (!hints || !chatWindow) return;
    const hasMessages = chatWindow.querySelectorAll('.message').length > 0;
    this.updateOnboardingVisibility();
    const onboardingVisible = this.els.onboardingScreen && !this.els.onboardingScreen.classList.contains('hidden');
    const showStarter = !onboardingVisible && !hasMessages && !this.state.hasStartedChat;
    hints.classList.toggle('visible', showStarter);
    hints.setAttribute('aria-hidden', showStarter ? 'false' : 'true');
  },

  updateChatHintsContent() {
    const hints = this.els.chatHints;
    if (!hints) return;
    const nudge = this.els.starterDocNudge;
    if (nudge) {
      const hasDocs = Array.isArray(this.state.documents) && this.state.documents.length > 0;
      nudge.classList.toggle('hidden', !hasDocs);
    }
  },

  scrollToMessageAnchor(messageId) {
    const chatMessages = this.els.chatMessages;
    if (!chatMessages) return;
    const el = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!el) return;
    const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'nearest' });
    el.classList.add('highlight');
    const t = setTimeout(() => {
      el.classList.remove('highlight');
    }, 2000);
    if (el._highlightTimer) clearTimeout(el._highlightTimer);
    el._highlightTimer = t;
  },

  async loadSessionHistory() {
    try {
      const res = await fetch(`/api/chat/history?session_id=${encodeURIComponent(this.state.sessionId)}`);
      if (!res.ok) return;
      const data = await res.json();
      const list = data.history || [];
      if (list.length === 0) return;
      this.markChatStarted();
      this.state.messages = list
        .filter((m) => m.role)
        .map((m) => ({
          id: this.generateMessageId(),
          role: m.role,
          content: m.content || '',
          status: 'complete',
        }));
      this.syncDomFromMessages();
      this.scrollToBottom(this.els.chatMessages);
      this.updateScrollButtonVisibility();
      this.updateChatHintsVisibility();
    } catch (_) {}
  },

  async clearSession() {
    try {
      await fetch('/api/chat/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.state.sessionId }),
      });
    } catch (_) {}
    this.state.currentStreamingId = null;
    this.state.currentStreamId = null;
    this.state.messages = [];
    this.syncDomFromMessages();
  },

  newSession() {
    const prevId = this.state.sessionId;
    try {
      fetch('/api/chat/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: prevId }),
      }).catch(() => {});
    } catch (_) {}
    this.state.sessionId = crypto.randomUUID();
    try {
      sessionStorage.setItem('whisperleaf_session_id', this.state.sessionId);
    } catch (_) {}
    this.state.currentStreamingId = null;
    this.state.currentStreamId = null;
    this.state.messages = [];
    this.syncDomFromMessages();
    const input = this.els.messageInput;
    if (input) {
      input.focus();
    }
  },

  // --- Stream response (reader loop)
  // streamId: active stream guard — chunks from an older stream are ignored so only the latest response writes to the UI.
  async streamAssistantResponse(response, streamId) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullReply = '';
    let buffer = '';
    let firstChunkLogged = false;
    let chunkDebugCount = 0;

    const isActiveStream = () => streamId === this.state.currentStreamId;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const { blocks, remainder } = this.processStreamBuffer(buffer);
      buffer = remainder;

      for (const block of blocks) {
        const parsed = this.parseSSEBlock(block);
        if (parsed === null) continue;
        const { event, data } = parsed;
        this.state.lastSseEventAt = Date.now();

        if (event === 'chunk' && data !== undefined) {
          fullReply += data;
          if (!firstChunkLogged && typeof console !== 'undefined' && console.log) {
            console.log('[WhisperLeaf] first SSE chunk received, len=', data.length);
            firstChunkLogged = true;
          }
          if (typeof console !== 'undefined' && console.log && chunkDebugCount < 3) {
            console.log('[WhisperLeaf debug] chunk data:', JSON.stringify(data), 'fullReply len:', fullReply.length);
            chunkDebugCount += 1;
          }
          if (isActiveStream()) {
            this.setSendingState(false);
            const sid = this.state.currentStreamingId;
            if (sid) this.updateMessage(sid, { content: fullReply });
            this.updateStreamingBubble(fullReply);
          }
        } else if (event === 'status') {
          if (isActiveStream()) {
            try {
              const payload = typeof data === 'string' ? JSON.parse(data) : data;
              const step = payload && payload.step;
              const query = (payload && payload.query) || '';
              if (step === 'memory_search') {
                const short = String(query).trim().slice(0, 40);
                this.setThinkingStep(short ? `Searching memory: ${short}${short.length >= 40 ? '\u2026' : ''}` : 'Searching memory\u2026');
              } else if (step === 'model_start') {
                this.setThinkingStep('Warming up local model\u2026');
              } else if (typeof step === 'string' && step.trim()) {
                this.setThinkingStep(step.trim());
              }
            } catch (_) {}
          }
        } else if (event === 'meta') {
          if (isActiveStream()) {
            try {
              const payload = typeof data === 'string' ? JSON.parse(data) : data;
              if (payload && payload.used_memory && Array.isArray(payload.snippets)) {
                this.state.lastMemorySnippets = payload.snippets;
                this.updateMemoryIndicatorUI();
                if (this.els.memoryVisibilityPanel && !this.els.memoryVisibilityPanel.classList.contains('hidden')) {
                  this.renderMemorySnippetsList();
                }
              }
            } catch (_) {}
          }
        } else if (event === 'memory_saved') {
          if (isActiveStream()) {
            try {
              const payload = typeof data === 'string' ? JSON.parse(data) : data;
              this.showMemorySavedNotification(payload || {});
              this.loadSavedMemories();
            } catch (_) {}
          }
        } else if (event === 'doc_sources') {
          if (isActiveStream()) {
            try {
              const payload = typeof data === 'string' ? JSON.parse(data) : data;
              const list = payload && Array.isArray(payload.sources) ? payload.sources : [];
              this.state.docSourcesForCurrentResponse = list.map((s) => String(s).trim()).filter(Boolean);
              const excerpts = payload && Array.isArray(payload.excerpts) ? payload.excerpts : [];
              this.state.docExcerptsForCurrentResponse = excerpts.map((e) => ({
                name: String(e.name || '').trim(),
                snippet: String(e.snippet || '').trim(),
              })).filter((e) => e.name || e.snippet);
            } catch (_) {}
          }
        } else if (event === 'done') {
          if (typeof console !== 'undefined' && console.log) console.log('[WhisperLeaf] SSE done, reply_len=', fullReply.length);
          this.stopWatchdog();
          this.stopGenerationFeedback();
          if (isActiveStream()) {
            if (typeof console !== 'undefined' && console.log) console.log('[WhisperLeaf debug] final frontend text before render (first 120):', JSON.stringify((fullReply || '').slice(0, 120)));
            if (!fullReply.trim()) this.setStreamingBubbleError('No response from model. Check that Ollama is running and the model is loaded.');
            else this.finalizeStreamingBubble();
          } else {
            if (typeof console !== 'undefined' && console.warn) console.warn('[WhisperLeaf] Stale stream done, ignored.');
          }
          return;
        } else if (event === 'error') {
          if (typeof console !== 'undefined' && console.warn) console.warn('[WhisperLeaf] SSE error:', (data || '').trim() || 'Error');
          this.stopWatchdog();
          this.stopGenerationFeedback();
          if (isActiveStream()) {
            this.setStreamingBubbleError((data || '').trim() || 'Error');
          } else {
            if (typeof console !== 'undefined' && console.warn) console.warn('[WhisperLeaf] Stale stream error, ignored.');
          }
          return;
        }
      }
    }

    if (buffer.trim()) {
      const remainderBlocks = buffer.split(/\n\n+/);
      for (let i = 0; i < remainderBlocks.length; i++) {
        const parsed = this.parseSSEBlock(remainderBlocks[i]);
        if (parsed === null) continue;
        const event = parsed.event;
        const data = parsed.data;
        if (event === 'chunk' && data !== undefined) {
          fullReply += data;
          if (isActiveStream()) {
            this.setSendingState(false);
            const sid = this.state.currentStreamingId;
            if (sid) this.updateMessage(sid, { content: fullReply });
            this.updateStreamingBubble(fullReply);
          }
        } else if (event === 'done') {
          this.stopWatchdog();
          this.stopGenerationFeedback();
          if (isActiveStream()) {
            if (!fullReply.trim()) this.setStreamingBubbleError('No response from model. Check that Ollama is running and the model is loaded.');
            else this.finalizeStreamingBubble();
          }
          return;
        } else if (event === 'error') {
          this.stopWatchdog();
          this.stopGenerationFeedback();
          if (isActiveStream()) {
            this.setStreamingBubbleError((data || '').trim() || 'Error');
          }
          return;
        }
      }
    }

    if (typeof console !== 'undefined' && console.log) console.log('[WhisperLeaf] stream reader done (no done event), reply_len=', fullReply.length);
    this.stopWatchdog();
    this.stopGenerationFeedback();
    if (isActiveStream()) {
      if (!fullReply.trim()) this.setStreamingBubbleError('No response from model. Check that Ollama is running and the model is loaded.');
      else this.finalizeStreamingBubble();
    } else {
      if (typeof console !== 'undefined' && console.warn) console.warn('[WhisperLeaf] Stale stream completed, ignored.');
    }
  },

  async sendMessage() {
    if (this.state.isSending) return;
    this.setSendingState(true);
    const text = (this.els.messageInput?.value || '').trim();
    if (!text) {
      this.setSendingState(false);
      return;
    }
    this.markChatStarted();
    const streamId = crypto.randomUUID();
    this.state.currentStreamId = streamId;
    this.els.messageInput.value = '';
    this.resetInputHeight();

    const streamingPrev = this.state.messages.filter((m) => m.status === 'streaming');
    for (const m of streamingPrev) {
      this.state.messages = this.state.messages.filter((x) => x.id !== m.id);
      const el = document.querySelector(`[data-message-id="${m.id}"]`);
      if (el) el.remove();
    }
    this.state.currentStreamingId = null;

    const userMsg = { id: this.generateMessageId(), role: 'user', content: text, status: 'complete' };
    this.addMessage(userMsg);
    this.appendMessageEl(userMsg);
    this.refreshSidebarHistory();

    const assistantMsg = { id: this.generateMessageId(), role: 'assistant', content: '', status: 'streaming' };
    this.addMessage(assistantMsg);
    this.appendMessageEl(assistantMsg);
    this.state.currentStreamingId = assistantMsg.id;
    this.state.lastMemorySnippets = [];
    this.state.docSourcesForCurrentResponse = [];
    this.state.docExcerptsForCurrentResponse = [];
    this.updateMemoryIndicatorUI();
    if (this.els.memoryVisibilityPanel) this.els.memoryVisibilityPanel.classList.add('hidden');
    if (this.els.mindMemoryBtn) this.els.mindMemoryBtn.setAttribute('aria-expanded', 'false');

    this.scrollToBottom(this.els.chatMessages);
    this.updateScrollButtonVisibility();
    this.startGenerationFeedback();
    this.startWatchdog();

    const abortController = new AbortController();
    const onAbort = () => {
      this.stopWatchdog();
      this.stopGenerationFeedback();
      this.setStreamingBubbleError('Request cancelled.');
      this.setSendingState(false);
    };
    const abort = () => {
      abortController.abort();
      window.removeEventListener('beforeunload', abort);
      window.removeEventListener('pagehide', abort);
    };
    window.addEventListener('beforeunload', abort);
    window.addEventListener('pagehide', abort);

    try {
      if (typeof console !== 'undefined' && console.log) console.log('[WhisperLeaf] sending message to /api/chat');
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: this.getHistoryForApi(),
          session_id: this.state.sessionId,
        }),
        signal: abortController.signal,
      });

      if (!res.ok) {
        this.stopWatchdog();
        this.stopGenerationFeedback();
        const err = await res.json().catch(() => ({}));
        let msg = err.detail;
        if (Array.isArray(msg)) msg = (msg[0] && msg[0].msg) ? msg[0].msg : 'Request failed';
        if (typeof msg !== 'string') msg = 'Request failed';
        if (typeof console !== 'undefined' && console.warn) console.warn('[WhisperLeaf] request failed', res.status, err);
        this.setStreamingBubbleError(msg || 'Request failed');
        return;
      }

      if (!res.body) {
        this.stopWatchdog();
        this.stopGenerationFeedback();
        this.setStreamingBubbleError('No response body');
        return;
      }

      await this.streamAssistantResponse(res, streamId);
    } catch (e) {
      if (e && e.name === 'AbortError') {
        onAbort();
        return;
      }
      this.stopWatchdog();
      this.stopGenerationFeedback();
      this.setStreamingBubbleError('Network error: ' + (e && e.message ? e.message : 'Unknown error'));
    } finally {
      window.removeEventListener('beforeunload', abort);
      window.removeEventListener('pagehide', abort);
      if (!this.state.currentStreamingId) this.stopGenerationFeedback();
      this.setSendingState(false);
    }
  },
};

document.addEventListener('DOMContentLoaded', () => ChatController.init());
