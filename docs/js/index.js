/* Daasa Saahitya - index filters */
(function () {
  'use strict';

  const DS = window.DS_INDEX;
  if (!DS) return;

  // Strip case and combining marks so "rāma" matches a typed "rama".
  const normalize = (text) =>
    String(text || '').toLowerCase().replace(/[̀-ͯ]/g, '');

  const songs = DS.songs.map((song) => {
    song.category = song.category || [];
    song.types = song.types || [];
    song.on_who = song.on_who || [];
    song.searchAuthor = normalize(song.author);
    song.haystack = normalize(
      (song.title || '') + ' ' + (song.author || '') + ' ' + (song.preview || '')
    );
    return song;
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

  const authors = Array.from(
    new Set(DS.songs.map((song) => song.author).filter(Boolean))
  ).sort();

  const onWhoOptions = Array.from(
    new Set(DS.onWho.concat(DS.songs.flatMap((song) => song.on_who || [])))
  ).sort();

  // ── Filtering ──

  function matchesField(values, chosen) {
    return !chosen.size || values.some((value) => chosen.has(value));
  }

  function visible() {
    const terms = normalize(state.query).split(/\s+/).filter(Boolean);

    return songs.filter((song) => {
      if (!terms.every((term) => song.haystack.includes(term))) return false;
      if (!matchesField(song.category, state.category)) return false;
      if (!matchesField(song.types, state.type)) return false;
      if (!matchesField(song.on_who, state.on_who)) return false;
      if (state.author.size
        && !Array.from(state.author).some((a) => normalize(a) === song.searchAuthor)) {
        return false;
      }
      return true;
    });
  }

  function activeCount() {
    const sets = state.category.size + state.type.size + state.on_who.size + state.author.size;
    return sets + (state.query.trim() ? 1 : 0);
  }

  function syncUrl() {
    const params = new URLSearchParams();
    if (state.query.trim()) params.set('q', state.query.trim());

    ['category', 'type', 'on_who', 'author'].forEach((field) => {
      const values = Array.from(state[field]);
      if (values.length) params.set(field, values.join(','));
    });

    const query = params.toString();
    window.history.replaceState(null, '', window.location.pathname + (query ? '?' + query : ''));
  }

  function apply() {
    const shown = visible();
    const keep = new Set(shown.map((song) => song.id));

    Array.from(dom.list.children).forEach((entry) => {
      entry.hidden = !keep.has(entry.dataset.id);
    });

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
    values.forEach((value) => {
      const label = document.createElement('label');
      label.className = 'option';

      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = value;
      input.addEventListener('change', () => {
        if (input.checked) state[field].add(value);
        else state[field].delete(value);
        apply();
      });

      const text = document.createElement('span');
      text.textContent = value;

      label.append(input, text);
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

    container.append(chips, input, list);

    function renderChips() {
      chips.textContent = '';
      selected.forEach((value) => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.appendChild(document.createTextNode(value));

        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'tag-remove';
        remove.textContent = '×';
        remove.setAttribute('aria-label', 'Remove ' + value);
        remove.addEventListener('click', () => {
          selected.delete(value);
          state[field].delete(value);
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

      const matches = options
        .filter((option) => !selected.has(option)
          && (!query || normalize(option).includes(query)))
        .slice(0, 12);

      if (!matches.length) {
        list.hidden = true;
        return;
      }

      matches.forEach((option) => {
        const item = document.createElement('li');
        item.className = 'tag-suggestion';
        item.textContent = option;
        item.addEventListener('mousedown', (event) => {
          event.preventDefault();
          add(option);
        });
        list.appendChild(item);
      });

      list.hidden = false;
    }

    function add(value) {
      const exact = options.find((option) => normalize(option) === normalize(value));
      const firstSuggestion = list.hidden ? '' : list.firstElementChild.textContent;
      const key = exact || firstSuggestion;
      if (!key || selected.has(key)) return;
      selected.add(key);
      state[field].add(key);
      input.value = '';
      renderChips();
      renderSuggestions();
      apply();
      input.focus();
    }

    input.addEventListener('input', renderSuggestions);
    input.addEventListener('focus', renderSuggestions);

    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        add(input.value.trim());
      } else if (event.key === 'Backspace' && !input.value) {
        const last = Array.from(selected).pop();
        if (last) {
          selected.delete(last);
          state[field].delete(last);
          renderChips();
          apply();
        }
      } else if (event.key === 'Escape') {
        input.value = '';
        renderSuggestions();
      }
    });

    document.addEventListener('click', (event) => {
      if (!container.contains(event.target)) list.hidden = true;
    });

    renderChips();
    initial.forEach((value) => state[field].add(value));

    return function clear() {
      selected.clear();
      input.value = '';
      list.hidden = true;
      renderChips();
    };
  }

  // ── URL state (shareable result links) ──

  function restoreUrl() {
    const params = new URLSearchParams(window.location.search);
    state.query = params.get('q') || '';
    dom.search.value = state.query;

    ['category', 'type', 'on_who'].forEach((field) => {
      (params.get(field) || '').split(',').filter(Boolean).forEach((value) => state[field].add(value));
    });

    (params.get('author') || '').split(',').filter(Boolean).forEach((value) => {
      const match = authors.find((author) => normalize(author) === normalize(value));
      if (match) state.author.add(match);
    });

    // Any unmatched tag in the URL would never match a song.
    ['category', 'type', 'on_who', 'author'].forEach((field) => {
      const vocabulary = field === 'category' ? DS.categories
        : field === 'type' ? DS.types
        : field === 'on_who' ? onWhoOptions
        : authors;
      Array.from(state[field]).forEach((value) => {
        if (!vocabulary.some((option) => normalize(option) === normalize(value))) {
          state[field].delete(value);
        }
      });
    });
  }

  function restoreControls() {
    ['category', 'type'].forEach((field) => {
      const container = field === 'category' ? dom.category : dom.type;
      Array.from(container.querySelectorAll('input')).forEach((input) => {
        input.checked = state[field].has(input.value);
      });
    });
  }

  function reset() {
    state.query = '';
    ['category', 'type', 'on_who', 'author'].forEach((field) => state[field].clear());
    dom.search.value = '';
    [dom.category, dom.type].forEach((container) => {
      container.querySelectorAll('input').forEach((input) => { input.checked = false; });
    });
    clearTags.forEach((clear) => clear());
    apply();
  }

  // ── Init ──

  function init() {
    restoreUrl();

    buildCheckboxes(dom.category, DS.categories, 'category');
    buildCheckboxes(dom.type, DS.types, 'type');

    const clearTags = [
      buildTagInput(dom.onWho, onWhoOptions, Array.from(state.on_who)),
      buildTagInput(dom.author, authors, Array.from(state.author))
    ];

    restoreControls();

    dom.search.addEventListener('input', () => {
      state.query = dom.search.value;
      apply();
    });

    dom.reset.addEventListener('click', () => {
      reset();
      dom.search.focus();
    });

    document.addEventListener('keydown', (event) => {
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