import {el,setValue,safeLink} from './utils.js';
import {EXPANSION_ORDER,expansionFromSeason,fillGroupedOptions} from './warcraftlogs.js';
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
  if(!id)continue;
  if(typeof score!=='number'&&(!Array.isArray(runs)||!runs.length))continue;
  const old=entries.get(String(id));
  const verifiedRuns=Array.isArray(runs)?runs:[];
  entries.set(String(id),{id:String(id),label,expansion:expansionFromSeason(label)||old?.expansion||'Other',score:typeof score==='number'?score:old?.score??null,runs:verifiedRuns.length?verifiedRuns:old?.runs||[]});
 }
 const records=[...entries.values()].sort((a,b)=>{
  const x=EXPANSION_ORDER.indexOf(a.expansion),y=EXPANSION_ORDER.indexOf(b.expansion);
  if(x!==y)return (x<0?999:x)-(y<0?999:y);
  return b.id.localeCompare(a.id,undefined,{numeric:true});
 });
 const display=entry=>{
  const match=entry.id.match(/^(season-[a-z]+)-(\d+)$/);
  const previousId=match&&Number(match[2])>1?`${match[1]}-${Number(match[2])-1}`:null;
  const previous=previousId?entries.get(previousId):null;
  const prevNode=el('rio-previous');
  if(prevNode){prevNode.textContent=typeof previous?.score==='number'?previous.score.toLocaleString('en-US',{maximumFractionDigits:1}):'—';prevNode.classList.remove('rio-gold','rio-purple','rio-blue','rio-green','rio-unranked');prevNode.classList.add(rioScoreClass(previous?.score));}
  const prevLabel=el('rio-previous-season');if(prevLabel)prevLabel.textContent=previous?.label||'No verified previous season';
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


export {renderRaiderIo};
