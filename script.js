const el=id=>document.getElementById(id);
function setValue(id,value){if(value===null||value===undefined||value==='')return;el(id).textContent=typeof value==='number'?value.toLocaleString('en-US'):String(value)}
function setCards(id,items,fallback){if(!Array.isArray(items)||!items.length)return;const parent=el(id);parent.replaceChildren();for(const item of items){const card=document.createElement('article');card.className='data-card';const title=document.createElement('h4');title.textContent=item.name||'Unnamed';card.append(title);if(item.note){const note=document.createElement('p');note.textContent=item.note;card.append(note)}if(item.url&&/^https:\/\//i.test(item.url)){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='VIEW DETAILS ↗';card.append(link)}parent.append(card)}}
function safeLink(id,url){if(typeof url==='string'&&/^https:\/\//i.test(url))el(id).href=url}
fetch('data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}).then(d=>{
 setValue('mounts-count',d.accountWideMountCount??d.mountCount);setValue('points',d.achievementPoints);
 const mounts=d.mounts||[];if(mounts.length)setValue('rare-count',mounts.filter(x=>x.rare).length);setCards('mount-list',mounts);setCards('achievement-list',d.achievements);if(d.achievements?.length)setValue('achievement-count',d.achievements.length);
 const ce=(d.cuttingEdgeAchievements||[]).filter(x=>x.verified===true);if(ce.length){setValue('ce-count',ce.length);const tiers=ce.map(x=>x.tierId).filter(Boolean);if(tiers.length)setValue('ce-tier-count',new Set(tiers).size)}setCards('ce-list',ce);setCards('raid-list',d.raidProgression);
 setValue('rio-score',d.raiderIo?.mythicPlusScore);setValue('rio-previous',d.raiderIo?.previousSeasonScore);setValue('rio-rank',d.raiderIo?.ranking);setCards('rio-runs',d.raiderIo?.bestRuns);safeLink('rio-link',d.raiderIo?.profileUrl);safeLink('wowprogress-link',d.wowprogress?.profileUrl);
 if(d.updatedAt)el('status').textContent='Data updated: '+d.updatedAt;
}).catch(()=>{el('status').textContent='Data unavailable. Use GitHub Pages or a local web server.'});
