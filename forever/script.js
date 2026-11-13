// Forever profile is independent from the Retail data.json.
const fields = {name:'char-name',level:'char-level',talents:'char-talents',itemLevel:'char-item-level'};
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
    const professions = Array.isArray(data.professions) ? data.professions : [];
    for (let i = 0; i < 2; i++) {
      const item = professions[i];
      const nameNode = document.getElementById(`char-profession-${i+1}-name`);
      const skillNode = document.getElementById(`char-profession-${i+1}-skill`);
      if (!item || typeof item.name !== 'string' || !Number.isInteger(item.skill) ||
          !Number.isInteger(item.maxSkill) || item.maxSkill <= 0 || item.skill > item.maxSkill) continue;
      if (nameNode) nameNode.textContent = item.name;
      if (skillNode) skillNode.textContent = `${item.skill} / ${item.maxSkill}`;
    }
    const role = document.getElementById('char-role');
    if (role && data.class && data.race) role.textContent = `${data.class} · ${data.race}`;
    const portrait = document.getElementById('forever-portrait');
    if (portrait && typeof data.portraitUrl === 'string' && /^https:\/\//i.test(data.portraitUrl)) {
      portrait.onerror = () => {portrait.onerror = null; portrait.src = './assets/avatar.png';};
      portrait.src = data.portraitUrl;
    }
    if (note) note.textContent = data.updatedAt
      ? `Forever profile data updated: ${data.updatedAt}. Source: Raider.IO / Blizzard Forever API.`
      : 'Forever character profile data from Raider.IO / Blizzard Forever API.';
  })
  .catch(() => {if (note) note.textContent = 'Forever API data unavailable. View the Raider.IO profile for current character information.';});
