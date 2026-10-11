import {el} from './utils.js';
function renderGuild(guild){const wrapper=el('guild-header'),link=el('guild-link');if(!wrapper||!link)return;const name=typeof guild?.name==='string'?guild.name.trim():'';const url=guild?.url;if(!name||typeof url!=='string'||!/^https:\/\//i.test(url)){wrapper.hidden=true;return;}link.textContent=name+' ↗';link.href=url;wrapper.hidden=false;}

export {renderGuild};
