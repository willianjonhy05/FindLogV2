    document.addEventListener('DOMContentLoaded', () => {
      const STORAGE_KEY = 'findlog:itens-salvos';

      const STATUS_META = {
        '1': { label: 'Perdido', icon: 'bi-exclamation-circle' },
        '2': { label: 'Encontrado', icon: 'bi-box-arrow-in-down' },
        '3': { label: 'Devolvido', icon: 'bi-check2-circle' },
        '4': { label: 'Outro', icon: 'bi-question-circle' }
      };

      const body = document.body;
      const currentInstitution = (body.dataset.instituicao || '').trim();

      const feed = document.getElementById('feedGrid');
      const searchInput = document.getElementById('feedSearch');
      const searchClear = document.getElementById('feedSearchClear');
      const statusChips = document.getElementById('statusChips');
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
      const menuSavedCount = document.getElementById('menuSaved');
      const headerSavedCount = document.getElementById('headerSavedCount');
      const bottomSavedCount = document.getElementById('bottomSavedCount');
      const statItens = document.getElementById('statItens');
      const statCategorias = document.getElementById('statCategorias');
      const statSalvos = document.getElementById('statSalvos');
      const toastStack = document.getElementById('toastStack');
      const claimModalEl = document.getElementById('claimModal');

      if (!feed) {
        return;
      }

      const posts = Array.from(feed.querySelectorAll('.usr-post')).map(el => ({
        el,
        instituicao: el.dataset.instituicao || '',
        status: el.dataset.status || '',
        categoria: el.dataset.categoria || 'Sem categoria',
        codigo: el.dataset.codigo || '',
        ts: Number(el.dataset.timestamp) || 0,
        search: normalize(el.dataset.search)
      }));

      const institutionPosts = posts.filter(post => (
        !currentInstitution || post.instituicao === currentInstitution
      ));

      // Itens de outras instituições nunca aparecem, mesmo que cheguem no contexto.
      posts.forEach(post => {
        if (currentInstitution && post.instituicao !== currentInstitution) {
          post.el.classList.add('usr-hidden');
        }
      });

      let activeStatus = 'all';
      let activeCategory = '';
      let currentView = 'feed';
      let saved = new Set(loadSaved());

      const viewButtons = Array.from(document.querySelectorAll('[data-view]'));

      /* ------------------------------------------------------------------
         Utilidades
         ------------------------------------------------------------------ */
      function normalize(value) {
        return (value || '')
          .toString()
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '');
      }

      function setText(id, value) {
        const element = document.getElementById(id);
        if (element) {
          element.textContent = value;
        }
      }

      function loadSaved() {
        try {
          const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
          return Array.isArray(raw) ? raw.filter(item => typeof item === 'string') : [];
        } catch (error) {
          return [];
        }
      }

      function persistSaved() {
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify([...saved]));
        } catch (error) {
          /* Armazenamento indisponível: mantém apenas em memória. */
        }
      }

      function copyText(text) {
        const fallback = () => {
          try {
            const area = document.createElement('textarea');
            area.value = text;
            area.setAttribute('readonly', '');
            area.style.position = 'fixed';
            area.style.opacity = '0';
            document.body.appendChild(area);
            area.select();
            const ok = document.execCommand('copy');
            area.remove();
            return ok;
          } catch (error) {
            return false;
          }
        };

        if (navigator.clipboard && window.isSecureContext) {
          return navigator.clipboard.writeText(text)
            .then(() => true)
            .catch(() => fallback());
        }

        return Promise.resolve(fallback());
      }

      function toast(message, icon) {
        if (!toastStack) {
          return;
        }

        const element = document.createElement('div');
        element.className = 'usr-toast';

        const iconElement = document.createElement('i');
        iconElement.className = 'bi ' + (icon || 'bi-check2-circle');

        const textElement = document.createElement('span');
        textElement.textContent = message;

        element.append(iconElement, textElement);
        toastStack.appendChild(element);

        window.setTimeout(() => {
          element.classList.add('is-leaving');
          window.setTimeout(() => element.remove(), 220);
        }, 2600);
      }

      /* ------------------------------------------------------------------
         Categorias
         ------------------------------------------------------------------ */
      function categoryEntries() {
        const counts = new Map();

        institutionPosts.forEach(post => {
          const name = post.categoria || 'Sem categoria';
          counts.set(name, (counts.get(name) || 0) + 1);
        });

        return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0], 'pt-BR'));
      }

      function renderCategories() {
        const entries = categoryEntries();

        if (categoryList) {
          categoryList.innerHTML = '';

          if (!entries.length) {
            const empty = document.createElement('p');
            empty.className = 'usr-cat-empty';
            empty.textContent = 'Nenhuma categoria disponível.';
            categoryList.appendChild(empty);
          }

          entries.forEach(([name, count]) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'usr-cat-item' + (activeCategory === name ? ' active' : '');
            button.title = name;

            const dot = document.createElement('span');
            dot.className = 'usr-cat-dot';

            const label = document.createElement('span');
            label.className = 'usr-cat-name';
            label.textContent = name;

            const total = document.createElement('span');
            total.className = 'usr-cat-count';
            total.textContent = count;

            button.append(dot, label, total);
            button.addEventListener('click', () => toggleCategory(name));
            categoryList.appendChild(button);
          });
        }

        if (mobileCategoryChips) {
          mobileCategoryChips.innerHTML = '';

          const allChip = document.createElement('button');
          allChip.type = 'button';
          allChip.className = 'usr-chip' + (activeCategory === '' ? ' active' : '');
          allChip.textContent = 'Todas';
          allChip.addEventListener('click', () => toggleCategory(''));
          mobileCategoryChips.appendChild(allChip);

          entries.forEach(([name]) => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'usr-chip' + (activeCategory === name ? ' active' : '');
            chip.textContent = name;
            chip.addEventListener('click', () => toggleCategory(name));
            mobileCategoryChips.appendChild(chip);
          });
        }

        if (categoryClear) {
          categoryClear.disabled = !activeCategory;
        }
      }

      function toggleCategory(name) {
        activeCategory = activeCategory === name ? '' : name;
        renderCategories();
        applyFilters();
      }

      /* ------------------------------------------------------------------
         Status
         ------------------------------------------------------------------ */
      function buildStatusChips() {
        if (!statusChips) {
          return;
        }

        const counts = new Map();
        institutionPosts.forEach(post => {
          counts.set(post.status, (counts.get(post.status) || 0) + 1);
        });

        statusChips.innerHTML = '';

        // Com um único status, o filtro não acrescenta nada.
        if (counts.size <= 1) {
          statusChips.classList.add('usr-hidden');
          return;
        }

        statusChips.classList.remove('usr-hidden');

        const entries = [{
          value: 'all',
          label: 'Todos',
          icon: 'bi-grid-3x3-gap'
        }].concat(
          [...counts.entries()]
            .sort((a, b) => Number(a[0]) - Number(b[0]))
            .map(([value]) => ({
              value,
              label: (STATUS_META[value] || {}).label || 'Outro',
              icon: (STATUS_META[value] || {}).icon || 'bi-circle'
            }))
        );

        entries.forEach(entry => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'usr-chip' + (activeStatus === entry.value ? ' active' : '');
          button.dataset.status = entry.value;

          const icon = document.createElement('i');
          icon.className = 'bi ' + entry.icon;

          const label = document.createElement('span');
          label.textContent = entry.label;

          button.append(icon, label);
          button.addEventListener('click', () => {
            activeStatus = entry.value;
            buildStatusChips();
            applyFilters();
          });

          statusChips.appendChild(button);
        });
      }

      /* ------------------------------------------------------------------
         Salvos
         ------------------------------------------------------------------ */
      function savedInstitutionCount() {
        return institutionPosts.filter(post => saved.has(post.codigo)).length;
      }

      function updateSavedUI() {
        const total = savedInstitutionCount();
        [menuSavedCount, headerSavedCount, bottomSavedCount, statSalvos].forEach(element => {
          if (element) {
            element.textContent = total;
          }
        });

        [headerSavedCount, bottomSavedCount].forEach(element => {
          if (element) {
            element.classList.toggle('usr-hidden', total === 0);
          }
        });

        feed.querySelectorAll('[data-save]').forEach(button => {
          const isSaved = saved.has(button.dataset.codigo);
          const post = button.closest('.usr-post');
          const itemName = post ? post.dataset.nome : 'item';

          button.classList.toggle('is-saved', isSaved);
          button.setAttribute('aria-pressed', String(isSaved));
          button.setAttribute(
            'aria-label',
            (isSaved ? 'Remover ' : 'Salvar ') + itemName + (isSaved ? ' dos salvos' : '')
          );

          const icon = button.querySelector('i');
          if (icon) {
            icon.className = isSaved ? 'bi bi-bookmark-fill' : 'bi bi-bookmark';
          }

          const label = button.querySelector('span');
          if (label) {
            label.textContent = isSaved ? 'Salvo' : 'Salvar';
          }
        });
      }

      /* ------------------------------------------------------------------
         Visualizações (feed x salvos)
         ------------------------------------------------------------------ */
      function updateViewButtons() {
        viewButtons.forEach(button => {
          const isActive = button.dataset.view === currentView;
          button.classList.toggle('active', isActive);

          if (button.classList.contains('usr-menu-item')) {
            if (isActive) {
              button.setAttribute('aria-current', 'page');
            } else {
              button.removeAttribute('aria-current');
            }
          }
        });

        document.querySelectorAll('.usr-view-feed-link').forEach(link => {
          link.classList.toggle('active', currentView === 'feed');
        });
      }

      function setView(view) {
        currentView = view === 'saved' ? 'saved' : 'feed';
        updateViewButtons();
        applyFilters();

        const top = feed.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top, behavior: 'smooth' });
      }

      viewButtons.forEach(button => {
        button.addEventListener('click', () => setView(button.dataset.view));
      });

      /* ------------------------------------------------------------------
         Ordenação
         ------------------------------------------------------------------ */
      function sortPosts(mode) {
        const ordered = [...institutionPosts].sort((a, b) => (
          mode === 'old' ? a.ts - b.ts : b.ts - a.ts
        ));

        ordered.forEach(post => feed.appendChild(post.el));

        if (emptyState) {
          feed.appendChild(emptyState);
        }
      }

      /* ------------------------------------------------------------------
         Filtros
         ------------------------------------------------------------------ */
      function applyFilters() {
        const term = normalize(searchInput ? searchInput.value.trim() : '');
        let visible = 0;

        posts.forEach(post => {
          const matchesInstitution = !currentInstitution || post.instituicao === currentInstitution;
          const matchesTerm = !term || post.search.includes(term);
          const matchesStatus = activeStatus === 'all' || post.status === activeStatus;
          const matchesCategory = !activeCategory || post.categoria === activeCategory;
          const matchesView = currentView !== 'saved' || saved.has(post.codigo);
          const show = matchesInstitution && matchesTerm && matchesStatus && matchesCategory && matchesView;

          post.el.classList.toggle('usr-hidden', !show);

          if (show) {
            visible += 1;
          }
        });

        if (countBadge) {
          countBadge.innerHTML = '<i class="bi bi-collection"></i> ' + visible + (visible === 1 ? ' item' : ' itens');
        }

        if (searchClear) {
          searchClear.classList.toggle('usr-hidden', !term);
        }

        if (savedBanner) {
          savedBanner.classList.toggle('usr-hidden', currentView !== 'saved');
        }

        const hasFilter = Boolean(term) || Boolean(activeCategory) || activeStatus !== 'all' || currentView === 'saved';
        const showEmpty = visible === 0 && (institutionPosts.length > 0 || hasFilter);

        if (emptyState) {
          emptyState.classList.toggle('usr-hidden', !showEmpty);
        }

        if (showEmpty && emptyTitle && emptyText) {
          if (currentView === 'saved' && savedInstitutionCount() === 0) {
            emptyTitle.textContent = 'Nenhum item salvo';
            emptyText.textContent = 'Toque em “Salvar” nas publicações para guardar os itens que você quer acompanhar.';
          } else if (currentView === 'saved') {
            emptyTitle.textContent = 'Nenhum salvo com esses filtros';
            emptyText.textContent = 'Você tem itens salvos, mas nenhum corresponde à busca ou aos filtros atuais.';
          } else {
            emptyTitle.textContent = 'Nenhum item encontrado';
            emptyText.textContent = 'Nenhum item corresponde à busca ou aos filtros selecionados.';
          }
        }

        if (emptyClear) {
          emptyClear.classList.toggle('usr-hidden', !hasFilter);
        }
      }

      function resetFilters() {
        if (searchInput) {
          searchInput.value = '';
        }

        activeStatus = 'all';
        activeCategory = '';
        currentView = 'feed';

        if (sortSelect) {
          sortSelect.value = 'recent';
        }

        buildStatusChips();
        renderCategories();
        updateViewButtons();
        sortPosts('recent');
        applyFilters();
      }

      /* ------------------------------------------------------------------
         Eventos de busca, filtro e ordenação
         ------------------------------------------------------------------ */
      if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
        searchInput.addEventListener('search', applyFilters);
      }

      if (searchClear) {
        searchClear.addEventListener('click', () => {
          if (searchInput) {
            searchInput.value = '';
            applyFilters();
            searchInput.focus();
          }
        });
      }

      if (sortSelect) {
        sortSelect.addEventListener('change', () => {
          sortPosts(sortSelect.value);
          applyFilters();
        });
      }

      if (categoryClear) {
        categoryClear.addEventListener('click', () => {
          activeCategory = '';
          renderCategories();
          applyFilters();
        });
      }

      if (emptyClear) {
        emptyClear.addEventListener('click', resetFilters);
      }

      document.querySelectorAll('[data-focus-search]').forEach(button => {
        button.addEventListener('click', () => {
          if (!searchInput) {
            return;
          }

          searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
          window.setTimeout(() => searchInput.focus(), 260);
        });
      });

      /* ------------------------------------------------------------------
         Salvar item
         ------------------------------------------------------------------ */
      feed.querySelectorAll('[data-save]').forEach(button => {
        button.addEventListener('click', () => {
          const code = button.dataset.codigo;
          if (!code) {
            return;
          }

          if (saved.has(code)) {
            saved.delete(code);
            toast('Item removido dos salvos.', 'bi-bookmark');
          } else {
            saved.add(code);
            toast('Item salvo! Veja em “Salvos”.', 'bi-bookmark-fill');
          }

          persistSaved();
          updateSavedUI();
          applyFilters();
        });
      });

      /* ------------------------------------------------------------------
         Compartilhar item
         ------------------------------------------------------------------ */
      feed.querySelectorAll('[data-share]').forEach(button => {
        button.addEventListener('click', () => {
          const post = button.closest('.usr-post');
          const code = button.dataset.codigo || (post ? post.dataset.codigo : '');
          const name = post ? post.dataset.nome : 'Item';
          const url = window.location.origin + window.location.pathname + '#item-' + encodeURIComponent(code);
          const text = name + ' — achados e perdidos (código ' + code + ')';

          const fallback = () => {
            copyText(text + '\n' + url).then(ok => {
              toast(
                ok ? 'Link do item copiado!' : 'Não foi possível copiar o link.',
                ok ? 'bi-check2-circle' : 'bi-exclamation-circle'
              );
            });
          };

          if (navigator.share) {
            navigator.share({ title: 'FindLog', text, url }).catch(error => {
              if (!error || error.name !== 'AbortError') {
                fallback();
              }
            });
            return;
          }

          fallback();
        });
      });

      /* ------------------------------------------------------------------
         Links ainda não publicados
         ------------------------------------------------------------------ */
      document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', event => {
          event.preventDefault();
          toast('Esta área estará disponível em breve.', 'bi-info-circle');
        });
      });

      /* ------------------------------------------------------------------
         Modal de reivindicação
         ------------------------------------------------------------------ */
      if (claimModalEl) {
        claimModalEl.addEventListener('show.bs.modal', event => {
          const trigger = event.relatedTarget;
          if (!trigger) {
            return;
          }

          const name = trigger.dataset.nome || 'Item';
          const code = trigger.dataset.codigo || '—';
          const local = trigger.dataset.local || 'Local não informado';
          const institution = trigger.dataset.instituicao || 'a instituição';

          setText('claimItemName', name);
          setText('claimItemCode', '#' + code);
          setText('claimItemLocal', local);
          setText('claimItemCodeInline', '#' + code);
          setText('claimItemInstitution', institution);

          const copyButton = document.getElementById('claimCopyCode');
          if (copyButton) {
            copyButton.dataset.codigo = code;
          }
        });
      }

      const claimCopyButton = document.getElementById('claimCopyCode');
      if (claimCopyButton) {
        claimCopyButton.addEventListener('click', () => {
          const code = claimCopyButton.dataset.codigo || '';

          copyText(code).then(ok => {
            toast(
              ok ? 'Código #' + code + ' copiado!' : 'Não foi possível copiar o código.',
              ok ? 'bi-clipboard-check' : 'bi-exclamation-circle'
            );
          });
        });
      }

      /* ------------------------------------------------------------------
         Estatísticas e inicialização
         ------------------------------------------------------------------ */
      if (statItens) {
        statItens.textContent = institutionPosts.length;
      }

      if (statCategorias) {
        statCategorias.textContent = categoryEntries().length;
      }

      buildStatusChips();
      renderCategories();
      updateSavedUI();
      updateViewButtons();
      sortPosts('recent');
      applyFilters();

      /* Fechamento automático das mensagens do Django */
      document.querySelectorAll('.custom-alert').forEach(alert => {
        window.setTimeout(() => {
          const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
          bsAlert.close();
        }, 5000);
      });
    });