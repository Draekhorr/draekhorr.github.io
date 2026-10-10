const el=id=>document.getElementById(id);
function setValue(id,value){if(value===null||value===undefined||value==='')return;el(id).textContent=typeof value==='number'?value.toLocaleString('en-US'):String(value)}
function setCards(id,items,fallback){if(!Array.isArray(items)||!items.length)return;const parent=el(id);parent.replaceChildren();for(const item of items){const card=document.createElement('article');card.className='data-card';const title=document.createElement('h4');title.textContent=item.name||'Unnamed';card.append(title);if(item.note){const note=document.createElement('p');note.textContent=item.note;card.append(note)}if(item.url&&/^https:\/\//i.test(item.url)){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='VIEW DETAILS ↗';card.append(link)}parent.append(card)}}
function safeLink(id,url){if(typeof url==='string'&&/^https:\/\//i.test(url))el(id).href=url}
fetch('data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}).then(d=>{
 setValue('mounts-count',d.accountWideMountCount??d.mountCount);setValue('points',d.achievementPoints);
 const mounts=d.mounts||[];if(mounts.length)setValue('rare-count',mounts.filter(x=>x.rare).length);setCards('mount-list',mounts);setCards('achievement-list',d.achievements);if(d.achievements?.length)setValue('achievement-count',d.achievements.length);
 const ce=(d.cuttingEdgeAchievements||[]).filter(x=>x.verified===true);if(ce.length){setValue('ce-count',ce.length);const tiers=ce.map(x=>x.tierId).filter(Boolean);if(tiers.length)setValue('ce-tier-count',new Set(tiers).size)}setCards('ce-list',ce);renderRaids(d);safeLink('raid-source-link',d.raidSourceUrl);
 setValue('wcl-best',d.warcraftLogs?.bestPerformanceAverage);setValue('wcl-median',d.warcraftLogs?.medianPerformanceAverage);setCards('wcl-parses',d.warcraftLogs?.bossParses);safeLink('wcl-link',d.warcraftLogs?.profileUrl);
 setValue('rio-score',d.raiderIo?.currentSeasonScore??d.raiderIo?.mythicPlusScore);setValue('rio-previous',d.raiderIo?.previousSeasonScore);setValue('rio-rank',d.raiderIo?.ranking);setCards('rio-runs',d.raiderIo?.bestRuns);safeLink('rio-link',d.raiderIo?.profileUrl);safeLink('wowprogress-link',d.wowprogress?.profileUrl);
 if(d.updatedAt)el('status').textContent='Data updated: '+d.updatedAt;
}).catch(()=>{el('status').textContent='Data unavailable. Use GitHub Pages or a local web server.'});

// Current raid season display and historical expansion dropdowns.
// Explicit mapping is a temporary fallback for the current legacy JSON format.
const RAID_MAP={
 'the venomous abyss':{expansion:'Midnight',season:'Season 2',current:true},
 'the tidebound grotto':{expansion:'Midnight',season:'Season 2',current:true},
 'sporefall':{expansion:'Midnight',season:'Season 1',current:false},
 'tier mn 1':{expansion:'Midnight',season:'Season 1',current:false}
};
function makeRaidCard(raid){
 const card=document.createElement('article');card.className='data-card';
 const h=document.createElement('h4');h.textContent=raid.name||'Unnamed raid';card.append(h);
 if(raid.note){const p=document.createElement('p');p.textContent=raid.note;card.append(p)}
 if(raid.url&&/^https:\/\//.test(raid.url)){const a=document.createElement('a');a.href=raid.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='VIEW DETAILS ↗';card.append(a)}
 return card;
}
function renderRaids(data){
 const current=el('raid-list'),history=el('raid-history');
 current.replaceChildren();history.replaceChildren();
 const raids=Array.isArray(data.raidProgression)?data.raidProgression:[];
 const grouped=new Map();let count=0;
 const byExpansion=data.raidProgressionByExpansion;
 // Use the normalized backend format when available; legacy data uses known raid names.
 if(byExpansion&&typeof byExpansion==='object'){
  // Still use legacy entries for now unless a recognizable structured raids array exists.
  // This avoids silently dropping raids from differently shaped API sync versions.
 }
 for(const raid of raids){
  const key=String(raid.name||'').trim().toLowerCase();const meta=RAID_MAP[key];
  if(meta?.current){current.append(makeRaidCard(raid));count++;continue}
  const expansion=meta?.expansion||'Unclassified raids';const season=meta?.season||'Season unknown';
  if(!grouped.has(expansion))grouped.set(expansion,new Map());
  const seasons=grouped.get(expansion);if(!seasons.has(season))seasons.set(season,[]);
  seasons.get(season).push(raid);
 }
 if(!count){const p=document.createElement('p');p.className='empty-state';p.textContent='No current season raid progress available.';current.append(p)}
 for(const [expansion,seasons] of grouped){
  const details=document.createElement('details');details.className='expansion-dropdown';
  const summary=document.createElement('summary');summary.textContent=expansion;details.append(summary);
  for(const [season,entries] of seasons){const h=document.createElement('h5');h.textContent=season;details.append(h);
   const list=document.createElement('div');list.className='raid-items';for(const raid of entries)list.append(makeRaidCard(raid));details.append(list)}
  history.append(details);
 }
 if(!grouped.size){const p=document.createElement('p');p.className='empty-state';p.textContent='No historical raid data available yet.';history.append(p)}
}
