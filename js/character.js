import {el,setValue} from './utils.js';
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
export {renderCharacter};
