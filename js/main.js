import {el,setValue,safeLink} from './utils.js';
import {renderGuild} from './header.js';
import {renderCharacter} from './character.js';
import {collectVerifiedCuttingEdges,renderRaids} from './raids.js';
import {renderWclHistory} from './warcraftlogs.js';
import {renderRaiderIo} from './mythicplus.js';

async function loadComponents(){
 const names=['header','hero','character','raids','mythicplus','outro','footer'];
 await Promise.all(names.map(async name=>{
  const slot=document.querySelector(`[data-component="${name}"]`);
  if(!slot)throw Error(`Missing component mount: ${name}`);
  const response=await fetch(`components/${name}.html`,{cache:'no-store'});
  if(!response.ok)throw Error(`Unable to load ${name}: ${response.status}`);
  // Components are maintained as project-owned HTML, never untrusted API data.
  slot.outerHTML=await response.text();
 }));
}
async function start(){
 try{
  await loadComponents();
  const response=await fetch('data.json',{cache:'no-store'});
  if(!response.ok)throw Error(`Data unavailable: ${response.status}`);
  const d=await response.json();
  const ce=(d.cuttingEdgeAchievements||[]).filter(x=>x.verified===true);
  setValue('ce-count',new Set(ce.map(x=>String(x.tierId)).filter(Boolean)).size);
  collectVerifiedCuttingEdges(ce);renderRaids(d);safeLink('raid-source-link',d.raidSourceUrl);
  renderWclHistory(d.warcraftLogs,d);safeLink('wcl-link',d.warcraftLogs?.profileUrl);
  renderGuild(d.guild);renderCharacter(d.character,d.achievementPoints);
  renderRaiderIo(d.raiderIo);safeLink('rio-link',d.raiderIo?.profileUrl);
  if(d.updatedAt)el('status').textContent='Data updated: '+d.updatedAt;
 }catch(error){console.error('Draekhorr bootstrap:',error);const status=el('status');if(status)status.textContent='Site data unavailable. Check the console or GitHub Pages deployment.';}
}
start();
