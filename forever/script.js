// Forever profile is independent from the Retail data.json.
const fields = {name:'char-name',level:'char-level',honorableKills:'char-honorable-kills',talents:'char-talents',makgoraKills:'char-makgora-kills',itemLevel:'char-item-level'};
const note = document.getElementById('source-note');
fetch('./data.json', {cache:'no-store'})
  .then(response => {if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json();})
  .then(data => {
    for (const [key,id] of Object.entries(fields)) {
      const value = data[key];
      if (value === null || value === undefined || value === '') continue;
      const node = document.getElementById(id);
      if (node) node.textContent = String(value);
    }
    const role = document.getElementById('char-role');
    if (role && data.class && data.race) role.textContent = `${data.class} · ${data.race}`;
    const portrait = document.getElementById('forever-portrait');
    if (portrait && typeof data.portraitUrl === 'string' && /^https:\/\//i.test(data.portraitUrl)) {
      portrait.onerror = () => {portrait.onerror = null; portrait.src = './assets/avatar.png';};
      portrait.src = data.portraitUrl;
    }
    if (note) note.textContent = data.updatedAt
      ? `Forever profile data updated: ${data.updatedAt}. Source: Raider.IO.`
      : 'Forever character profile data from Raider.IO.';
  })
  .catch(() => {if (note) note.textContent = 'Forever API data unavailable. View the Raider.IO profile for current character information.';});
