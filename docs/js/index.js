/* Daasa Saahitya - index filters */
(function () {
  'use strict';

  const DS = window.DS_INDEX;
  if (!DS) return;

  // Strip case and combining marks so "rāma" matches a typed "rama".
  const normalize = (text) =>
    String(text || '').toLowerCase().replace(/[̀-ͯ]/g, '');

  const asList = (value) =>
    Array.isArray(value) ? value : (value ? [value] : []);

  // Every filter is a tag input. `song` says which song fields a filter reads:
  // author and ankita are single strings, the rest are lists.
  const FIELDS = [
    { key: 'on_who',    el: 'filter-on',        song: (s) => s.on_who },
    { key: 'category',  el: 'filter-category',  song: (s) => s.category },
    { key: 'type',      el: 'filter-type',      song: (s) => s.types },
    { key: 'festivals', el: 'filter-festivals', song: (s) => s.festivals },
    { key: 'author',    el: 'filter-author',    song: (s) => s.author },
    { key: 'ankita',    el: 'filter-ankita',    song: (s) => s.ankita }
  ];

  const songs = DS.songs.map((song) => {
    song.category = asList(song.category);
    song.types = asList(song.types);
    song.on_who = asList(song.on_who);
    song.festivals = asList(song.festivals);
    song.ankita = song.ankita || '';
    song.haystack = normalize(
      (song.title || '') + ' ' + (song.author || '') + ' ' +
      (song.ankita || '') + ' ' + (song.preview || '')
    );
    song.keys = {};
    return song;
  });

  const state = { query: '' };

  FIELDS.forEach((field) => {
    state[field.key] = new Set();

    // Which normalised values the songs actually use, and how to spell them.
    const used = new Map(); // normalised -> first spelling seen
    songs.forEach((song) => {
      const keys = new Set();
      asList(field.song(song)).forEach((value) => {
        const key = normalize(value);
        if (!key) return;
        keys.add(key);
        if (!used.has(key)) used.set(key, value);
      });
      song.keys[field.key] = keys;
    });

    // The canonical vocabulary first, in the order scripts/align.py declares it,
    // then anything the songs use that is not on the list. That way a song still
    // tagged with the older wording ("Devaru", "Sampradaya Haadu") stays
    // filterable until it is re-tagged by hand.
    const canonical = (DS.vocabularies && DS.vocabularies[field.key]) || [];
    const options = [];
    const taken = new Set();

    canonical.forEach((value) => {
      const key = normalize(value);
      if (!key || taken.has(key)) return;
      taken.add(key);
      options.push(value);
    });

    const extras = [];
    used.forEach((value, key) => {
      if (!taken.has(key)) extras.push(value);
    });
    extras.sort((a, b) => a.localeCompare(b));
    field.options = options.concat(extras);
    field.display = new Map(); // normalised -> displayed spelling
    field.options.forEach((value) => field.display.set(normalize(value), value));
  });

  const dom = {
    search: document.getElementById('search-input'),
    searchButton: document.getElementById('search-button'),
    status: document.getElementById('filter-status'),
    list: document.getElementById('song-list'),
    empty: document.getElementById('empty-state'),
    reset: document.getElementById('reset-filters')
  };

  const clearTags = [];

  // ── Filtering ──

  function matchesField(song, field) {
    const chosen = state[field.key];
    if (!chosen.size) return true;
    for (const key of chosen) {
      if (song.keys[field.key].has(key)) return true;
    }
    return false;
  }

  function visible() {
    const terms = normalize(state.query).split(/\s+/).filter(Boolean);

    return songs.filter((song) => {
      if (!terms.every((term) => song.haystack.includes(term))) return false;
      return FIELDS.every((field) => matchesField(song, field));
    });
  }

  function activeCount() {
    const chosen = FIELDS.reduce((total, field) => total + state[field.key].size, 0);
    return chosen + (state.query.trim() ? 1 : 0);
  }

  function syncUrl() {
    const params = new URLSearchParams();
    if (state.query.trim()) params.set('q', state.query.trim());

    FIELDS.forEach((field) => {
      const values = Array.from(state[field.key]);
      if (values.length) params.set(field.key, values.join(','));
    });

    const query = params.toString();
    window.history.replaceState(null, '', window.location.pathname + (query ? '?' + query : ''));
  }

  // Results are only refreshed when Search is pressed, so half-finished
  // filter selections never change the list under the user.
  function apply() {
    state.query = dom.search.value;
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

  // ── Tag autocomplete ──

  function buildTagInput(container, field) {
    // selected: normalised -> displayed value
    const selected = new Map();

    // The legend is a sibling, and the group is no longer a <fieldset>, so the
    // input needs its own accessible name.
    const legend = container.parentElement
      && container.parentElement.querySelector('.filter-legend');
    const label = legend ? legend.textContent.trim() : field.key;

    const chips = document.createElement('div');
    chips.className = 'tag-chips';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'tag-field';
    input.autocomplete = 'off';
    input.placeholder = 'Type to search…';
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-label', label);
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');

    const list = document.createElement('ul');
    list.className = 'tag-suggestions';
    list.setAttribute('role', 'listbox');
    list.setAttribute('aria-label', label);
    list.hidden = true;

    container.append(chips, input, list);

    function showSuggestions() {
      list.hidden = false;
      input.setAttribute('aria-expanded', 'true');
    }

    function hideSuggestions() {
      list.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }

    function select(value) {
      const key = normalize(value);
      if (!key || selected.has(key)) return;
      selected.set(key, field.display.get(key) || value);
      state[field.key].add(key);
    }

    function deselect(key) {
      selected.delete(key);
      state[field.key].delete(key);
    }

    function renderChips() {
      chips.textContent = '';
      selected.forEach((value, key) => {
        const chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.appendChild(document.createTextNode(value));

        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'tag-remove';
        remove.textContent = '×';
        remove.setAttribute('aria-label', 'Remove ' + value);
        remove.addEventListener('click', () => {
          deselect(key);
          renderChips();
          input.focus();
        });

        chip.appendChild(remove);
        chips.appendChild(chip);
      });
    }

    function highlight(item) {
      Array.from(list.children).forEach((child) => {
        child.classList.remove('is-active');
        child.setAttribute('aria-selected', 'false');
      });
      item.classList.add('is-active');
      item.setAttribute('aria-selected', 'true');
      list.dataset.active = item.textContent;
      input.setAttribute('aria-activedescendant', item.id);
    }

    function renderSuggestions() {
      const query = normalize(input.value.trim());
      list.textContent = '';

      const found = field.options.filter((option) => {
        const key = normalize(option);
        return !selected.has(key) && (!query || key.includes(query));
      }).slice(0, 40);

      if (!found.length) {
        hideSuggestions();
        delete list.dataset.active;
        input.removeAttribute('aria-activedescendant');
        return;
      }

      found.forEach((option, index) => {
        const item = document.createElement('li');
        item.className = 'tag-suggestion';
        item.id = field.key + '-option-' + index;
        item.textContent = option;
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', 'false');
        // mousedown, so the input cannot blur before the click lands.
        item.addEventListener('mousedown', (event) => {
          event.preventDefault();
          add(option);
        });
        list.appendChild(item);
      });

      showSuggestions();

      // Only auto-highlight once there is a query or a single hit, otherwise the
      // highlighted row would jump around while typing.
      if (query || found.length === 1) highlight(list.firstElementChild);
      else {
        delete list.dataset.active;
        input.removeAttribute('aria-activedescendant');
      }
    }

    function add(typed) {
      const exact = field.options.find((option) => normalize(option) === normalize(typed));
      const highlighted = list.hidden ? '' : list.dataset.active;
      if (exact) select(exact);
      else if (highlighted) select(highlighted);
      else return;

      input.value = '';
      renderChips();
      renderSuggestions();
      input.focus();
    }

    input.addEventListener('input', renderSuggestions);
    input.addEventListener('focus', renderSuggestions);

    input.addEventListener('keydown', (event) => {
      const items = Array.from(list.children);

      if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        add(input.value.trim());
      } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        if (list.hidden || !items.length) return;
        event.preventDefault();
        const current = Array.from(items).indexOf(list.querySelector('.is-active'));
        let next = event.key === 'ArrowDown' ? 0 : items.length - 1;
        if (current !== -1) {
          const step = event.key === 'ArrowDown' ? 1 : -1;
          next = (current + step + items.length) % items.length;
        }
        highlight(items[next]);
      } else if (event.key === 'Backspace' && !input.value) {
        const last = Array.from(selected.keys()).pop();
        if (last) {
          deselect(last);
          renderChips();
        }
      } else if (event.key === 'Escape') {
        input.value = '';
        renderSuggestions();
      }
    });

    document.addEventListener('click', (event) => {
      if (!container.contains(event.target)) hideSuggestions();
    });

    // Anything restored from the URL starts out already selected.
    Array.from(state[field.key]).forEach((key) => {
      if (field.display.has(key)) select(field.display.get(key));
    });
    renderChips();

    return function clear() {
      selected.clear();
      state[field.key].clear();
      input.value = '';
      hideSuggestions();
      renderChips();
    };
  }

  // ── URL state (shareable result links) ──

  function restoreUrl() {
    const params = new URLSearchParams(window.location.search);
    state.query = params.get('q') || '';
    dom.search.value = state.query;

    FIELDS.forEach((field) => {
      (params.get(field.key) || '').split(',').filter(Boolean).forEach((value) => {
        const key = normalize(value);
        // A tag that is not on the list could never match a song, so drop it
        // rather than leave a chip the user cannot remove.
        if (field.display.has(key)) state[field.key].add(key);
      });
    });
  }

  function reset() {
    state.query = '';
    FIELDS.forEach((field) => state[field.key].clear());
    dom.search.value = '';
    clearTags.forEach((clear) => clear());
    apply();
  }

  // ── Init ──

  function init() {
    restoreUrl();

    FIELDS.forEach((field) => {
      const container = document.getElementById(field.el);
      if (container) clearTags.push(buildTagInput(container, field));
    });

    const runSearch = () => apply();

    dom.search.addEventListener('input', () => { state.query = dom.search.value; });
    dom.search.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') { event.preventDefault(); runSearch(); }
    });

    dom.searchButton.addEventListener('click', runSearch);

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