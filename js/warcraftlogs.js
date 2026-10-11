import {el} from './utils.js';
import {normalizeRaidName} from './raids.js';
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
 const liveS1=archive['season-mn-1']?.bossParses?.length?archive['season-mn-1'].bossParses:archive['wcl-zone-46']?.bossParses;
 const seasonOneRows=Array.isArray(liveS1)&&liveS1.length?liveS1:MIDNIGHT_S1_BOSSES;
 const existingS1=records.find(r=>r.id==='season-mn-1');
 if(existingS1){existingS1.label='Midnight Season 1';existingS1.expansion='Midnight';existingS1.bossParses=seasonOneRows;}
 else records.push({id:'season-mn-1',label:'Midnight Season 1',expansion:'Midnight',bossParses:seasonOneRows});
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


export {renderWclHistory,EXPANSION_ORDER,expansionFromSeason,fillGroupedOptions};
