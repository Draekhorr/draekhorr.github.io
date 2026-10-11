const el=id=>document.getElementById(id);
function setValue(id,value){if(value===null||value===undefined||value==='')return;el(id).textContent=typeof value==='number'?value.toLocaleString('en-US'):String(value)}
function setCards(id,items,fallback){if(!Array.isArray(items)||!items.length)return;const parent=el(id);parent.replaceChildren();for(const item of items){const card=document.createElement('article');card.className='data-card';const title=document.createElement('h4');title.textContent=item.name||'Unnamed';card.append(title);if(item.note){const note=document.createElement('p');note.textContent=item.note;card.append(note)}if(item.url&&/^https:\/\//i.test(item.url)){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='VIEW DETAILS ↗';card.append(link)}parent.append(card)}}
function safeLink(id,url){if(typeof url==='string'&&/^https:\/\//i.test(url))el(id).href=url}
function renderGuild(guild){const wrapper=el('guild-header'),link=el('guild-link');if(!wrapper||!link)return;const name=typeof guild?.name==='string'?guild.name.trim():'';const url=guild?.url;if(!name||typeof url!=='string'||!/^https:\/\//i.test(url)){wrapper.hidden=true;return;}link.textContent=name+' ↗';link.href=url;wrapper.hidden=false;}
fetch('data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}).then(d=>{
 const ce=(d.cuttingEdgeAchievements||[]).filter(x=>x.verified===true);setValue('ce-count',new Set(ce.map(x=>String(x.tierId)).filter(Boolean)).size);collectVerifiedCuttingEdges(ce);renderRaids(d);safeLink('raid-source-link',d.raidSourceUrl);
 renderWclHistory(d.warcraftLogs,d);safeLink('wcl-link',d.warcraftLogs?.profileUrl);
 renderGuild(d.guild);renderCharacter(d.character,d.achievementPoints);renderRaiderIo(d.raiderIo);safeLink('rio-link',d.raiderIo?.profileUrl);
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
// Verified Season 1 raid-healing snapshot supplied from Warcraft Logs zone 46.
// This replaces only the misleading Sporefall entry; all other archived raids remain untouched.
const MIDNIGHT_S1_WCL_URL='https://www.warcraftlogs.com/character/id/82347618?zone=46';
const MIDNIGHT_S1_BOSSES=[
 ['Imperator Averzian',84,139771.5],
 ['Vorasius',74,132722.4],
 ['Fallen-King Salhadaar',62,134585.9],
 ['Vaelgor & Ezzorak',61,141367.0],
 ['Lightblinded Vanguard',88,163906.1],
 ['Crown of the Cosmos',62,155953.6],
 ['Chimaerus, the Undreamt God',86,129923.4],
 ["Belo'ren, Child of Al'ar",null,null],
 ['Midnight Falls',26,158473.9]
].map(([name,bestPercent,highestHps])=>({name,bestPercent,highestHps,url:MIDNIGHT_S1_WCL_URL}));
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
 // Replace the old single-raid Sporefall option with the complete Midnight S1 zone.
 // Preserve all other archive entries and the current season exactly as received.
 const oldSporefall=records.findIndex(r=>r.expansion==='Midnight'&&normalizeRaidName(r.label)==='sporefall');
 if(oldSporefall>=0)records.splice(oldSporefall,1);
 const existingS1=records.find(r=>r.id==='season-mn-1');
 if(existingS1){existingS1.label='Midnight Season 1';existingS1.expansion='Midnight';existingS1.bossParses=MIDNIGHT_S1_BOSSES;}
 else records.push({id:'season-mn-1',label:'Midnight Season 1',expansion:'Midnight',bossParses:MIDNIGHT_S1_BOSSES});
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
function setupMplusHistorySelector(rio){
 const selector=el('rio-season-select');
 const currentId=String(rio.currentSeason||'current');
 const history=rio.seasonHistory&&typeof rio.seasonHistory==='object'?rio.seasonHistory:{};
 const entries=new Map();
 for(const [id,entry] of Object.entries(history)){
  if(!entry||typeof entry!=='object')continue;
  const score=typeof entry.score==='number'&&Number.isFinite(entry.score)?entry.score:null;
  const runs=Array.isArray(entry.bestRuns)?entry.bestRuns:[];
  if(score===null&&!runs.length)continue;
  const label=entry.name||id;
  entries.set(id,{id,label,expansion:entry.expansion||expansionFromSeason(label)||'Other',score,runs});
 }
 // Legacy data: previous season score is verified even before history is created.
 for(const [id,label,score,runs] of [
  [currentId,rio.currentSeasonName||currentId,rio.currentSeasonScore??rio.mythicPlusScore,rio.bestRuns],
  [rio.previousSeason,rio.previousSeasonName||rio.previousSeason,rio.previousSeasonScore,[]]
 ]){
  if(!id||entries.has(id))continue;
  if(typeof score!=='number'&&!Array.isArray(runs))continue;
  entries.set(String(id),{id:String(id),label,expansion:expansionFromSeason(label)||'Other',score:typeof score==='number'?score:null,runs:Array.isArray(runs)?runs:[]});
 }
 const records=[...entries.values()].sort((a,b)=>{
  const x=EXPANSION_ORDER.indexOf(a.expansion),y=EXPANSION_ORDER.indexOf(b.expansion);
  if(x!==y)return (x<0?999:x)-(y<0?999:y);
  return b.id.localeCompare(a.id,undefined,{numeric:true});
 });
 const display=entry=>{
  const scoreNode=el('rio-score');
  if(scoreNode){scoreNode.textContent=typeof entry.score==='number'?entry.score.toLocaleString('en-US',{maximumFractionDigits:1}):'—';scoreNode.classList.remove('rio-gold','rio-purple','rio-blue','rio-green','rio-unranked');scoreNode.classList.add(rioScoreClass(entry.score));}
  const labelNode=el('rio-current-season');if(labelNode)labelNode.textContent=entry.label;
  const titleNode=el('rio-selected-score-label');if(titleNode)titleNode.textContent=entry.id===currentId?'CURRENT MYTHIC+ SCORE':'SELECTED SEASON SCORE';
  renderMplusRunCards(entry.runs);
  safeLink('rio-link',rio.profileUrl?.split('?')[0]+'?season='+encodeURIComponent(entry.id));
 };
 if(selector&&records.length){
  fillGroupedOptions(selector,records,currentId);
  selector.onchange=()=>{const selected=entries.get(selector.value);if(selected)display(selected);};
 }
 const initial=entries.get(currentId)||records[0];
 if(initial)display(initial);
}

function renderRaiderIo(rio){
 if(!rio)return;
 setValue('rio-score',rio.currentSeasonScore??rio.mythicPlusScore);
 setValue('rio-previous',rio.previousSeasonScore);
 if(el('rio-current-season'))el('rio-current-season').textContent=rio.currentSeasonName||rio.currentSeason||'';
 if(el('rio-previous-season'))el('rio-previous-season').textContent=rio.previousSeasonName||rio.previousSeason||'';
 for(const [id,value] of [['rio-score',rio.currentSeasonScore??rio.mythicPlusScore],['rio-previous',rio.previousSeasonScore]]){
  const node=el(id);if(node)node.classList.add(rioScoreClass(value));
 }
  setupMplusHistorySelector(rio);
}

function renderMplusRunCards(runs){
 const parent=el('rio-runs');if(!parent)return;parent.replaceChildren();
 if(!runs.length){const p=document.createElement('p');p.className='empty-state';p.textContent='No verified dungeon runs archived for this season yet.';parent.append(p);return;}
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