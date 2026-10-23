const I18N = {
en: {
  c_sos:"I need help now", g_chasing:"A dog is chasing me", g_bitten:"I've been bitten", g_nearby:"Dog nearby, not approaching", g_safe:"I'm safe now",
  f_what:"What happened?", cat_sighting:"Stray dog sighting", cat_pack:"Pack of stray dogs", cat_aggressive:"Aggressive dog",
  cat_chasing:"Chased by a dog", cat_attack:"Someone was attacked", cat_injured:"Injured stray",
  f_animal:"Animal", an_dog:"Stray dog", an_wildlife:"Dangerous wildlife", f_photo:"Photo (from a safe distance)",
  f_left:"The dog is not in my photo (I ran away)", f_note:"Note (optional)", ph_note:"Brown dog near the bus stop", f_send:"Send report",
  c_hint:"Tap the map to set your location if GPS is off. Red = verified, amber = unverified, grey = low confidence.",
  r_sent:"Report sent to {n}.", r_status:"Status", r_conf:"confidence",
  r_wait:"Nearby people are alerted once others confirm it or the authority acknowledges it.",
  st_verified:"verified", st_unverified:"unverified", st_low:"low", st_acknowledged:"acknowledged", st_resolved:"resolved",
  still:"Still here", ago:"{n} min ago", alert:"Verified report within {n} m of you. Stay alert.",
  why_dogs:"{n} dog(s) detected in photo", why_left:"no dog in photo, but user says it left the frame", why_nodog:"no dog detected in photo",
  why_nophoto:"no photo supplied", why_fresh:"photo taken just before the report", why_confirms:"{n} confirmation(s) from nearby users",
  a_title:"Authority dashboard", a_demo:"Load demo data", a_all:"All agencies", k_active:"Active reports", k_verified:"Verified",
  k_unverified:"Awaiting verification", k_resolved:"Resolved", a_hot:"Hotspots", a_cat:"Reports by type", a_trend:"Reports, last 12 hours",
  a_queue:"Action queue", th_photo:"Photo", th_report:"Report", th_conf:"AI confidence", th_age:"Age", th_status:"Status", th_action:"Action",
  call:"Call", nav:"Navigate", upd:"Update…", ack:"Acknowledge", empty:"No active reports.", hot_n:"{n} report(s)", dogs_n:"{n} dog(s)",
  a_live:"Live, refreshes every 3 s", a_nohot:"No hotspots yet. Load demo data to try it."
},
ms: {
  c_sos:"Saya perlukan bantuan sekarang", g_chasing:"Anjing sedang mengejar saya", g_bitten:"Saya telah digigit", g_nearby:"Anjing berdekatan, tidak menghampiri", g_safe:"Saya sudah selamat",
  f_what:"Apa yang berlaku?", cat_sighting:"Anjing liar kelihatan", cat_pack:"Kumpulan anjing liar", cat_aggressive:"Anjing agresif",
  cat_chasing:"Dikejar anjing", cat_attack:"Seseorang diserang", cat_injured:"Anjing liar cedera",
  f_animal:"Haiwan", an_dog:"Anjing liar", an_wildlife:"Hidupan liar berbahaya", f_photo:"Gambar (dari jarak selamat)",
  f_left:"Anjing tiada dalam gambar (saya lari)", f_note:"Nota (pilihan)", ph_note:"Anjing coklat berhampiran perhentian bas", f_send:"Hantar laporan",
  c_hint:"Ketik peta untuk tetapkan lokasi jika GPS dimatikan. Merah = disahkan, jingga = belum disahkan, kelabu = keyakinan rendah.",
  r_sent:"Laporan dihantar kepada {n}.", r_status:"Status", r_conf:"keyakinan",
  r_wait:"Orang sekitar akan dimaklumkan apabila pengguna lain mengesahkannya atau pihak berkuasa mengakuinya.",
  st_verified:"disahkan", st_unverified:"belum disahkan", st_low:"rendah", st_acknowledged:"diakui", st_resolved:"selesai",
  still:"Masih di sini", ago:"{n} min lalu", alert:"Laporan disahkan dalam lingkungan {n} m daripada anda. Berwaspada.",
  why_dogs:"{n} anjing dikesan dalam gambar", why_left:"tiada anjing dalam gambar, tetapi pengguna kata ia sudah keluar bingkai",
  why_nodog:"tiada anjing dikesan dalam gambar", why_nophoto:"tiada gambar", why_fresh:"gambar diambil sebelum laporan dibuat",
  why_confirms:"{n} pengesahan daripada pengguna berdekatan",
  a_title:"Papan pemuka pihak berkuasa", a_demo:"Muat data demo", a_all:"Semua agensi", k_active:"Laporan aktif", k_verified:"Disahkan",
  k_unverified:"Menunggu pengesahan", k_resolved:"Selesai", a_hot:"Kawasan panas", a_cat:"Laporan mengikut jenis", a_trend:"Laporan, 12 jam lepas",
  a_queue:"Giliran tindakan", th_photo:"Gambar", th_report:"Laporan", th_conf:"Keyakinan AI", th_age:"Masa", th_status:"Status", th_action:"Tindakan",
  call:"Telefon", nav:"Navigasi", upd:"Kemas kini…", ack:"Akui", empty:"Tiada laporan aktif.", hot_n:"{n} laporan", dogs_n:"{n} anjing",
  a_live:"Langsung, dikemas kini setiap 3 saat", a_nohot:"Belum ada kawasan panas. Muat data demo untuk mencuba."
}};
let LANG = localStorage.getItem('lang') || 'en';
const t = (k, n) => (I18N[LANG][k] ?? I18N.en[k] ?? k).replace('{n}', n);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const whyText = w => { const [c, n] = w.split(':'); return t('why_' + c, n); };
function applyLang() {
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-i18n]').forEach(e => e.textContent = t(e.dataset.i18n));
  document.querySelectorAll('[data-ph]').forEach(e => e.placeholder = t(e.dataset.ph));
  const b = document.getElementById('lang'); if (b) b.textContent = LANG === 'en' ? 'Bahasa Melayu' : 'English';
}
function setLang(l) { LANG = l; localStorage.setItem('lang', l); applyLang(); window.onLang && window.onLang(); }
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('lang').onclick = () => setLang(LANG === 'en' ? 'ms' : 'en');
  applyLang();
});

