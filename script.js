const el=id=>document.getElementById(id);
function setValue(id,value){if(value===null||value===undefined||value==='')return;el(id).textContent=typeof value==='number'?value.toLocaleString('en-US'):String(value)}
function setCards(id,items,fallback){if(!Array.isArray(items)||!items.length)return;const parent=el(id);parent.replaceChildren();for(const item of items){const card=document.createElement('article');card.className='data-card';const title=document.createElement('h4');title.textContent=item.name||'Unnamed';card.append(title);if(item.note){const note=document.createElement('p');note.textContent=item.note;card.append(note)}if(item.url&&/^https:\/\//i.test(item.url)){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='VIEW DETAILS ↗';card.append(link)}parent.append(card)}}
function safeLink(id,url){if(typeof url==='string'&&/^https:\/\//i.test(url))el(id).href=url}
fetch('data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}).then(d=>{
 const ce=(d.cuttingEdgeAchievements||[]).filter(x=>x.verified===true);setValue('ce-count',new Set(ce.map(x=>String(x.tierId)).filter(Boolean)).size);collectVerifiedCuttingEdges(ce);renderRaids(d);safeLink('raid-source-link',d.raidSourceUrl);
 renderWclHistory(d.warcraftLogs,d);safeLink('wcl-link',d.warcraftLogs?.profileUrl);
 renderCharacter(d.character,d.achievementPoints);renderRaiderIo(d.raiderIo,d.warcraftLogs);safeLink('rio-link',d.raiderIo?.profileUrl);
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
// Only the Blizzard Cutting Edge achievement list can award a CE badge.
// Raid progress (including full Mythic clears) NEVER grants Cutting Edge.
// Verified achievement ID -> historical raid name. Unknown IDs get no badge
// until an authoritative raid mapping is added; this prevents false positives.
const CE_RAID_IDS={
 '11191':'The Emerald Nightmare',
 '11580':'Trial of Valor',
 '11192':'The Nighthold',
 '13323':"Battle of Dazar'alor",
 '14069':"Ny'alotha, the Waking City",
 '14461':'Castle Nathria',
 '15135':'Sanctum of Domination',
 '18254':'Aberrus, the Shadowed Crucible',
 '19351':"Amirdrassil, the Dream's Hope",
 '40254':"Nerub-ar Palace",
 '41297':'Liberation of Undermine',
 '41625':'Manaforge Omega'
};
let verifiedCeByRaid=new Map();
function normalizeRaidName(value){return String(value||'').toLowerCase().replace(/[’‘`]/g,"'").replace(/[^a-z0-9]+/g,' ').trim();}
function collectVerifiedCuttingEdges(achievements){
 verifiedCeByRaid=new Map();
 for(const achievement of Array.isArray(achievements)?achievements:[]){
  if(achievement?.verified!==true)continue;
  const raid=CE_RAID_IDS[String(achievement.tierId)];
  if(!raid)continue;
  verifiedCeByRaid.set(normalizeRaidName(raid),achievement);
 }
}
function makeRaidCard(raid){
 const card=document.createElement('article');card.className='data-card';
 const h=document.createElement('h4');h.textContent=raid.name||'Unnamed raid';card.append(h);
 if(raid.note||verifiedCeByRaid.has(normalizeRaidName(raid.name))){const p=document.createElement('p');p.className='raid-progress-line';if(raid.note){const progress=document.createElement('span');progress.textContent=raid.note;p.append(progress)}const achievement=verifiedCeByRaid.get(normalizeRaidName(raid.name));if(achievement){const badge=document.createElement('a');badge.className='ce-badge';badge.textContent='CE';badge.title=achievement.name||'Verified Cutting Edge';badge.setAttribute('aria-label',badge.title);if(typeof achievement.url==='string'&&/^https:\/\//i.test(achievement.url)){badge.href=achievement.url;badge.target='_blank';badge.rel='noopener noreferrer';}p.append(badge)}card.append(p)}
 if(raid.url&&/^https:\/\//.test(raid.url)){const a=document.createElement('a');a.href=raid.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='VIEW DETAILS ↗';card.append(a)}
 return card;
}
function renderRaids(data){
 const current=el('raid-list'),history=el('raid-history'),selector=el('raid-expansion-select');
 if(!current||!history)return;
 current.replaceChildren();history.replaceChildren();if(selector)selector.replaceChildren(new Option('Select expansion...',''));
 const grouped=new Map(), seen=new Set();
 const currentNames=new Set();
 const add=(expansion,season,raid)=>{
  if(!raid||!raid.name)return;
  if(currentNames.has(String(raid.name).trim().toLowerCase()))return;
  if(String(season).trim().toLowerCase()===String(by.currentSeason?.seasonName||'').trim().toLowerCase() || String(season).trim()===String(by.currentSeason?.season||''))return;
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
 const currentRaids=Array.isArray(normalizedCurrent)?normalizedCurrent:legacy;
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
   if(expansion===by.currentSeason?.expansion)continue;
   add(expansion,'Historical raids',raid);
  }
 }
 // Fallback for old data.json, until the backend populates historical data.
 for(const raid of (Object.keys(historyData).length?[]:legacy)){
  const key=String(raid.name||'').trim().toLowerCase(),meta=RAID_MAP[key];
  if(meta?.current||currentNames.has(key))continue;
  add(meta?.expansion||'Unclassified raids',meta?.season||'Season unknown',raid);
 }
 const priority=['Midnight','The War Within','Dragonflight','Shadowlands','Battle for Azeroth','Legion','Warlords of Draenor','Mists of Pandaria','Cataclysm','Wrath of the Lich King','The Burning Crusade','Classic','Unclassified raids'];
 for(const expansion of [...grouped.keys()].sort((a,b)=>{
  const ia=priority.indexOf(a),ib=priority.indexOf(b);
  return (ia<0?999:ia)-(ib<0?999:ib)||a.localeCompare(b);
 })){
  const details=document.createElement('div');details.className='expansion-dropdown';details.dataset.expansion=expansion;details.hidden=true;
  if(selector)selector.add(new Option(expansion,expansion));
  for(const [season,entries] of grouped.get(expansion)){
   const h=document.createElement('h5');h.textContent=season;details.append(h);
   const list=document.createElement('div');list.className='raid-items';
   for(const raid of entries)list.append(makeRaidCard(raid));
   details.append(list);
  }
  history.append(details);
 }
 if(selector){selector.onchange=()=>{for(const section of history.querySelectorAll('[data-expansion]'))section.hidden=section.dataset.expansion!==selector.value;};}
 if(!grouped.size){const p=document.createElement('p');p.className='empty-state';p.textContent='Historical raids will appear after the Blizzard sync returns confirmed Mythic/Heroic progression.';history.append(p)}
}

// The selector replaces the current table; only recorded snapshots are offered.
// Only show archived zones that match a raid in Blizzard's raid progression.
// This filters out dungeon / Mythic+ zones even if the backfill stored them.
function knownRaidNames(data){
 const names=new Set();
 const add=raid=>{if(raid?.name)names.add(normalizeRaidName(raid.name));};
 const by=data?.raidProgressionByExpansion||{};
 (by.currentSeason?.raids||[]).forEach(add);
 for(const groups of Object.values(by.history||{})){
  if(Array.isArray(groups))for(const group of groups)(group?.raids||[]).forEach(add);
 }
 for(const raids of Object.values(data?.historicalRaidProgression||{})){
  if(Array.isArray(raids))raids.forEach(add);
 }
 (data?.raidProgression||[]).forEach(add);
 return names;
}
// Unified expansion headings, with no invented historical results.
const EXPANSION_ORDER=['Midnight','The War Within','Dragonflight','Shadowlands','Battle for Azeroth','Legion','Warlords of Draenor','Mists of Pandaria','Cataclysm','Wrath of the Lich King','The Burning Crusade','Classic'];
function expansionForRaid(name,data){
 const key=normalizeRaidName(name);
 const by=data?.raidProgressionByExpansion||{};
 const current=by.currentSeason;
 if((current?.raids||[]).some(r=>normalizeRaidName(r.name)===key))return current.expansion||'Current expansion';
 for(const [exp,groups] of Object.entries(by.history||{}))for(const group of Array.isArray(groups)?groups:[]){
  if((group.raids||[]).some(r=>normalizeRaidName(r.name)===key))return exp;
 }
 for(const [exp,raids] of Object.entries(data?.historicalRaidProgression||{})){
  if(Array.isArray(raids)&&raids.some(r=>normalizeRaidName(r.name)===key))return exp;
 }
 return null;
}
function expansionFromSeason(name){
 const label=String(name||'');
 return EXPANSION_ORDER.find(exp=>label.toLowerCase().includes(exp.toLowerCase()))||null;
}
function fillGroupedOptions(selector,records,currentId){
 selector.replaceChildren();
 const groups=new Map();
 for(const item of records){const group=item.expansion||'Other';if(!groups.has(group))groups.set(group,[]);groups.get(group).push(item);}
 const order=[...groups.keys()].sort((a,b)=>{
  const ai=EXPANSION_ORDER.indexOf(a),bi=EXPANSION_ORDER.indexOf(b);
  return (ai<0?999:ai)-(bi<0?999:bi)||a.localeCompare(b);
 });
 for(const name of order){
  const group=document.createElement('optgroup');group.label=name.toUpperCase();
  for(const item of groups.get(name))group.append(new Option(item.label+(item.id===currentId?' (Current)':''),item.id));
  selector.append(group);
 }
 selector.value=records.some(item=>item.id===currentId)?currentId:records[0]?.id||'';
 selector.disabled=records.length<=1;
}
function renderWclHistory(wcl,data){
 const selector=el('wcl-season-select');
 if(!selector){renderWclBosses(wcl?.bossParses);return;}
 const archive=wcl?.seasonArchive&&typeof wcl.seasonArchive==='object'?wcl.seasonArchive:{};
 const currentId=String(wcl?.currentSeasonId||'current');
 const raidNames=knownRaidNames(data);
 const records=[];
 for(const [id,entry] of Object.entries(archive)){
  if(!Array.isArray(entry?.bossParses)||!entry.bossParses.length)continue;
  const isCurrent=id===currentId;
  if(!isCurrent&&!raidNames.has(normalizeRaidName(entry.name)))continue;
  const expansion=isCurrent?(data?.raidProgressionByExpansion?.currentSeason?.expansion||expansionFromSeason(entry.name)):expansionForRaid(entry.name,data);
  if(!expansion)continue; // Never label unknown dungeon zones as raids.
  records.push({id,label:entry.name||id,expansion,bossParses:entry.bossParses});
 }
 if(!records.some(x=>x.id===currentId)&&Array.isArray(wcl?.bossParses)&&wcl.bossParses.length){
  records.push({id:currentId,label:wcl?.currentSeasonName||'Current season',expansion:data?.raidProgressionByExpansion?.currentSeason?.expansion||'Current expansion',bossParses:wcl.bossParses});
 }
 records.sort((a,b)=>a.id===currentId?-1:b.id===currentId?1:b.label.localeCompare(a.label,undefined,{numeric:true}));
 fillGroupedOptions(selector,records,currentId);
 selector.title=records.length<=1?'No additional verified raid logs available yet.':'Select historical raid logs';
 const show=()=>renderWclBosses(records.find(x=>x.id===selector.value)?.bossParses||[]);
 selector.onchange=show;show();
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
  const icon=typeof boss.iconUrl==='string'&&/^https:\/\//i.test(boss.iconUrl)?boss.iconUrl:null;
  const placeholder=document.createElement('span');placeholder.className='boss-icon-placeholder';placeholder.textContent='✦';placeholder.setAttribute('aria-hidden','true');
  if(icon){const img=document.createElement('img');img.src=icon;img.alt='';img.loading='lazy';img.className='boss-icon';img.onerror=()=>img.replaceWith(placeholder);name.append(img);}else{name.append(placeholder);}
  name.classList.add('boss-name-cell');link.textContent=boss.name||'Unknown boss';name.append(link);
  const pct=document.createElement('td');pct.className='wcl-value';
  let score=Number.isFinite(Number(boss.bestPercent))&&boss.bestPercent!==null&&boss.bestPercent!==undefined?Number(boss.bestPercent):null;
  if(score===null){const match=String(boss.note||'').match(/Rank percentile:\s*([\d.]+)/i);if(match)score=Number(match[1]);}
  pct.textContent=score===null||!Number.isFinite(score)?'—':String(Math.trunc(Math.max(0,Math.min(100,score))));
  if(score!==null){pct.classList.add(score>=95?'parse-legendary':score>=75?'parse-epic':score>=50?'parse-rare':score>=25?'parse-uncommon':'parse-common');}
  const hps=document.createElement('td');hps.className='wcl-value wcl-hps';
  const n=boss.highestHps == null ? NaN : Number(boss.highestHps);hps.textContent=Number.isFinite(n)&&n>0?Math.round(n).toLocaleString('en-US'):'—';
  tr.append(name,pct,hps);tbody.append(tr);
 }
}

// Raider.IO Mythic+ dashboard. Never fabricate run times or dungeon icons.
function rioScoreClass(value){
 if(typeof value!=='number'||!Number.isFinite(value))return 'rio-unranked';
 // Visual tiers only: not a claim about official Raider.IO thresholds.
 return value>=3500?'rio-gold':value>=2500?'rio-purple':value>=1500?'rio-blue':'rio-green';
}
function rioDuration(run){
 const ms=run.clearTimeMs;
 if(typeof ms==='number'&&Number.isFinite(ms)&&ms>=0){
  const seconds=Math.floor(ms/1000);
  const m=Math.floor(seconds/60),s=seconds%60;
  return `${m}:${String(s).padStart(2,'0')}`;
 }
 return '—';
}
// Match WCL historical dungeon zones to Raider.IO dungeon names, never by run time.
// An archived WCL zone is NOT evidence that its parse came from the displayed RIO run.
function dungeonKey(name){
 return String(name||'').toLowerCase().replace(/[’‘`]/g,"'")
  .replace(/\s*\+\d+\s*$/,'').replace(/[^a-z0-9]+/g,' ').trim();
}
function wclDungeonIndex(wcl,rio){
 const runs=Array.isArray(rio?.bestRuns)?rio.bestRuns:[];
 const valid=new Set(runs.map(r=>dungeonKey(r.name)).filter(Boolean));
 const index=new Map();
 const archives=wcl?.seasonArchive&&typeof wcl.seasonArchive==='object'?wcl.seasonArchive:{};
 for(const [id,zone] of Object.entries(archives)){
  if(!id.startsWith('wcl-zone-')||!zone||!Array.isArray(zone.bossParses))continue;
  const key=dungeonKey(zone.name);
  if(!valid.has(key))continue;
  const rows=zone.bossParses.filter(row=>row&&typeof row==='object');
  const percents=rows.map(row=>Number(row.bestPercent)).filter((v,i)=>rows[i].bestPercent!=null&&Number.isFinite(v)&&v>=0&&v<=100);
  const amounts=rows.map(row=>Number(row.highestHps)).filter(v=>Number.isFinite(v)&&v>0);
  if(!percents.length&&!amounts.length)continue;
  const prev=index.get(key);
  const best=percents.length?Math.max(...percents):null;
  const hps=amounts.length?Math.max(...amounts):null;
  index.set(key,{
   bestPercent:best==null?prev?.bestPercent??null:Math.max(best,prev?.bestPercent??0),
   highestHps:hps==null?prev?.highestHps??null:Math.max(hps,prev?.highestHps??0),
   url:typeof zone.url==='string'&&/^https:\/\//i.test(zone.url)?zone.url:(rows.find(r=>typeof r.url==='string'&&/^https:\/\//i.test(r.url))?.url||wcl?.profileUrl||null)
  });
 }
 return index;
}
function appendDungeonHealing(card,performance){
 if(!performance)return;
 const box=document.createElement('div');box.className='rio-wcl-metrics';
 const label=document.createElement('p');label.className='rio-wcl-caption';label.textContent='WARCRAFT LOGS · DUNGEON HEALING (SEPARATE RUNS)';box.append(label);
 const stats=document.createElement('div');stats.className='rio-wcl-stats';
 if(performance.bestPercent!=null){
  const row=document.createElement('span');row.textContent='Best parse: ';
  const strong=document.createElement('strong');strong.textContent=String(Math.trunc(performance.bestPercent));
  strong.className=performance.bestPercent>=95?'parse-legendary':performance.bestPercent>=75?'parse-epic':performance.bestPercent>=50?'parse-rare':performance.bestPercent>=25?'parse-uncommon':'parse-common';
  row.append(strong);stats.append(row);
 }
 if(performance.highestHps!=null){
  const row=document.createElement('span');row.textContent='Highest HPS: ';
  const strong=document.createElement('strong');strong.textContent=Math.round(performance.highestHps).toLocaleString('en-US');
  row.append(strong);stats.append(row);
 }
 box.append(stats);
 if(performance.url&&/^https:\/\//i.test(performance.url)){
  const link=document.createElement('a');link.href=performance.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='WCL SOURCE ↗';box.append(link);
 }
 card.append(box);
}
function renderMplusHistorySelector(rio){
 const selector=el('rio-season-select');if(!selector)return;
 // Current bestRuns are the only season-specific M+ runs in the existing JSON.
 // Never show previous seasons with current-season runs or scores.
 const id=String(rio.currentSeason||'current');
 const label=rio.currentSeasonName||id;
 const expansion=expansionFromSeason(label)||'Current expansion';
 fillGroupedOptions(selector,[{id,label:label.replace(/^.*?Season/i,'Season'),expansion}],id);
 selector.title='Historical Mythic+ runs require season-specific data from Raider.IO.';
}
function renderRaiderIo(rio,wcl){
 renderMplusHistorySelector(rio);
 if(!rio)return;
 setValue('rio-score',rio.currentSeasonScore??rio.mythicPlusScore);
 setValue('rio-previous',rio.previousSeasonScore);
 if(el('rio-current-season'))el('rio-current-season').textContent=rio.currentSeasonName||rio.currentSeason||'';
 if(el('rio-previous-season'))el('rio-previous-season').textContent=rio.previousSeasonName||rio.previousSeason||'';
 for(const [id,value] of [['rio-score',rio.currentSeasonScore??rio.mythicPlusScore],['rio-previous',rio.previousSeasonScore]]){
  const node=el(id);if(node)node.classList.add(rioScoreClass(value));
 }
 const parent=el('rio-runs');if(!parent)return;parent.replaceChildren();
 const dungeonHealing=wclDungeonIndex(wcl,rio);
 const runs=Array.isArray(rio.bestRuns)?rio.bestRuns:[];
 if(!runs.length){const p=document.createElement('p');p.className='empty-state';p.textContent='No current-season runs available.';parent.append(p);return;}
 for(const run of runs){
  const card=document.createElement('article');card.className='rio-run-card';
  const header=document.createElement('div');header.className='rio-run-heading';
  const imgUrl=typeof run.iconUrl==='string'&&/^https:\/\//i.test(run.iconUrl)?run.iconUrl:null;
  const fallback=document.createElement('span');fallback.className='rio-run-icon-fallback';fallback.textContent='✦';fallback.setAttribute('aria-hidden','true');
  if(imgUrl){const img=document.createElement('img');img.src=imgUrl;img.alt='';img.loading='lazy';img.className='rio-run-icon';img.onerror=()=>img.replaceWith(fallback);header.append(img);}
  else header.append(fallback);
  const title=document.createElement('h4');title.textContent=run.name||'Dungeon';header.append(title);card.append(header);
  const info=document.createElement('div');info.className='rio-run-meta';
  const score=document.createElement('span');score.textContent='Score: '+(typeof run.score==='number'?run.score.toLocaleString('en-US',{maximumFractionDigits:1}):'—');score.className=rioScoreClass(run.score);
  const time=document.createElement('span');time.textContent='Time: '+rioDuration(run);
  info.append(score,time);card.append(info);
  appendDungeonHealing(card,dungeonHealing.get(dungeonKey(run.name)));
  if(typeof run.url==='string'&&/^https:\/\//i.test(run.url)){const a=document.createElement('a');a.href=run.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='VIEW DETAILS ↗';card.append(a);}
  parent.append(card);
 }
}

// V5.2 character banner. Never infer an active specialization from class alone.
function renderCharacter(character,achievementPoints){
 if(!character||typeof character!=='object')return;
 if(character.name)setValue('character-name',String(character.name).toUpperCase());
 if(character.race)setValue('character-race',character.race);
 const spec=typeof character.specialization==='string'&&character.specialization.trim()?character.specialization.trim():null;
 const cls=typeof character.class==='string'?character.class:'Shaman';
 setValue('character-spec',spec?`${spec} ${cls}`:cls);
 const ilvl=Number(character.itemLevel);
 if(character.itemLevel!=null&&Number.isFinite(ilvl)&&ilvl>0)setValue('character-ilvl',Math.trunc(ilvl));
 const lifetime=character.lifetimeStatistics||{};
 const lifetimeValues=[['lifetime-raid-deaths',lifetime.raidDeaths],['lifetime-deaths',lifetime.totalDeaths],['lifetime-falling-deaths',lifetime.fallingDeaths],['lifetime-achievement-points',achievementPoints]];
 for(const [id,value] of lifetimeValues){const node=el(id);if(node&&value!=null&&Number.isFinite(Number(value))&&Number(value)>=0)node.textContent=Number(value).toLocaleString('en-US',{maximumFractionDigits:0});}
 const portrait=el('character-portrait');
 if(portrait&&typeof character.portraitUrl==='string'&&/^https:\/\//i.test(character.portraitUrl)){
  portrait.onerror=()=>{portrait.onerror=null;portrait.src='avatar.png';};
  portrait.src=character.portraitUrl;
 }
}
