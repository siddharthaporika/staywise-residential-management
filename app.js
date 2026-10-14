const $ = (id) => document.getElementById(id);
let studentsCache = [], complaintsCache = [], roomsCache = [], availableRoomsCache = [];
const titleMap = {
  overview: ["Overview", "A better view of <i>campus living.</i>", "Your residence at a glance. Everything in its right place."],
  students: ["Residents", "People make a <i>residence.</i>", "A clear directory of the people who call this place home."],
  rooms: ["Rooms", "Space for everyone to <i>settle in.</i>", "Understand capacity and availability without the spreadsheet shuffle."],
  complaints: ["Maintenance", "Small fixes, <i>better days.</i>", "Every request tracked, every follow-up a little easier."]
};
function toast(message){$('toast').textContent=message;$('toast').classList.remove('hidden');setTimeout(()=>$('toast').classList.add('hidden'),2600)}
async function api(url, options={}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json'},...options});
  const data = await response.json();
  if(!response.ok) throw new Error(data.error || 'Something went wrong');
  return data;
}
function statusClass(s){return s==='Resolved'?'status-resolved':s==='In progress'?'status-progress':'status-open'}
function priorityClass(p){return p==='High'?'priority-high':p==='Low'?'priority-low':'priority-medium'}
function showView(view){
  document.querySelectorAll('.view').forEach(el=>el.classList.add('hidden'));
  $('view-'+view).classList.remove('hidden');
  document.querySelectorAll('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.view===view));
  $('crumb-title').textContent=titleMap[view][0];$('page-title').innerHTML=titleMap[view][1];$('page-subtitle').textContent=titleMap[view][2];
  $('new-complaint').classList.toggle('hidden',!['overview','complaints'].includes(view));
  $('new-resident').classList.toggle('hidden',view!=='students');
  $('allocate-room-top').classList.toggle('hidden',!['students','rooms'].includes(view));
  if(view==='students') renderStudents();if(view==='rooms') renderRooms();if(view==='complaints') renderComplaints();
}
function renderCategoryChart(items){
  const root=$('category-chart');
  if(!items.length){root.innerHTML='<div class="empty">No requests yet. You are off to a good start.</div>';return}
  const max=Math.max(...items.map(x=>x.total),1);
  root.innerHTML=items.map(x=>`<div class="bar-row"><label>${escapeHtml(x.category)}</label><div class="bar-track"><div class="bar-fill" style="width:${x.total/max*100}%"></div></div><strong>${x.total}</strong></div>`).join('');
}
function escapeHtml(value=''){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function requestCell(c){return `<span class="request-name">#${c.id} · ${escapeHtml(c.category)}</span><span class="request-sub">${escapeHtml(c.description)}</span>`}
function renderRecent(items){
  $('recent-table').innerHTML=items.length?items.map(c=>`<tr><td>${requestCell(c)}</td><td>${escapeHtml(c.student)}</td><td>${escapeHtml(c.room_no)}</td><td><span class="priority ${priorityClass(c.priority)}">${escapeHtml(c.priority)}</span></td><td><span class="status ${statusClass(c.status)}">${escapeHtml(c.status)}</span></td></tr>`).join(''):'<tr><td colspan="5" class="empty">No maintenance requests recorded.</td></tr>';
}
async function loadDashboard(){
  try{
    const d=await api('/api/dashboard');
    $('m-students').textContent=d.students;$('m-occupancy').textContent=d.occupancy;$('m-vacant').textContent=d.vacant;$('m-open').textContent=d.open_complaints;
    $('m-occupied').textContent=d.occupied;$('m-rooms').textContent=d.rooms;$('occupancy-bar').style.width=d.occupancy+'%';
    $('donut-value').textContent=d.occupancy+'%';$('donut').style.background=`conic-gradient(#7562e9 ${d.occupancy*3.6}deg,#f0eff7 0deg)`;
    $('legend-occupied').textContent=d.occupied;$('legend-vacant').textContent=d.vacant;
    $('nav-students').textContent=d.students;$('nav-complaints').textContent=d.open_complaints;
    renderCategoryChart(d.by_category);renderRecent(d.recent);
  }catch(e){toast('Could not load dashboard. Is the Flask server running?')}
}
function renderStudents(){
  const q=($('student-search').value||'').toLowerCase();
  const data=studentsCache.filter(s=>[s.name,s.roll_no,s.department,s.hostel,s.room_no].join(' ').toLowerCase().includes(q));
  $('students-table').innerHTML=data.map(s=>`<tr><td><span class="request-name">${escapeHtml(s.name)}</span><span class="request-sub">${escapeHtml(s.email||'No email added')}</span></td><td>${escapeHtml(s.roll_no)}</td><td>${escapeHtml(s.department)}</td><td>Year ${s.year}</td><td>${escapeHtml(s.hostel||'Not allocated')} ${s.room_no?`/ ${escapeHtml(s.room_no)}`:''}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">No residents match your search.</td></tr>';
}
function renderRooms(){
  $('room-grid').innerHTML=roomsCache.map(r=>`<article class="room-card"><div class="room-card-head"><div><div class="room-number">${escapeHtml(r.room_no)}</div><div class="room-hostel">${escapeHtml(r.hostel)}</div></div><div class="room-icon">▦</div></div><div class="room-beds">${Array.from({length:r.capacity},(_,i)=>`<span class="bed ${i<r.occupied?'used':''}"></span>`).join('')}</div><div class="room-foot"><span>${r.occupied} of ${r.capacity} beds occupied</span><b class="${r.vacant?'room-open':'room-full'}">${r.vacant} available</b></div></article>`).join('')||'<div class="empty">No rooms have been added yet.</div>';
}
function renderComplaints(){
  const filter=$('status-filter').value;
  const data=complaintsCache.filter(c=>filter==='All'||c.status===filter);
  $('complaints-table').innerHTML=data.map(c=>`<tr><td>${requestCell(c)}</td><td>${escapeHtml(c.student)}<span class="request-sub">Room ${escapeHtml(c.room_no)}</span></td><td><span class="priority ${priorityClass(c.priority)}">${escapeHtml(c.priority)}</span></td><td><span class="status ${statusClass(c.status)}">${escapeHtml(c.status)}</span></td><td><select class="search status-select" data-id="${c.id}"><option ${c.status==='Open'?'selected':''}>Open</option><option ${c.status==='In progress'?'selected':''}>In progress</option><option ${c.status==='Resolved'?'selected':''}>Resolved</option></select></td></tr>`).join('')||'<tr><td colspan="5" class="empty">Nothing to show for this status.</td></tr>';
}
async function loadData(){
  try{
    [studentsCache,roomsCache,complaintsCache,availableRoomsCache]=await Promise.all([api('/api/students'),api('/api/rooms'),api('/api/complaints'),api('/api/rooms/available')]);
    $('resident-select').innerHTML='<option value="">Not specified</option>'+studentsCache.map(s=>`<option value="${escapeHtml(s.roll_no)}">${escapeHtml(s.name)} · ${escapeHtml(s.roll_no)}</option>`).join('');
    const unallocated=studentsCache.filter(s=>!s.hostel);
    $('allocation-student').innerHTML='<option value="">Choose an unallocated resident</option>'+unallocated.map(s=>`<option value="${escapeHtml(s.roll_no)}">${escapeHtml(s.name)} · ${escapeHtml(s.roll_no)}</option>`).join('');
    $('allocation-room').innerHTML='<option value="">Choose a room</option>'+availableRoomsCache.map(r=>`<option value="${r.id}">${escapeHtml(r.hostel)} · Room ${escapeHtml(r.room_no)} (${r.vacant} bed${r.vacant===1?'':'s'} available)</option>`).join('');
    renderStudents();renderRooms();renderComplaints();
  }catch(e){toast(e.message)}
}
function openModal(){$('modal').classList.remove('hidden');$('form-message').textContent=''}
function closeModal(){$('modal').classList.add('hidden');$('complaint-form').reset()}
$('new-complaint').addEventListener('click',openModal);
$('close-modal').addEventListener('click',closeModal);$('cancel-modal').addEventListener('click',closeModal);
$('modal').addEventListener('click',e=>{if(e.target===$('modal'))closeModal()});
$('refresh').addEventListener('click',async()=>{await Promise.all([loadDashboard(),loadData()]);toast('Dashboard refreshed')});
document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
document.querySelectorAll('[data-goto]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.goto)));
$('student-search').addEventListener('input',renderStudents);$('status-filter').addEventListener('change',renderComplaints);
$('complaints-table').addEventListener('change',async e=>{
  if(!e.target.matches('.status-select'))return;
  try{await api(`/api/complaints/${e.target.dataset.id}`,{method:'PATCH',body:JSON.stringify({status:e.target.value})});await Promise.all([loadDashboard(),loadData()]);toast('Request status updated')}
  catch(err){toast(err.message)}
});
function openResidentModal(){$('resident-modal').classList.remove('hidden');$('resident-message').textContent='';$('resident-message').classList.remove('success')}
function closeResidentModal(){$('resident-modal').classList.add('hidden');$('resident-form').reset()}
function openAllocationModal(){$('allocation-modal').classList.remove('hidden');$('allocation-message').textContent='';$('allocation-message').classList.remove('success')}
function closeAllocationModal(){$('allocation-modal').classList.add('hidden');$('allocation-form').reset()}
$('new-resident').addEventListener('click',openResidentModal);
$('close-resident-modal').addEventListener('click',closeResidentModal);$('cancel-resident-modal').addEventListener('click',closeResidentModal);
$('resident-modal').addEventListener('click',e=>{if(e.target===$('resident-modal'))closeResidentModal()});
$('allocate-room-top').addEventListener('click',openAllocationModal);
$('close-allocation-modal').addEventListener('click',closeAllocationModal);$('cancel-allocation-modal').addEventListener('click',closeAllocationModal);
$('allocation-modal').addEventListener('click',e=>{if(e.target===$('allocation-modal'))closeAllocationModal()});
$('resident-form').addEventListener('submit',async e=>{
  e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());
  try{
    await api('/api/students',{method:'POST',body:JSON.stringify(data)});
    $('resident-message').textContent='Resident registered successfully.';$('resident-message').classList.add('success');
    await Promise.all([loadDashboard(),loadData()]);
    setTimeout(()=>{closeResidentModal();showView('students');toast('Resident registered')},500);
  }catch(err){$('resident-message').textContent=err.message;$('resident-message').classList.remove('success')}
});
$('allocation-form').addEventListener('submit',async e=>{
  e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());
  try{
    const result=await api('/api/allotments',{method:'POST',body:JSON.stringify(data)});
    $('allocation-message').textContent=result.message;$('allocation-message').classList.add('success');
    await Promise.all([loadDashboard(),loadData()]);
    setTimeout(()=>{closeAllocationModal();showView('rooms');toast('Room allocated successfully')},500);
  }catch(err){$('allocation-message').textContent=err.message;$('allocation-message').classList.remove('success')}
});
$('complaint-form').addEventListener('submit',async e=>{
  e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());
  try{await api('/api/complaints',{method:'POST',body:JSON.stringify(data)});closeModal();await Promise.all([loadDashboard(),loadData()]);showView('complaints');toast('Maintenance request added')}
  catch(err){$('form-message').textContent=err.message}
});
loadDashboard();loadData();