Object.assign(I18N.en, {
  login_title:"Log in", signup_title:"Sign up", f_name:"Full name", f_email:"Email", f_phone:"Phone (optional)", f_pass:"Password (8+ characters)",
  or_anon:"Report an emergency without an account", a_login:"Authority login", demo_cred:"Demo login: officer@mpspk.demo or officer@perhilitan.demo, password demo1234",
  err_role:"This is not an authority account.", hi:"Hi, {n}", pts:"{n} pts", b_bronze:"Bronze", b_silver:"Silver", b_gold:"Gold",
  my_reports:"My reports", report_tab:"Report", logout:"Log out", login:"Log in", signup:"Sign up",
  anon_note:"You are reporting anonymously. Anonymous reports have lower trust and earn no rewards.",
  as_user:"Reporting as {n}. Your account details are shared with the authority for follow-up.",
  f_cphone:"Phone for follow-up (optional)", f_cemail:"Email for follow-up (optional)",
  rew_tip:"Rewards: +5 points per report, +10 when verified, +20 when resolved. False reports lose points.",
  mine_empty:"You haven't sent any reports yet.", notif:"Notifications", reopen:"Still a problem", discuss:"Discuss ({n})",
  chat_ph:"Ask or share an update", chat_send:"Send", chat_login:"Log in to join the discussion", chat_empty:"No messages yet.", close:"Close",
  n_acknowledged:"Your report was acknowledged by the authority.", n_resolved:"Your report was marked resolved.",
  n_false:"Your report was marked as a false report.", n_followup:"Message from the authority:",
  err_rate:"Too many reports. Please wait a few minutes.", st_false:"false report", st_submitted:"submitted", st_reopened:"reopened", st_followup:"message sent",
  why_anon:"anonymous report (lower trust)", why_lowtrust:"reporter has earlier false reports",
  a_history:"Report history", a_dash:"Dashboard", h_search:"Search", h_all:"All statuses", th_contact:"Reporter", th_when:"Time", th_log:"Timeline",
  no_contact:"no contact given", note_ph:"Note for the reporter (optional)", a_false:"False report", a_msg:"Message reporter"
});
Object.assign(I18N.ms, {
  login_title:"Log masuk", signup_title:"Daftar", f_name:"Nama penuh", f_email:"E-mel", f_phone:"Telefon (pilihan)", f_pass:"Kata laluan (8+ aksara)",
  or_anon:"Laporkan kecemasan tanpa akaun", a_login:"Log masuk pihak berkuasa", demo_cred:"Log masuk demo: officer@mpspk.demo atau officer@perhilitan.demo, kata laluan demo1234",
  err_role:"Ini bukan akaun pihak berkuasa.", hi:"Hai, {n}", pts:"{n} mata", b_bronze:"Gangsa", b_silver:"Perak", b_gold:"Emas",
  my_reports:"Laporan saya", report_tab:"Lapor", logout:"Log keluar", login:"Log masuk", signup:"Daftar",
  anon_note:"Anda melapor tanpa nama. Laporan tanpa nama kurang dipercayai dan tidak mendapat ganjaran.",
  as_user:"Melapor sebagai {n}. Butiran akaun anda dikongsi dengan pihak berkuasa untuk tindakan susulan.",
  f_cphone:"Telefon untuk susulan (pilihan)", f_cemail:"E-mel untuk susulan (pilihan)",
  rew_tip:"Ganjaran: +5 mata setiap laporan, +10 apabila disahkan, +20 apabila selesai. Laporan palsu menolak mata.",
  mine_empty:"Anda belum menghantar sebarang laporan.", notif:"Notifikasi", reopen:"Masih bermasalah", discuss:"Bincang ({n})",
  chat_ph:"Tanya atau kongsi maklumat terkini", chat_send:"Hantar", chat_login:"Log masuk untuk menyertai perbincangan", chat_empty:"Belum ada mesej.", close:"Tutup",
  n_acknowledged:"Laporan anda telah diakui oleh pihak berkuasa.", n_resolved:"Laporan anda telah ditandakan selesai.",
  n_false:"Laporan anda ditandakan sebagai laporan palsu.", n_followup:"Mesej daripada pihak berkuasa:",
  err_rate:"Terlalu banyak laporan. Sila tunggu beberapa minit.", st_false:"laporan palsu", st_submitted:"dihantar", st_reopened:"dibuka semula", st_followup:"mesej dihantar",
  why_anon:"laporan tanpa nama (kurang dipercayai)", why_lowtrust:"pelapor pernah membuat laporan palsu",
  a_history:"Sejarah laporan", a_dash:"Papan pemuka", h_search:"Cari", h_all:"Semua status", th_contact:"Pelapor", th_when:"Masa", th_log:"Garis masa",
  no_contact:"tiada hubungan diberi", note_ph:"Nota untuk pelapor (pilihan)", a_false:"Laporan palsu", a_msg:"Mesej pelapor"
});
Object.assign(I18N.en, {
  wcat_sighting:"Wildlife sighting (monkey, wild boar, snake...)", wcat_pack:"Group of wild animals", wcat_aggressive:"Aggressive wild animal",
  wcat_chasing:"Chased by a wild animal", wcat_attack:"Someone was attacked or bitten", wcat_injured:"Injured wildlife",
  f_left_w:"The animal is not in my photo (I ran away)", why_wildphoto:"photo supplied (the AI only verifies dogs, so confirmations count more)"
});
Object.assign(I18N.ms, {
  wcat_sighting:"Hidupan liar kelihatan (monyet, babi hutan, ular...)", wcat_pack:"Kumpulan haiwan liar", wcat_aggressive:"Haiwan liar agresif",
  wcat_chasing:"Dikejar haiwan liar", wcat_attack:"Seseorang diserang atau digigit", wcat_injured:"Hidupan liar cedera",
  f_left_w:"Haiwan tiada dalam gambar (saya lari)", why_wildphoto:"gambar dibekalkan (AI hanya mengesahkan anjing, jadi pengesahan lebih penting)"
});
Object.assign(I18N.en, {ph_note_w:"Monkey near the playground"});
Object.assign(I18N.ms, {ph_note_w:"Monyet berhampiran taman permainan"});
