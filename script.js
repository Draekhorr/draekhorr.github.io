const el=id=>document.getElementById(id);
function setValue(id,value){if(value===null||value===undefined||value==='')return;el(id).textContent=typeof value==='number'?value.toLocaleString('en-US'):String(value)}
function setCards(id,items,fallback){if(!Array.isArray(items)||!items.length)return;const parent=el(id);parent.replaceChildren();for(const item of items){const card=document.createElement('article');card.className='data-card';const title=document.createElement('h4');title.textContent=item.name||'Unnamed';card.append(title);if(item.note){const note=document.createElement('p');note.textContent=item.note;card.append(note)}if(item.url&&/^https:\/\//i.test(item.url)){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='VIEW DETAILS ↗';card.append(link)}parent.append(card)}}
function safeLink(id,url){if(typeof url==='string'&&/^https:\/\//i.test(url))el(id).href=url}
fetch('data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}).then(d=>{
 setValue('mounts-count',d.accountWideMountCount??d.mountCount);setValue('points',d.achievementPoints);
 const mounts=d.mounts||[];if(mounts.length)setValue('rare-count',mounts.filter(x=>x.rare).length);setCards('mount-list',mounts);setCards('achievement-list',d.achievements);if(d.achievements?.length)setValue('achievement-count',d.achievements.length);
 const ce=(d.cuttingEdgeAchievements||[]).filter(x=>x.verified===true);if(ce.length){setValue('ce-count',ce.length);const tiers=ce.map(x=>x.tierId).filter(Boolean);if(tiers.length)setValue('ce-tier-count',new Set(tiers).size)}setCards('ce-list',ce);renderRaids(d);safeLink('raid-source-link',d.raidSourceUrl);
 renderWclBosses(d.warcraftLogs?.bossParses);safeLink('wcl-link',d.warcraftLogs?.profileUrl);
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
 if(!current||!history)return;
 current.replaceChildren();history.replaceChildren();
 const grouped=new Map(), seen=new Set();
 const currentNames=new Set();
 const add=(expansion,season,raid)=>{
  if(!raid||!raid.name)return;
  if(currentNames.has(String(raid.name).trim().toLowerCase()))return;
  if(/^(current season|season-mn-2|midnight season 2)$/i.test(String(season).trim()))return;
  const key=[expansion,season,raid.name].join('|').toLowerCase();
  if(seen.has(key))return;
  seen.add(key);
  if(!grouped.has(expansion))grouped.set(expansion,new Map());
  const seasons=grouped.get(expansion);
  if(!seasons.has(season))seasons.set(season,[]);
  seasons.get(season).push(raid);
 };
 const by=data.raidProgressionByExpansion||{};
 const normalizedCurrent=by.currentSeason?.raids;
 const legacy=Array.isArray(data.raidProgression)?data.raidProgression:[];
 const currentRaids=Array.isArray(normalizedCurrent)&&normalizedCurrent.length?normalizedCurrent:legacy.filter(r=>RAID_MAP[String(r.name||'').trim().toLowerCase()]?.current);
 for(const raid of currentRaids){currentNames.add(String(raid.name||'').trim().toLowerCase());current.append(makeRaidCard(raid));}
 if(!currentRaids.length){const p=document.createElement('p');p.className='empty-state';p.textContent='No verified current-season raid progress available.';current.append(p)}
 if(el('raid-current-season'))el('raid-current-season').textContent=(by.currentSeason?.seasonName||data.raiderIo?.currentSeasonName||'CURRENT SEASON').toUpperCase();
 // Backend expansion history: expansion -> [{seasonName, raids}].
 const historyData=by.history||{};
 for(const [expansion,groups] of Object.entries(historyData)){
  if(Array.isArray(groups))for(const group of groups){
   if(!group||!Array.isArray(group.raids))continue;
   for(const raid of group.raids)add(expansion,group.seasonName||'Historical raids',raid);
  }
 }
 // Raw Blizzard historical data: expansion -> [raid]. Also works if grouped history is empty.
 const historical=data.historicalRaidProgression||{};
 for(const [expansion,raids] of Object.entries(historical)){
  if(!Array.isArray(raids))continue;
  for(const raid of raids){
   if(!raid||!['MYTHIC','HEROIC'].includes(String(raid.difficulty||'').toUpperCase()))continue;
   if(expansion==='Midnight')continue;
   add(expansion,'Historical raids',raid);
  }
 }
 // Fallback for old data.json, until the backend populates historical data.
 for(const raid of legacy){
  const key=String(raid.name||'').trim().toLowerCase(),meta=RAID_MAP[key];
  if(meta?.current||currentNames.has(key))continue;
  add(meta?.expansion||'Unclassified raids',meta?.season||'Season unknown',raid);
 }
 const priority=['Midnight','The War Within','Dragonflight','Shadowlands','Battle for Azeroth','Legion','Warlords of Draenor','Mists of Pandaria','Cataclysm','Wrath of the Lich King','The Burning Crusade','Classic','Unclassified raids'];
 for(const expansion of [...grouped.keys()].sort((a,b)=>{
  const ia=priority.indexOf(a),ib=priority.indexOf(b);
  return (ia<0?999:ia)-(ib<0?999:ib)||a.localeCompare(b);
 })){
  const details=document.createElement('details');details.className='expansion-dropdown';
  const summary=document.createElement('summary');summary.textContent=expansion;details.append(summary);
  for(const [season,entries] of grouped.get(expansion)){
   const h=document.createElement('h5');h.textContent=season;details.append(h);
   const list=document.createElement('div');list.className='raid-items';
   for(const raid of entries)list.append(makeRaidCard(raid));
   details.append(list);
  }
  history.append(details);
 }
 if(!grouped.size){const p=document.createElement('p');p.className='empty-state';p.textContent='Historical raids will appear after the Blizzard sync returns confirmed Mythic/Heroic progression.';history.append(p)}
}

// WCL: display per-boss healing results, never invent missing HPS.
function renderWclBosses(items){
 const tbody=el('wcl-parses');if(!tbody)return;tbody.replaceChildren();
 if(!Array.isArray(items)||!items.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=3;td.className='empty-state';td.textContent='No Warcraft Logs boss data available.';tr.append(td);tbody.append(tr);return;}
 for(const boss of items){
  const tr=document.createElement('tr');
  const name=document.createElement('td');
  const link=(typeof boss.url==='string'&&/^https:\/\//i.test(boss.url))?document.createElement('a'):document.createElement('span');
  if(link.tagName==='A'){link.href=boss.url;link.target='_blank';link.rel='noopener noreferrer';}
  link.textContent=boss.name||'Unknown boss';name.append(link);
  const pct=document.createElement('td');pct.className='wcl-value';
  let score=Number.isFinite(Number(boss.bestPercent))&&boss.bestPercent!==null&&boss.bestPercent!==undefined?Number(boss.bestPercent):null;
  if(score===null){const match=String(boss.note||'').match(/Rank percentile:\s*([\d.]+)/i);if(match)score=Number(match[1]);}
  pct.textContent=score===null?'—':Math.round(score).toLocaleString('en-US');
  if(score!==null){pct.classList.add(score>=95?'parse-legendary':score>=75?'parse-epic':score>=50?'parse-rare':score>=25?'parse-uncommon':'parse-common');}
  const hps=document.createElement('td');hps.className='wcl-value wcl-hps';
  const n=boss.highestHps;hps.textContent=(typeof n==='number'&&Number.isFinite(n))?n.toLocaleString('en-US',{maximumFractionDigits:1}):'—';
  tr.append(name,pct,hps);tbody.append(tr);
 }
}
