document.addEventListener('DOMContentLoaded', () => {
  const STORAGE_KEY = 'findlog:itens-salvos';
  const feed = document.getElementById('feedGrid');
  if (!feed) return;

  const feedUrl = feed.dataset.feedUrl || window.location.pathname;
  let hasNext = feed.dataset.hasNext === 'true';
  let nextPage = feed.dataset.nextPage ? Number(feed.dataset.nextPage) : null;
  let totalItens = Number(feed.dataset.totalItens) || 0;
  let isLoading = false;
  let abortController = null;

  const searchInput = document.getElementById('feedSearch');
  const searchClear = document.getElementById('feedSearchClear');
  const sortSelect = document.getElementById('feedSort');
  const categoryList = document.getElementById('categoryList');
  const mobileCategoryChips = document.getElementById('mobileCategoryChips');
  const categoryClear = document.getElementById('categoryClear');
  const countBadge = document.getElementById('feedCount');
  const emptyState = document.getElementById('feedEmpty');
  const emptyTitle = document.getElementById('feedEmptyTitle');
  const emptyText = document.getElementById('feedEmptyText');
  const emptyClear = document.getElementById('emptyClear');
  const savedBanner = document.getElementById('savedBanner');
  const sentinel = document.getElementById('feedInfiniteSentinel');

  let activeCategory = '';
  let currentView = 'feed';
  let saved = new Set(loadSaved());

  // Lê as categorias agregadas do servidor (cobre todos os itens, não só a 1ª página)
  let serverCategories = [];
  const catScript = document.getElementById('feedCategoriasData');
  if (catScript) {
    try { serverCategories = JSON.parse(catScript.textContent) || []; } catch (e) {}
  }

  function loadSaved() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      return Array.isArray(raw) ? raw.filter(i => typeof i === 'string') : [];
    } catch (e) { return []; }
  }

  function persistSaved() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify([...saved])); } catch (e) {}
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* ------------------------------------------------------------------
     Renderização de card recebido via JSON
     ------------------------------------------------------------------ */
  function createPostElement(item) {
    const isSaved = saved.has(item.codigo);
    const article = document.createElement('article');
    article.className = 'usr-post';
    article.id = 'item-' + item.codigo;
    article.dataset.instituicao = item.instituicao_cnpj;
    article.dataset.status = item.status;
    article.dataset.categoria = item.categoria;
    article.dataset.codigo = item.codigo;
    article.dataset.nome = item.nome;
    article.dataset.local = item.local;
    article.dataset.timestamp = item.timestamp;

    const facts = [
      `<span class="usr-fact" title="${escapeHtml(item.local)}"><i class="bi bi-geo-alt-fill"></i><span>${escapeHtml(item.local)}</span></span>`,
      `<span class="usr-fact" title="Data de registro"><i class="bi bi-calendar3"></i><span>${escapeHtml(item.data_registro_fmt)}</span></span>`,
      item.marca_ou_modelo ? `<span class="usr-fact"><i class="bi bi-upc-scan"></i><span>${escapeHtml(item.marca_ou_modelo)}</span></span>` : '',
      item.cor ? `<span class="usr-fact"><i class="bi bi-palette"></i><span>${escapeHtml(item.cor)}</span></span>` : '',
      item.material ? `<span class="usr-fact"><i class="bi bi-layers"></i><span>${escapeHtml(item.material)}</span></span>` : '',
      item.tamanho ? `<span class="usr-fact"><i class="bi bi-rulers"></i><span>${escapeHtml(item.tamanho)}</span></span>` : '',
      item.local_guardado ? `<span class="usr-fact"><i class="bi bi-box-seam"></i><span>Guardado em ${escapeHtml(item.local_guardado)}</span></span>` : ''
    ].filter(Boolean).join('');

    article.innerHTML = `
      <header class="usr-post-head">
        <div class="usr-post-avatar" aria-hidden="true">${escapeHtml(item.instituicao_nome.slice(0, 1) || 'I')}</div>
        <div class="usr-post-author">
          <span class="usr-post-inst">${escapeHtml(item.instituicao_nome)}</span>
          <span class="usr-post-sub">
            <i class="bi bi-clock" aria-hidden="true"></i>
            <span>${escapeHtml(item.tempo_atras)}</span>
            <span class="usr-post-sub-place">
              <span aria-hidden="true">·</span>
              <i class="bi bi-geo-alt" aria-hidden="true"></i>
              <span>${escapeHtml(item.local)}</span>
            </span>
          </span>
        </div>
        <span class="usr-post-status usr-st-found">
          <i class="bi bi-box-arrow-in-down"></i> ${escapeHtml(item.status_label)}
        </span>
      </header>

      <div class="usr-post-content">
        <div class="usr-post-kicker">
          <span class="usr-post-cat"><i class="bi bi-tag-fill"></i><span>${escapeHtml(item.categoria)}</span></span>
          <span class="usr-post-code">#${escapeHtml(item.codigo)}</span>
        </div>
        <h2 class="usr-post-title">${escapeHtml(item.nome)}</h2>
        ${item.descricao ? `<p class="usr-post-desc">${escapeHtml(item.descricao)}</p>` : ''}
      </div>

      <div class="usr-post-media">
        <div class="usr-post-media-placeholder" aria-hidden="true">
          <i class="bi bi-image"></i>
          <span>Sem foto do item</span>
        </div>
        ${item.foto_url ? `<img src="${escapeHtml(item.foto_url)}" alt="Foto de ${escapeHtml(item.nome)}" loading="lazy" decoding="async" onerror="this.classList.add('usr-hidden');">` : ''}
      </div>

      <div class="usr-post-facts">${facts}</div>

      <footer class="usr-post-actions">
        <button type="button" class="usr-action usr-action-primary" data-claim
                data-bs-toggle="modal" data-bs-target="#claimModal"
                data-nome="${escapeHtml(item.nome)}"
                data-codigo="${escapeHtml(item.codigo)}"
                data-local="${escapeHtml(item.local)}"
                data-instituicao="${escapeHtml(item.instituicao_nome)}"
                data-categoria="${escapeHtml(item.categoria)}">
          <i class="bi bi-person-raised-hand"></i>
          <span>É meu, quero reivindicar</span>
        </button>

        <button type="button" class="usr-action usr-action-save ${isSaved ? 'is-saved' : ''}" data-save
                data-codigo="${escapeHtml(item.codigo)}" aria-pressed="${isSaved}">
          <i class="bi ${isSaved ? 'bi-bookmark-fill' : 'bi-bookmark'}"></i>
          <span>${isSaved ? 'Salvo' : 'Salvar'}</span>
        </button>

        <button type="button" class="usr-action usr-action-icon" data-share
                data-codigo="${escapeHtml(item.codigo)}"
                aria-label="Compartilhar ${escapeHtml(item.nome)}">
          <i class="bi bi-share"></i>
        </button>
      </footer>
    `;
    return article;
  }

  /* ------------------------------------------------------------------
     Busca paginada no servidor (append = true no scroll; false no filtro)
     ------------------------------------------------------------------ */
  async function fetchFeedPage({ page = 1, append = false } = {}) {
    if (isLoading && append) return;
    if (!append && abortController) abortController.abort();

    isLoading = true;
    abortController = new AbortController();

    const params = new URLSearchParams();
    params.set('format', 'json');
    params.set('page', String(page));

    const term = searchInput ? searchInput.value.trim() : '';
    if (term) params.set('q', term);
    if (activeCategory) params.set('categoria', activeCategory);
    if (sortSelect && sortSelect.value) params.set('ordem', sortSelect.value);
    if (currentView === 'saved') {
      params.set('salvos', saved.size ? [...saved].join(',') : '__nenhum__');
    }

    if (sentinel) sentinel.classList.remove('usr-hidden');

    try {
      const resp = await fetch(`${feedUrl}?${params.toString()}`, {
        signal: abortController.signal,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!resp.ok) throw new Error('Falha ao carregar feed');
      const data = await resp.json();

      if (!append) {
        feed.querySelectorAll('.usr-post').forEach(el => el.remove());
      }

      const fragment = document.createDocumentFragment();
      (data.itens || []).forEach(item => fragment.appendChild(createPostElement(item)));

      if (emptyState) {
        feed.insertBefore(fragment, emptyState);
      } else {
        feed.appendChild(fragment);
      }

      hasNext = Boolean(data.has_next);
      nextPage = data.next_page || null;
      totalItens = Number(data.total_itens) || 0;

      updateFeedChrome();
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error(err);
      }
    } finally {
      isLoading = false;
      if (sentinel) sentinel.classList.toggle('usr-hidden', !hasNext);
    }
  }

  function updateFeedChrome() {
    const term = searchInput ? searchInput.value.trim() : '';
    if (countBadge) {
      countBadge.innerHTML = `<i class="bi bi-collection"></i> ${totalItens}${totalItens === 1 ? ' item' : ' itens'}`;
    }
    if (searchClear) searchClear.classList.toggle('usr-hidden', !term);
    if (savedBanner) savedBanner.classList.toggle('usr-hidden', currentView !== 'saved');

    const hasFilter = Boolean(term) || Boolean(activeCategory) || currentView === 'saved';
    const renderedCount = feed.querySelectorAll('.usr-post').length;

    if (emptyState) {
      emptyState.classList.toggle('usr-hidden', renderedCount > 0);
      if (renderedCount === 0 && emptyTitle && emptyText) {
        emptyTitle.textContent = currentView === 'saved' ? 'Nenhum item salvo' : 'Nenhum item encontrado';
        emptyText.textContent = currentView === 'saved'
          ? 'Toque em "Salvar" nas publicações para acompanhar itens aqui.'
          : 'Nenhum item corresponde à busca ou aos filtros selecionados.';
      }
    }
    if (emptyClear) emptyClear.classList.toggle('usr-hidden', !hasFilter);
  }

  /* ------------------------------------------------------------------
     IntersectionObserver: dispara a próxima página ao rolar perto do fim
     ------------------------------------------------------------------ */
  if (sentinel && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasNext && nextPage && !isLoading) {
        fetchFeedPage({ page: nextPage, append: true });
      }
    }, { rootMargin: '320px 0px' }); // Pré-carrega 320px antes de chegar no rodapé

    observer.observe(sentinel);
  }

  /* ------------------------------------------------------------------
     Delegação de eventos no #feedGrid (funciona para itens SSR e AJAX)
     ------------------------------------------------------------------ */
  feed.addEventListener('click', (event) => {
    const saveBtn = event.target.closest('[data-save]');
    if (saveBtn) {
      const code = saveBtn.dataset.codigo;
      if (!code) return;
      if (saved.has(code)) saved.delete(code);
      else saved.add(code);
      persistSaved();

      const isSaved = saved.has(code);
      saveBtn.classList.toggle('is-saved', isSaved);
      saveBtn.setAttribute('aria-pressed', String(isSaved));
      const icon = saveBtn.querySelector('i');
      const label = saveBtn.querySelector('span');
      if (icon) icon.className = isSaved ? 'bi bi-bookmark-fill' : 'bi bi-bookmark';
      if (label) label.textContent = isSaved ? 'Salvo' : 'Salvar';

      if (currentView === 'saved') fetchFeedPage({ page: 1, append: false });
      return;
    }

    const shareBtn = event.target.closest('[data-share]');
    if (shareBtn) {
      const post = shareBtn.closest('.usr-post');
      const code = shareBtn.dataset.codigo || (post ? post.dataset.codigo : '');
      const name = post ? post.dataset.nome : 'Item';
      const url = `${window.location.origin}${window.location.pathname}#item-${encodeURIComponent(code)}`;
      if (navigator.share) {
        navigator.share({ title: 'FindLog', text: `${name} — código ${code}`, url }).catch(() => {});
      } else if (navigator.clipboard) {
        navigator.clipboard.writeText(`${name} — código ${code}\n${url}`).catch(() => {});
      }
    }
  });

  /* ------------------------------------------------------------------
     Debounce na busca + filtros
     ------------------------------------------------------------------ */
  let searchTimer = null;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => fetchFeedPage({ page: 1, append: false }), 350);
    });
  }

  if (searchClear) {
    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      fetchFeedPage({ page: 1, append: false });
      searchInput.focus();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener('change', () => fetchFeedPage({ page: 1, append: false }));
  }

  if (emptyClear) {
    emptyClear.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      activeCategory = '';
      currentView = 'feed';
      if (sortSelect) sortSelect.value = 'recent';
      renderCategories();
      fetchFeedPage({ page: 1, append: false });
    });
  }

  function renderCategories() {
    if (categoryList) {
      categoryList.innerHTML = '';
      serverCategories.forEach(({ nome, total }) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'usr-cat-item' + (activeCategory === nome ? ' active' : '');
        btn.innerHTML = `<span class="usr-cat-dot"></span><span class="usr-cat-name">${escapeHtml(nome)}</span><span class="usr-cat-count">${total}</span>`;
        btn.addEventListener('click', () => {
          activeCategory = activeCategory === nome ? '' : nome;
          renderCategories();
          fetchFeedPage({ page: 1, append: false });
        });
        categoryList.appendChild(btn);
      });
    }

    if (mobileCategoryChips) {
      mobileCategoryChips.innerHTML = '';
      const allBtn = document.createElement('button');
      allBtn.type = 'button';
      allBtn.className = 'usr-chip' + (activeCategory === '' ? ' active' : '');
      allBtn.textContent = 'Todas';
      allBtn.addEventListener('click', () => {
        activeCategory = '';
        renderCategories();
        fetchFeedPage({ page: 1, append: false });
      });
      mobileCategoryChips.appendChild(allBtn);

      serverCategories.forEach(({ nome }) => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'usr-chip' + (activeCategory === nome ? ' active' : '');
        chip.textContent = nome;
        chip.addEventListener('click', () => {
          activeCategory = activeCategory === nome ? '' : nome;
          renderCategories();
          fetchFeedPage({ page: 1, append: false });
        });
        mobileCategoryChips.appendChild(chip);
      });
    }

    if (categoryClear) categoryClear.disabled = !activeCategory;
  }

  document.querySelectorAll('[data-view]').forEach(btn => {
    btn.addEventListener('click', () => {
      currentView = btn.dataset.view === 'saved' ? 'saved' : 'feed';
      fetchFeedPage({ page: 1, append: false });
    });
  });

  renderCategories();
  updateFeedChrome();
});