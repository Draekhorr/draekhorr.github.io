import {el} from './utils.js';
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


export {collectVerifiedCuttingEdges,renderRaids,normalizeRaidName};
