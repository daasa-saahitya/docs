// -------- INDEX PAGE --------
const menuDiv = document.getElementById("menu");

if (menuDiv) {
  fetch("./songs/songs.json")
    .then(res => res.json())
    .then(data => {
      for (let group in data) {
        const groupDiv = document.createElement("div");
        groupDiv.className = "group";

        const heading = document.createElement("h2");
        heading.innerText = group;
        groupDiv.appendChild(heading);

        data[group].forEach(song => {
          const link = document.createElement("a");
          link.href = `song.html?file=${song.file}`;
          link.innerText = song.title;
          link.className = "song-link";
          groupDiv.appendChild(link);
        });

        menuDiv.appendChild(groupDiv);
      }
    });
}

// -------- SONG PAGE --------
const params = new URLSearchParams(window.location.search);
const filePath = params.get("file");

let lyricsData = {};
let currentScript = "kannada";

if (filePath) {
  fetch(`./songs/${filePath}`)
    .then(res => res.text())
    .then(text => parseMarkdown(text));
}

function parseMarkdown(text) {
  /* ---- Title ---- */
  const titleMatch = text.match(/^title:\s*(.*)$/m);
  if (titleMatch) {
    document.getElementById("songTitle").innerText = titleMatch[1].trim();
  }

  /* ---- Subtitle ---- */
  const subtitleMatch = text.match(/^subtitle:\s*(.*)$/m);
  const subtitleEl = document.getElementById("songSubtitle");

  if (subtitleMatch && subtitleEl) {
    subtitleEl.innerText = subtitleMatch[1].trim();
    subtitleEl.style.display = "block";
  } else if (subtitleEl) {
    subtitleEl.style.display = "none"; // hide if not present
  }

  /* ---- Lyrics Sections ---- */
  const sections = text.split("## ").slice(1);
  sections.forEach(section => {
    const [key, ...content] = section.split("\n");
    lyricsData[key.trim()] = content.join("\n").trim();
  });

  showScript(currentScript);
}

function showScript(script) {
  currentScript = script;
  document.getElementById("lyrics").innerText =
    lyricsData[script] || "Lyrics not available.";
  
  lyricsEl.className = scriptName;
}