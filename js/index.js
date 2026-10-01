/* Daasa Saahitya - index filters */
(function () {
  'use strict';

  const DS = window.DS_INDEX;
  if (!DS) return;

  const songs = DS.songs.map(function (song) {
    const badges = []
      .concat(song.category || [])
      .concat(song.on_who || [])
      .concat(song.types || [])
      .join(' ')
      .toLowerCase();

    return {
      id: song.id,
      title: (song.title || '').toLowerCase(),
      author: (song.author || '').toLowerCase(),
      preview: (song.preview || '').toLowerCase(),
      badges: badges,
      haystack: ((song.title || '') + ' ' + (song.author || '') + ' ' + (song.preview || '')).toLowerCase()
    };
  });

  const state = {
    query: '',
    category: new Set(),
    type: new Set(),
    on_who: new Set(),
    author: new Set()
  };

  const dom = {
    search: document.getElementById('search-input'),
    status: document.getElementById('filter-status'),
    list: document.getElementById('song-list'),
    empty: document.getElementById('empty-state'),
    reset: document.getElementById('reset-filters'),
    category: document.getElementById('filter-category'),
    type: document.getElementById('filter-type'),
    onWho: document.getElementById('filter-on'),
    author: document.getElementById('filter-author')
  };

  const authors = Array.from(new Set(DS.songs.map(function (s) { return s.author; })
    .filter(Boolean))).sort();

  const onWhoOptions = Array.from(new Set(DS.onWho.concat(
    DS.songs.reduce(function (all, s) { return all.concat(s.on_who || []); }, [])
  ))).sort();

  // ── Filtering ──

  function normalize(text) {
    return text.toLowerCase().replace(/[\u0300-\u036f]/g, '');
  }

  function matches(song, terms) {
    return terms.every(function (term) { return song.haystack.indexOf(term) !== -1; });
  }

  function visible() {
    const terms = normalize(state.query).split(/\s+/).filter(Boolean);
    return songs.filter(function (song) {
      if (!matches(song, terms)) return false;
      if (state.category.size && !song.category.some(function (c) { return state.category.has(c); })) return false;
      if (state.type.size && !song.types.some(function (t) { return state.type.has(t); })) return false;
      if (state.on_who.size && !song.on_who.some(function (o) { return state.on_who.has(o); })) return false;
      if (state.author.size && !state.author.has(song.author)) return false;
      return true;
    });
  }

  function activeCount() {
    return state.category.size + state.type.size + state.on_who.size + state.author.size
      + (state.query.trim() ? 1 : 0);
  }

  function apply() {
    const shown = visible();
    const list = dom.list.children;
    const keep = new Set(shown.map(function (song) { return song.id; }));

    for (let i = 0; i < list.length; i++) {
      list[i].hidden = !keep.has(list[i].dataset.id);
    }

    dom.empty.hidden = shown.length !== 0;
    dom.list.hidden = shown.length === 0;

    const filters = activeCount();
    dom.status.textContent = filters === 0
      ? songs.length + ' compositions'
      : shown.length + ' of ' + songs.length + ' compositions · ' + filters
        + (filters === 1 ? ' filter' : ' filters') + ' active';

    syncUrl();
  }

  // ── Checkbox groups ──

  function buildCheckboxes(container, values, field) {
    values.forEach(function (value) {
      const label = document.createElement('label');
      label.className = 'option';

      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = value;
      input.addEventListener('change', function () {
        if (this.checked) state[field].add(value);
        else state[field].delete(value);
        apply();
      });

      const text = document.createElement('span');
      text.textContent = value;

      label.appendChild(input);
      label.appendChild(text);
      container.appendChild(label);
    });
  }

  // ── Tag autocomplete ──

  function buildTagInput(container, options, initial) {
    const field = container.dataset.field;
    const selected = new Set(initial);
    const chips = document.createElement('div');
    chips.className = 'tag-chips';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'tag-field';
    input.autocomplete = 'off';
    input.placeholder = 'Type to search…';

    const list = document.createElement('ul');
    list.className = 'tag-suggestions';
    list.hidden = true;

    container.appendChild(chips);
    container.appendChild(input);
    container.appendChild(list);

    function renderChips() {
      chips.textContent = '';
      selected.forEach(function (value) {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.textContent = value;

        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'tag-remove';
        remove.textContent = '×';
        remove.setAttribute('aria-label', 'Remove ' + value);
        remove.addEventListener('click', function () {
          selected.delete(value);
          state[container.dataset.field].delete(value);
          renderChips();
          apply();
        });

        chip.appendChild(remove);
        chips.appendChild(chip);
      });
    }

    function renderSuggestions() {
      const query = normalize(input.value.trim());
      list.textContent = '';

      const matches = options.filter(function (option) {
        return !selected.has(option) && (!query || normalize(option).indexOf(query) !== -1);
      }).slice(0, 12);

      if (!matches.length) {
        list.hidden = true;
        return;
      }

      matches.forEach(function (option) {
        const item = document.createElement('li');
        item.className = 'tag-suggestion';
        item.textContent = option;
        item.addEventListener('mousedown', function (event) {
          event.preventDefault();
          add(option);
        });
        list.appendChild(item);
      });

      list.hidden = false;
    }

    function add(value) {
      if (!value || selected.has(value)) return;
      selected.add(value);
      state[container.dataset.field].add(value);
      input.value = '';
      renderChips();
      renderSuggestions();
      apply();
      input.focus();
    }

    input.addEventListener('input', renderSuggestions);
    input.addEventListener('focus', renderSuggestions);

    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        const exact = options.filter(function (option) {
          return normalize(option) === normalize(input.value.trim());
        })[0];
        add(exact || input.value.trim());
      } else if (event.key === 'Backspace' && !input.value) {
        const last = Array.from(selected).pop();
        if (last) {
          selected.delete(last);
          state[container.dataset.field].delete(last);
          renderChips();
          apply();
        }
      } else if (event.key === 'Escape') {
        input.value = '';
        renderSuggestions();
      }
    });

    document.addEventListener('click', function (event) {
      if (!container.contains(event.target)) list.hidden = true;
    });

    renderChips();
    initial.forEach(function (value) { state[field].add(value); });
  }

  // ── URL state (shareable / bookmarkable result links) ──

  function syncUrl() {
    const params = new URLSearchParams();

    if (state.query.trim()) params.set('q', state.query.trim());
    ['category', 'type', 'on_who', 'author'].forEach(function (field) {
      const values = Array.from(state[field]);
      if (values.length) params.set(field, values.join(','));
    });

    const query = params.toString();
    const url = window.location.pathname + (query ? '?' + query : '');
    window.history.replaceState(null, '', url);
  }

  function restoreUrl() {
    const params = new URLSearchParams(window.location.search);
    state.query = params.get('q') || '';

    ['category', 'type', 'on_who', 'author'].forEach(function (field) {
      const raw = params.get(field);
      if (raw) raw.split(',').filter(Boolean).forEach(function (value) {
        state[field].add(value);
      });
    });

    dom.search.value = state.query;
  }

  function restoreControls() {
    ['category', 'type'].forEach(function (field) {
      const container = field === 'category' ? dom.category : dom.type;
      Array.from(container.querySelectorAll('input')).forEach(function (input) {
        input.checked = state[field].has(input.value);
      });
    });
  }

  function reset() {
    state.query = '';
    Object.keys(state).forEach(function (field) {
      if (state[field] instanceof Set) state[field].clear();
    });
    dom.search.value = '';
    apply();
  }

  // ── Init ──

  function init() {
    restoreUrl();

    buildCheckboxes(dom.category, DS.categories, 'category');
    buildCheckboxes(dom.type, DS.types, 'type');
    buildTagInput(dom.onWho, onWhoOptions, Array.from(state.on_who));
    buildTagInput(dom.author, authors, Array.from(state.author));

    restoreControls();

    dom.search.addEventListener('input', function () {
      state.query = this.value;
      apply();
    });

    dom.reset.addEventListener('click', function () {
      reset();
      dom.search.focus();
    });

    document.addEventListener('keydown', function (event) {
      const typing = /^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName);
      if (event.key === '/' && !typing) {
        event.preventDefault();
        dom.search.focus();
      } else if (event.key === 'Escape') {
        reset();
      }
    });

    apply();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();