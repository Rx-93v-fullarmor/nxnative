'use strict';
let token = location.hash.slice(1), inputs = [], env = null, logTask = null, logOffset = 0;
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, options = {}) {
  const response = await fetch('/api/' + path, {...options, headers: {'X-Session-Token': token, ...(options.body instanceof Blob ? {} : {'Content-Type':'application/json'}), ...options.headers}});
  const value = await response.json();
  if (!response.ok) throw new Error(value.detail || 'Request failed');
  return value;
}
function message(text) { $('message').textContent = t(text); $('message').style.display = 'block'; }
function action(fn) { return async (...args) => { try { await fn(...args); } catch (error) { message(error.message); } }; }
function renderInputs() {
  $('inputs').innerHTML = inputs.map(x => `<li><span>${esc(x.name)}</span><button data-remove="${x.id}" aria-label="${esc(t('Remove '))}${esc(x.name)}">×</button></li>`).join('');
}
async function upload(files) {
  $('start').disabled = true;
  try {
    for (const file of files) {
      const key = 'nx-upload:' + [file.name, file.size, file.lastModified].join(':');
      let state;
      const saved = localStorage.getItem(key);
      if (saved) { try { state = await api('uploads/' + saved); } catch (_) {} }
      if (!state) state = await api('uploads', {method:'POST', body:JSON.stringify({name:file.name,size:file.size})});
      localStorage.setItem(key, state.id);
      $('upload-progress').hidden = false;
      while (state.offset < file.size) {
        const chunk = file.slice(state.offset, state.offset + 4 * 1024 * 1024);
        let result;
        for (let attempt = 0; attempt < 3; attempt++) {
          try { result = await api(`uploads/${state.id}?offset=${state.offset}`, {method:'PUT',body:chunk}); break; }
          catch (error) {
            const current = await api('uploads/' + state.id);
            if (current.offset > state.offset) { result = current; break; }
            if (attempt === 2) throw error;
          }
        }
        state.offset = result.offset;
        $('upload-progress').value = 100 * state.offset / file.size;
      }
      localStorage.removeItem(key);
      if (!inputs.some(x => x.id === state.id)) inputs.push({id:state.id,name:file.name});
      renderInputs();
    }
  } finally { $('start').disabled = false; $('upload-progress').hidden = true; }
}
function capability() {
  const profile = env?.profiles.find(p => p.id === $('game').value);
  $('build-options').hidden = $('kind').value !== 'build';
  $('mac').disabled = env?.system !== 'Darwin';
  if ($('mac').disabled) $('mac').checked = false;
  $('capability').textContent = t(profile?.reason || (profile?.graphics === 'vulkan' ? 'Vulkan game: MetalFX spatial upscaling is unavailable.' : 'Exact registered game versions are required for application builds.'));
  $('spatial').disabled = profile?.graphics === 'vulkan';
  if ($('spatial').disabled) $('spatial').value = '0';
}
async function loadEnvironment() {
  env = await api('environment');
  $('host').textContent = `${env.system} / ${env.machine} · ${env.checks.filter(x => !x.available).length} ${t('missing dependencies')}`;
  const selected = $('game').value;
  $('game').innerHTML = '<option value="">Detect from input</option>' + env.profiles.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
  $('game').value = selected;
  $('checks').innerHTML = env.checks.map(c => `<div class="check ${c.available?'':'missing'}" title="${esc(c.path)}">${c.available?'✓':'!'} ${esc(c.name)}</div>`).join('');
  $('tools-path').value = env.config.tools || ''; $('sdk-path').value = env.config.sdk || ''; $('metal-path').value = env.config.metal || '';
  $('data-folder').textContent = t('Data folder: ') + env.data_directory;
  capability(); translateStatic();
}
async function refresh() {
  const tasks = await api('tasks');
  $('tasks').innerHTML = tasks.length ? tasks.map(task => {
    const finished = ['succeeded','failed','cancelled','interrupted'].includes(task.status);
    return `<article class="task"><div><div class="task-title"><span class="badge">${esc(t(task.status))}</span>${esc(t(task.kind))} · ${esc(task.game || t('Auto detect'))} <small>${new Date(task.created*1000).toLocaleString(uiLanguage)}</small></div><div class="task-stage">${esc(t(task.message || task.stage))}</div></div><div class="actions"><button data-log="${task.id}">Log</button>${finished?`<button data-retry="${task.id}">Retry</button><button data-delete="${task.id}">Delete</button>`:`<button data-cancel="${task.id}">Cancel</button>`}</div><div class="downloads">${task.artifacts.map(name => `<a href="/api/tasks/${task.id}/artifacts/${name.split('/').map(encodeURIComponent).join('/')}">${esc(name)}</a>`).join('')}</div></article>`;
  }).join('') : '<p class="empty">No tasks yetask. Your next build starts above.</p>';
  translateStatic($('tasks'));
  if (logTask && $('logs').open) {
    const result = await api(`tasks/${logTask}/log?offset=${logOffset}`); logOffset = result.offset;
    $('log-text').textContent = ($('log-text').textContent + result.text).slice(-300000);
  }
}
$('files').onchange = action(e => upload(e.target.files));
$('drop').ondragover = e => e.preventDefault();
$('drop').ondrop = action(e => { e.preventDefault(); return upload(e.dataTransfer.files); });
$('import').onclick = action(async () => { const result = await api('import',{method:'POST',body:JSON.stringify({path:$('local-path').value})}); inputs.push(result); renderInputs(); $('local-path').value=''; });
$('inputs').onclick = action(async e => { const id=e.target.dataset.remove; if (!id) return; await api('uploads/'+id,{method:'DELETE'}); inputs=inputs.filter(x=>x.id!==id); renderInputs(); });
$('kind').onchange = $('game').onchange = capability;
$('start').onclick = action(async () => {
  const keys = inputs.filter(x => x.name.toLowerCase().endsWith('.keys'));
  if (keys.length !== 1) throw new Error('Add exactly one prod.keys file.');
  const targets = ['ios','mac'].filter(x => $(x).checked);
  if ($('kind').value === 'build' && !targets.length) throw new Error('Select at least one output platform.');
  const result = await api('tasks',{method:'POST',body:JSON.stringify({kind:$('kind').value,game:$('game').value,
    files:inputs.filter(x=>!x.name.toLowerCase().endsWith('.keys')).map(x=>x.id),keys:keys[0].id,targets:targets.length?targets:['ios'],retain_keys:$('retain').checked,
    settings:{DM_LANG:$('language').value,DM_OPMODE:$('mode').value,DM_METALFX_SPATIAL:$('spatial').value,DM_METALFX_OUTPUT_HEIGHT:$('resolution').value}})});
  message('Task queued: '+result.id.slice(0,8)); await refresh();
});
$('tasks').onclick = action(async e => {
  const d=e.target.dataset;
  if(d.log){logTask=d.log;logOffset=0;$('log-text').textContent='';$('logs').showModal();await refresh();}
  if(d.cancel) await api(`tasks/${d.cancel}/cancel`,{method:'POST'});
  if(d.retry) await api(`tasks/${d.retry}/retry`,{method:'POST'});
  if(d.delete && confirm(t('Delete this task, its copied inputs, cache and outputs? Original imported files remain.'))) await api('tasks/'+d.delete,{method:'DELETE'});
  if(d.cancel||d.retry||d.delete) await refresh();
});
$('settings-button').onclick = () => $('settings').showModal();
$('close-settings').onclick = () => $('settings').close();
$('close-logs').onclick = () => $('logs').close();
$('save-settings').onclick = action(async () => {await api('config',{method:'PUT',body:JSON.stringify({tools:$('tools-path').value,sdk:$('sdk-path').value,metal:$('metal-path').value})});await loadEnvironment();message('Tool paths saved.');});
$('ui-language').value = uiLanguage;
translateStatic();
$('ui-language').onchange = action(async () => {uiLanguage = $('ui-language').value; localStorage.setItem('nx-ui-language', uiLanguage); translateStatic(); renderInputs(); await loadEnvironment(); await refresh();});
action(async () => { await api('session',{method:'POST'}); history.replaceState(null,'','/'); token=''; await loadEnvironment(); await refresh(); setInterval(action(refresh),2500); })();
