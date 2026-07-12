/* Daasa Saahitya - Index page functionality */
(function() {
  'use strict';

  function initIndex() {
    var searchInput = document.getElementById('search-input');
    var resultsCount = document.getElementById('search-results-count');
    var songs = document.querySelectorAll('.song-entry');
    var folders = document.querySelectorAll('.folder-section');

    if (!searchInput) return;

    // Collapsible folders - collapsed by default
    var headers = document.querySelectorAll('.folder-header');
    for (var i = 0; i < headers.length; i++) {
      (function(header) {
        var toggle = document.createElement('span');
        toggle.className = 'folder-toggle';
        toggle.textContent = '\u25BC';
        header.appendChild(toggle);

        // Start collapsed
        header.parentElement.classList.add('collapsed');

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
        for (var i = 0; i < folders.length; i++) {
          folders[i].classList.remove('hidden');
          folders[i].classList.add('collapsed');
        }
        resultsCount.classList.remove('visible');
        return;
      }

      var matchCount = 0;

      // Match songs
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

      // Show folders that contain visible songs (walk bottom-up)
      // First hide all folders
      for (var i = 0; i < folders.length; i++) {
        folders[i].classList.add('hidden');
        folders[i].classList.remove('collapsed');
      }

      // Then unhide any folder containing visible songs or visible child folders
      var changed = true;
      while (changed) {
        changed = false;
        for (var i = 0; i < folders.length; i++) {
          var folder = folders[i];
          var visibleSongs = folder.querySelectorAll(':scope > .folder-content > .song-entry:not(.hidden)');
          var visibleChildren = folder.querySelectorAll(':scope > .folder-content > .folder-section:not(.hidden)');
          if (visibleSongs.length > 0 || visibleChildren.length > 0) {
            if (folder.classList.contains('hidden')) {
              folder.classList.remove('hidden');
              changed = true;
            }
          }
        }
      }

      // Also check if folder name matches
      for (var i = 0; i < folders.length; i++) {
        var folder = folders[i];
        var nameEl = folder.querySelector(':scope > .folder-header > .folder-name');
        var name = nameEl ? nameEl.textContent.toLowerCase() : '';
        if (name.indexOf(query) !== -1) {
          folder.classList.remove('hidden');
          folder.classList.remove('collapsed');
          // Show all songs inside
          var innerSongs = folder.querySelectorAll('.song-entry');
          for (var j = 0; j < innerSongs.length; j++) {
            innerSongs[j].classList.remove('hidden');
            matchCount++;
          }
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
