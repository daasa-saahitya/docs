/* Daasa Saahitya - Index page functionality */
(function() {
  'use strict';

  function initIndex() {
    var searchInput = document.getElementById('search-input');
    var resultsCount = document.getElementById('search-results-count');
    var songs = document.querySelectorAll('.song-entry');
    var categories = document.querySelectorAll('.category-section');
    var subcategories = document.querySelectorAll('.subcategory-section');

    if (!searchInput) return;

    // Collapsible categories
    var headers = document.querySelectorAll('.category-header');
    for (var i = 0; i < headers.length; i++) {
      (function(header) {
        var toggle = document.createElement('span');
        toggle.className = 'category-toggle';
        toggle.textContent = '▼';
        header.appendChild(toggle);

        header.addEventListener('click', function() {
          header.parentElement.classList.toggle('collapsed');
        });
      })(headers[i]);
    }

    // Search functionality
    searchInput.addEventListener('input', function() {
      var query = this.value.toLowerCase().trim();

      if (!query) {
        for (var i = 0; i < songs.length; i++) {
          songs[i].classList.remove('hidden');
        }
        for (var i = 0; i < categories.length; i++) {
          categories[i].classList.remove('hidden');
        }
        for (var i = 0; i < subcategories.length; i++) {
          subcategories[i].classList.remove('hidden');
        }
        resultsCount.classList.remove('visible');
        return;
      }

      var matchCount = 0;

      for (var i = 0; i < songs.length; i++) {
        var song = songs[i];
        var titleEl = song.querySelector('.song-entry-main');
        var authorEl = song.querySelector('.song-entry-author');
        var title = titleEl ? titleEl.textContent.toLowerCase() : '';
        var author = authorEl ? authorEl.textContent.toLowerCase() : '';
        var matches = title.indexOf(query) !== -1 || author.indexOf(query) !== -1;

        if (matches) {
          song.classList.remove('hidden');
          matchCount++;
        } else {
          song.classList.add('hidden');
        }
      }

      // Hide empty subcategories
      for (var i = 0; i < subcategories.length; i++) {
        var subcat = subcategories[i];
        var visibleSongs = subcat.querySelectorAll('.song-entry:not(.hidden)');
        if (visibleSongs.length === 0) {
          subcat.classList.add('hidden');
        } else {
          subcat.classList.remove('hidden');
        }
      }

      // Hide empty categories
      for (var i = 0; i < categories.length; i++) {
        var cat = categories[i];
        var catNameEl = cat.querySelector('.category-name');
        var catName = catNameEl ? catNameEl.textContent.toLowerCase() : '';
        var visibleSongs = cat.querySelectorAll('.song-entry:not(.hidden)');
        var nameMatch = catName.indexOf(query) !== -1;

        if (nameMatch) {
          cat.classList.remove('hidden');
          var allSongs = cat.querySelectorAll('.song-entry');
          for (var j = 0; j < allSongs.length; j++) {
            allSongs[j].classList.remove('hidden');
          }
          var allSubcats = cat.querySelectorAll('.subcategory-section');
          for (var j = 0; j < allSubcats.length; j++) {
            allSubcats[j].classList.remove('hidden');
          }
          matchCount = allSongs.length;
        } else if (visibleSongs.length === 0) {
          cat.classList.add('hidden');
        } else {
          cat.classList.remove('hidden');
        }
      }

      resultsCount.textContent = matchCount === 0 ? 'No matches found' : matchCount + ' result' + (matchCount !== 1 ? 's' : '') + ' found';
      resultsCount.classList.add('visible');
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
      if (e.key === '/' && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
      if (e.key === 'Escape' && document.activeElement === searchInput) {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
        searchInput.blur();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initIndex);
  } else {
    initIndex();
  }
})();
