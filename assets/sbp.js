/* ============================================================
   SBP Management System — shared shell + interactions
   Builds the header & sidebar on every page, wires nav/buttons.
   Pages declare context via <body data-page data-nav data-module data-crumb>
   ============================================================ */
(function () {
  "use strict";

  /* ---------- icon set (24x24 stroke) ---------- */
  var I = {
    menu:'M3 6h18M3 12h18M3 18h18',
    chevR:'m9 6 6 6-6 6', chevD:'m6 9 6 6 6-6', chevU:'m6 15 6-6 6 6',
    home:'M3 10.5 12 3l9 7.5M5 9.5V21h5v-6h4v6h5V9.5',
    recruit:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M19 8v6M22 11h-6',
    statement:'M9 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6H9ZM14 3v6h6M8 13h8M8 17h6',
    shield:'M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6l8-3ZM9 12l2 2 4-4',
    users:'M17 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M23 21v-2a4 4 0 0 0-3-3.87M16 3.13A4 4 0 0 1 16 11',
    cap:'M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 2.7 3 6 3s6-2 6-3v-5',
    db:'M12 3c4.4 0 8 1.3 8 3s-3.6 3-8 3-8-1.3-8-3 3.6-3 8-3ZM4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6',
    idcog:'M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2M8.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M19 14v3M19 21v.01M21.6 16.5l-2.6 1.5-2.6-1.5M16.4 16.5 19 18l2.6-1.5',
    flow:'M6 3v6m0 0a3 3 0 1 0 0 0ZM18 9a3 3 0 1 1 0-6 3 3 0 0 1 0 6Zm0 0v3a3 3 0 0 1-3 3H9m0 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
    route:'M5 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM19 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM5 8v4a3 3 0 0 0 3 3h6a3 3 0 0 0 3 3M9 4h8a2 2 0 0 1 2 2v6',
    lock:'M5 11h14a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1ZM8 11V7a4 4 0 0 1 8 0v4M12 15v2',
    schema:'M3 5h18v14H3zM3 10h18M3 15h18M9 5v14',
    badge:'M9 12l2 2 4-4M7.5 4.2a2 2 0 0 1 1.4-.6h6.2a2 2 0 0 1 1.4.6l1.3 1.3a2 2 0 0 1 .6 1.4v6.2a2 2 0 0 1-.6 1.4l-1.3 1.3a2 2 0 0 1-1.4.6H8.9a2 2 0 0 1-1.4-.6l-1.3-1.3a2 2 0 0 1-.6-1.4V6.9a2 2 0 0 1 .6-1.4Z',
    map:'M9 20l-5.5 2.5V6L9 3.5m0 16.5 6-2.5m-6 2.5V3.5m6 16.5 5.5 2.5V6L15 3.5m0 16.5V3.5m-6 0 6 2.5',
    pin:'M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11ZM12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z',
    star:'m12 2 3 6.3 6.9 1-5 4.9 1.2 6.8L12 18l-6.1 3 1.2-6.8-5-4.9 6.9-1L12 2Z',
    poll:'M9 17V9M15 17v-5M21 21H3M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16',
    alert:'M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z',
    save:'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2ZM17 21v-8H7v8M7 3v5h8',
    plus:'M12 5v14M5 12h14', trash:'M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6',
    edit:'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z',
    eye:'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7ZM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
    search:'M21 21l-4.3-4.3M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z',
    download:'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
    upload:'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12',
    clock:'M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
    braces:'M8 3H7a2 2 0 0 0-2 2v4c0 1.5-2 3-2 3s2 1.5 2 3v4a2 2 0 0 0 2 2h1M16 3h1a2 2 0 0 1 2 2v4c0 1.5 2 3 2 3s-2 1.5-2 3v4a2 2 0 0 1-2 2h-1',
    person:'M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0 2c-4.4 0-8 2.6-8 5.5V21h16v-1.5c0-2.9-3.6-5.5-8-5.5Z'
  };
  function svg(path, cls, w, fill) {
    w = w || 20;
    return '<svg class="' + (cls || '') + '" width="' + w + '" height="' + w + '" viewBox="0 0 24 24" fill="' +
      (fill || 'none') + '" stroke="' + (fill ? 'none' : 'currentColor') +
      '" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="' + path + '"/></svg>';
  }

  /* ---------- module navigation (global) ---------- */
  var MODULES = [
    { key:'home',        label:'Overview',                href:'index.html',        icon:I.home,      group:'ระบบประกันรายได้' },
    { key:'k2-create',   label:'สร้างเอกสาร',             href:'k2-create.html',    icon:I.plus,      group:'ระบบประกันรายได้' },
    { key:'k2-docs',     label:'เอกสาร',                  icon:I.badge,             group:'ระบบประกันรายได้', children:[
      { key:'k2-list-waiting',  label:'รอดำเนินการ',   href:'k2-list-waiting.html' },
      { key:'k2-list-related',  label:'ที่เกี่ยวข้อง',  href:'k2-list-related.html' }
      // ปิดเมนูชั่วคราว — รอตัดสินใจว่าจะใช้หน้าข้อมูลผิดปกติหรือไม่ (ไฟล์ k2-list-abnormal.html ยังอยู่ครบ)
      // ,{ key:'k2-list-abnormal', label:'ข้อมูลผิดปกติ',  href:'k2-list-abnormal.html' }
    ]},
    { key:'k2-report',   label:'รายงานสรุปสถานะ',         href:'k2-report.html',    icon:I.statement, group:'ระบบประกันรายได้' },
    { key:'k2-operators',label:'กำหนดผู้ปฏิบัติงาน',      href:'k2-operators.html', icon:I.idcog,     group:'ระบบประกันรายได้' },
    { key:'k2-factors',  label:'กำหนดปัจจัยภายนอก',       href:'k2-factors.html',   icon:I.db,        group:'ระบบประกันรายได้' },
    { key:'k2-permissions', label:'สิทธิ์การเข้าถึงเมนู',  href:'k2-permissions.html', icon:I.lock,   group:'ระบบประกันรายได้' },
    { key:'job-batch',   label:'Batch Job',                href:'job-batch.html',    icon:I.clock,     group:'ระบบประกันรายได้' },
    { key:'flow-fgi',    label:'Flow FGI/FCS',             href:'flow-fgi.html',     icon:I.flow,      group:'Flow' },
    { key:'k2-flow',     label:'Flow K2',                  href:'k2-flow.html',      icon:I.route,     group:'Flow' },
    { key:'plan-flow',   label:'Flow FGI/FCS + K2',        href:'plan-flow.html',    icon:I.flow,      group:'Flow' },
    { key:'fgi-database', label:'DB FGI/FCS',               href:'fgi-database.html', icon:I.db,        group:'Database' },
    { key:'k2-database', label:'DB K2',                     href:'k2-database.html',  icon:I.schema,    group:'Database' },
    { key:'plan-database', label:'DB FGI/FCS + K2',         href:'plan-database.html', icon:I.db,       group:'Database' },
    { key:'plan-api',    label:'API',                       href:'plan-api.html',     icon:I.braces,    group:'Plan' }
  ];
  function moduleByKey(k){
    for (var i=0;i<MODULES.length;i++){
      var m = MODULES[i];
      if (m.key===k) return m;
      if (m.children) for (var j=0;j<m.children.length;j++) if (m.children[j].key===k) return m.children[j];
    }
    return null;
  }

  /* ---------- application sub-sections (the [2/3] menu in the screenshot) ---------- */
  var APP_SECTIONS = [
    { key:'finance-hist',  label:'ประวัติฐานะทางการเงิน' },
    { key:'work-cpall',    label:'ประวัติการทำงาน กับบริษัท ซีพี ออลล์' },
    { key:'work-past',     label:'ประสบการณ์ทำงานที่ผ่านมา' },
    { key:'family',        label:'ประวัติครอบครัว' },
    { key:'business',      label:'ประวัติการดำเนินธุรกิจ' },
    { key:'finance-app',   label:'ประวัติฐานะทางการเงินของผู้สมัคร' },
    { key:'asset-app',     label:'ทรัพย์สิน-ภาระค่าใช้จ่ายของผู้สมัคร' },
    { key:'expense-family',label:'ข้อมูลภาระค่าใช้จ่าย ครอบครัว/ส่วนตัว' },
    { key:'asset-other',   label:'ทรัพย์สิน-ภาระค่าใช้จ่ายของผู้อื่นที่เกี่ยวข้อง' },
    { key:'comment',       label:'แสดงความคิดเห็น' }
  ];

  /* ---------- build header ---------- */
  function buildHeader() {
    var b = document.body;
    var moduleKey = b.getAttribute('data-module') || b.getAttribute('data-page');
    var mod = moduleByKey(moduleKey);
    var crumb = b.getAttribute('data-crumb') || (mod ? mod.label : '');
    var crumbHtml = '<a href="index.html">Home</a>';
    if (mod && mod.key !== 'home') {
      crumbHtml += sep() + '<a href="' + mod.href + '">SBP Management System</a>';
    } else {
      crumbHtml += sep() + '<span>SBP Management System</span>';
    }
    if (crumb && (!mod || mod.key !== 'home')) crumbHtml += sep() + '<span class="current">' + crumb + '</span>';
    function sep(){ return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="' + I.chevR + '"/></svg>'; }

    var h = document.createElement('header');
    h.className = 'app-header';
    h.innerHTML =
      '<button class="hamburger" id="btnMenu" aria-label="เมนู">' + svg(I.menu, '', 24) + '</button>' +
      '<a class="brand" href="index.html">' +
        '<img class="brand-logo" src="assets/logo-7-11-store-business-partner.png" width="169" height="40" alt="7-Eleven Store Business Partner">' +
      '</a>' +
      '<nav class="breadcrumb">' + crumbHtml + '</nav>' +
      '<div class="header-right">' +
        '<button class="lang" data-toast="สลับภาษา: ไทย / English (ตัวอย่าง)">' +
          '<span class="flag-th"><i class="r"></i><i class="w"></i><i class="b"></i><i class="w"></i><i class="r"></i></span> TH ' +
          svg(I.chevD, '', 16) + '</button>' +
        '<button class="user" data-toast="โปรไฟล์ผู้ใช้ (ตัวอย่าง)" style="border:none;background:none;">' +
          '<span class="avatar">' + svg(I.person, '', 22, '#fff') + '</span>' +
          '<span class="user-meta"><span class="name">Phatcharida Pra...</span><span class="role">Administrator</span></span>' +
        '</button>' +
      '</div>';
    b.insertBefore(h, b.firstChild);
  }

  /* ---------- build sidebar ---------- */
  function buildSidebar() {
    var aside = document.getElementById('sidebar');
    if (!aside) return;
    aside.className = 'sidebar';
    var nav = document.body.getAttribute('data-nav') || 'modules';

    if (nav === 'application') {
      var inApp = document.body.getAttribute('data-page') === 'application';
      var active = document.body.getAttribute('data-section') || (inApp ? 'work-cpall' : '');
      var html = '<a class="nav-item" href="recruitment.html" style="color:#2f6fed;font-weight:500;">' +
        svg(I.chevR, 'ico', 18) + '<span>กลับสู่รายการผู้สมัคร</span></a>' +
        '<div class="side-group">หัวข้อใบสมัคร</div>';
      APP_SECTIONS.forEach(function (s) {
        var on = s.key === active;
        var attrs = inApp ? 'href="#" data-section="' + s.key + '"' : 'href="application.html#' + s.key + '"';
        html += '<a class="nav-item' + (on ? ' active' : '') + '" ' + attrs + '>' +
          '<span>' + s.label + '</span>' + (on ? svg(I.chevR, 'chev', 18) : '') + '</a>';
      });
      aside.innerHTML = html;
      return;
    }

    var pageKey = document.body.getAttribute('data-page');
    var file = location.pathname.split('/').pop() || 'index.html';
    var full = file + (location.search || '');
    // เมนูลูกที่ active: (1) href ตรงทั้งไฟล์+query → (2) key ตรง data-page → (3) ไฟล์เดียวกัน (ตัวแรกชนะ)
    function activeChildIndex(children) {
      var i;
      for (i = 0; i < children.length; i++) if (children[i].href === full) return i;
      for (i = 0; i < children.length; i++) if (children[i].key === pageKey) return i;
      for (i = 0; i < children.length; i++) if (children[i].href.split('?')[0] === file) return i;
      return -1;
    }
    var groups = {}, order = [];
    MODULES.forEach(function (m) {
      var g = m.group || '_';
      if (!groups[g]) { groups[g] = []; order.push(g); }
      groups[g].push(m);
    });
    var out = '';
    order.forEach(function (g) {
      if (g !== '_') out += '<div class="side-group">' + g + '</div>';
      groups[g].forEach(function (m) {
        if (m.children) {
          var ai = activeChildIndex(m.children);
          var open = ai > -1;
          out += '<div class="nav-item nav-parent' + (open ? ' open child-on' : '') + '" data-navtoggle="' + m.key + '">' +
            svg(m.icon, 'ico', 20) + '<span>' + m.label + '</span>' + svg(I.chevR, 'chev caret', 18) + '</div>';
          out += '<div class="nav-sub' + (open ? ' open' : '') + '" data-navsub="' + m.key + '">';
          m.children.forEach(function (c, i) {
            var on = i === ai;
            out += '<a class="nav-item sub' + (on ? ' active' : '') + '" href="' + c.href + '">' +
              '<span>' + c.label + '</span>' + (on ? svg(I.chevR, 'chev', 16) : '') + '</a>';
          });
          out += '</div>';
          return;
        }
        var on = m.key === pageKey;
        out += '<a class="nav-item' + (on ? ' active' : '') + '" href="' + m.href + '">' +
          svg(m.icon, 'ico', 20) + '<span>' + m.label + '</span>' + (on ? svg(I.chevR, 'chev', 18) : '') + '</a>';
      });
    });
    aside.innerHTML = out;
  }

  /* ---------- toast ---------- */
  function toast(msg, kind) {
    var stack = document.getElementById('toast-stack');
    if (!stack) { stack = document.createElement('div'); stack.id = 'toast-stack'; document.body.appendChild(stack); }
    var t = document.createElement('div');
    t.className = 'toast ' + (kind || '');
    t.innerHTML = '<span class="tdot"></span><span>' + msg + '</span>';
    stack.appendChild(t);
    setTimeout(function () { t.style.opacity = '0'; t.style.transform = 'translateY(8px)'; t.style.transition = '.3s';
      setTimeout(function () { t.remove(); }, 320); }, 2400);
  }
  window.SBP = { toast: toast, openModal: openModal };

  /* ---------- wire interactions ---------- */
  function wire() {
    // hamburger: collapse on desktop, slide-in on mobile
    var btn = document.getElementById('btnMenu');
    if (btn) btn.addEventListener('click', function () {
      if (window.matchMedia('(max-width:860px)').matches) document.body.classList.toggle('sidebar-open');
      else document.body.classList.toggle('sidebar-collapsed');
    });

    // delegated clicks (view / edit / add / nav / actions)
    document.addEventListener('click', function (e) {
      var t = e.target.closest('.icon-view,.icon-edit,.icon-del,[data-add-row],[data-href],[data-section],[data-step],.hide-toggle,[data-toast],[data-ack],[data-navtoggle]');
      if (!t) return;
      var tbl, tr;
      if (t.hasAttribute('data-navtoggle')) {
        var sub = document.querySelector('[data-navsub="' + t.getAttribute('data-navtoggle') + '"]');
        t.classList.toggle('open');
        if (sub) sub.classList.toggle('open');
        return;
      }
      if (t.classList.contains('icon-view')) { e.preventDefault(); tbl = t.closest('table.data'); tr = t.closest('tr'); if (tbl && tr) openView(tbl, tr); return; }
      if (t.classList.contains('icon-edit')) { e.preventDefault(); tbl = t.closest('table.data'); tr = t.closest('tr'); if (tbl && tr) openEdit(tbl, tr); return; }
      if (t.classList.contains('icon-del')) { e.preventDefault(); tr = t.closest('tr'); if (tr && confirm('ยืนยันการลบรายการนี้?')) { tr.remove(); toast('ลบรายการแล้ว', 'del'); } return; }
      if (t.hasAttribute('data-add-row')) { e.preventDefault(); var at = document.getElementById(t.getAttribute('data-add-row')); if (at) openAdd(at); return; }
      if (t.hasAttribute('data-href')) { window.location.href = t.getAttribute('data-href'); return; }
      if (t.hasAttribute('data-section')) { e.preventDefault(); switchSection(t.getAttribute('data-section'), t); return; }
      if (t.hasAttribute('data-step')) { e.preventDefault(); switchStep(t.getAttribute('data-step')); return; }
      if (t.classList.contains('hide-toggle')) { e.preventDefault(); toggleCard(t); return; }
      if (t.hasAttribute('data-toast') || t.hasAttribute('data-ack')) {
        e.preventDefault();
        toast(t.getAttribute('data-toast') || t.getAttribute('data-ack'), t.getAttribute('data-kind') || (t.hasAttribute('data-ack') ? 'ok' : ''));
        return;
      }
    });

    // select-all checkboxes per table
    document.querySelectorAll('table.data').forEach(function (tbl) {
      var all = tbl.querySelector('thead .cbx');
      if (!all) return;
      var rows = function () { return [].slice.call(tbl.querySelectorAll('tbody .cbx')); };
      all.addEventListener('change', function () { rows().forEach(function (c) { c.checked = all.checked; }); });
      tbl.addEventListener('change', function (e) {
        if (e.target.classList.contains('cbx') && e.target !== all) {
          var r = rows(); all.checked = r.length && r.every(function (c) { return c.checked; });
        }
      });
    });

    // simple tab groups
    document.querySelectorAll('[data-tabs]').forEach(function (group) {
      group.addEventListener('click', function (e) {
        var t = e.target.closest('.tab'); if (!t) return;
        group.querySelectorAll('.tab').forEach(function (x) { x.classList.remove('active'); });
        t.classList.add('active');
        var key = t.getAttribute('data-tab');
        if (key) {
          document.querySelectorAll('[data-tabpane]').forEach(function (p) {
            p.hidden = p.getAttribute('data-tabpane') !== key;
          });
        }
      });
    });

    // [data-ack] / [data-toast] are handled by the delegated click handler above
    // (so dynamically-created modal buttons work too)
  }

  function switchSection(key, link) {
    document.querySelectorAll('[data-app-section]').forEach(function (s) {
      s.hidden = s.getAttribute('data-app-section') !== key;
    });
    // update sidebar active state
    document.querySelectorAll('#sidebar .nav-item').forEach(function (a) {
      a.classList.remove('active');
      var c = a.querySelector('.chev'); if (c) c.remove();
    });
    if (link) link.classList.add('active');
    var sec = document.querySelector('[data-app-section="' + key + '"]');
    var hd = document.getElementById('appSubTitle');
    if (hd && sec) hd.textContent = sec.getAttribute('data-app-title') || '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function switchStep(step) {
    var map = { '1': 'application-step1.html', '2': 'application.html', '3': 'application-step3.html' };
    if (map[step]) window.location.href = map[step];
  }

  function addRow(tableId) {
    var tbl = document.getElementById(tableId);
    if (!tbl) return;
    var body = tbl.querySelector('tbody');
    var last = body.querySelector('tr:last-child');
    var clone = last.cloneNode(true);
    clone.querySelectorAll('input.cbx').forEach(function (c) { c.checked = false; });
    clone.style.background = '#f0fff7';
    body.appendChild(clone);
    setTimeout(function () { clone.style.background = ''; }, 900);
    toast('เพิ่มแถวใหม่แล้ว — แก้ไขข้อมูลได้', 'ok');
  }

  function toggleCard(btn) {
    var card = btn.closest('.card');
    var hideEls = card.querySelectorAll('[data-hideable]');
    var hidden = btn.getAttribute('data-collapsed') === '1';
    hideEls.forEach(function (el) { el.hidden = !hidden; });
    btn.setAttribute('data-collapsed', hidden ? '0' : '1');
    btn.innerHTML = (hidden ? 'Hide' : 'Show') + ' ' + svg(hidden ? I.chevU : I.chevD, '', 18);
  }

  /* ---------- visual polish: count-up numbers ---------- */
  function countUp() {
    document.querySelectorAll('.stat .sv, [data-count]').forEach(function (el) {
      var raw = (el.getAttribute('data-count') || el.textContent).trim();
      var m = raw.match(/^([\d,]*\.?\d+)(.*)$/);
      if (!m) return;
      var target = parseFloat(m[1].replace(/,/g, ''));
      var suffix = m[2] || '';
      var dec = m[1].indexOf('.') >= 0 ? m[1].split('.')[1].length : 0;
      var dur = 1100, start = null;
      function fmt(n) { return n.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }); }
      function step(ts) {
        if (start === null) start = ts;
        var p = Math.min(1, (ts - start) / dur);
        var e = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(target * e) + suffix;
        if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(target) + suffix;
      }
      el.textContent = '0' + suffix;
      requestAnimationFrame(step);
    });
  }

  /* ---------- reveal cards on load (staggered) ---------- */
  function revealOnLoad() {
    var els = [].slice.call(document.querySelectorAll('.stat, .mod-card, .card, .flow-phase'));
    els.forEach(function (el) { el.classList.add('reveal'); });
    requestAnimationFrame(function () {
      els.forEach(function (el, i) { setTimeout(function () { el.classList.add('in'); }, Math.min(i, 14) * 55); });
    });
  }

  /* ---------- mini animated SVG charts ---------- */
  function uid() { return 'g' + Math.random().toString(36).slice(2, 8); }
  function renderCharts() {
    document.querySelectorAll('[data-chart]').forEach(function (el) {
      var type = el.getAttribute('data-chart');
      if (type === 'bar') return bar(el);
      if (type === 'donut') return donut(el);
      if (type === 'spark') return spark(el);
    });
  }
  function bar(el) {
    var vals = el.getAttribute('data-values').split(',').map(Number);
    var labs = (el.getAttribute('data-labels') || '').split(',');
    var max = Math.max.apply(null, vals) || 1;
    var W = 100, H = 60, n = vals.length, bw = W / n * 0.56, gap = W / n;
    var bars = '', lbl = '';
    vals.forEach(function (v, i) {
      var h = (v / max) * (H - 14), x = i * gap + (gap - bw) / 2, y = H - 12 - h;
      bars += '<rect class="barRect" x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + h.toFixed(1) + '" rx="2.2" style="animation-delay:' + (i * 70) + 'ms"/>';
      lbl += '<text class="barLab" x="' + (i * gap + gap / 2).toFixed(1) + '" y="' + (H - 2) + '" text-anchor="middle">' + (labs[i] || '') + '</text>';
    });
    el.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" width="100%" height="120">' + bars + lbl + '</svg>';
  }
  function donut(el) {
    var vals = el.getAttribute('data-values').split(',').map(Number);
    var cols = (el.getAttribute('data-colors') || '#2f6fed,#15b6a6,#f59e0b,#ef4444,#7c3aed').split(',');
    var total = vals.reduce(function (a, b) { return a + b; }, 0) || 1;
    var r = 52, c = 2 * Math.PI * r, cx = 70, cy = 70, acc = 0, segs = '';
    vals.forEach(function (v, i) {
      var len = v / total * c, rot = acc / total * 360 - 90;
      segs += '<circle class="donutSeg" cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + (cols[i % cols.length]) + '" stroke-width="15" stroke-dasharray="' + len.toFixed(2) + ' ' + (c - len).toFixed(2) + '" stroke-dashoffset="' + len.toFixed(2) + '" transform="rotate(' + rot.toFixed(2) + ' ' + cx + ' ' + cy + ')" style="transition-delay:' + (i * 120) + 'ms"/>';
      acc += v;
    });
    el.innerHTML = '<svg viewBox="0 0 140 140" width="150" height="150">' + segs +
      '<text x="70" y="65" text-anchor="middle" class="donutBig">' + total.toLocaleString() + '</text>' +
      '<text x="70" y="85" text-anchor="middle" class="donutSub">' + (el.getAttribute('data-center') || 'รวม') + '</text></svg>';
    requestAnimationFrame(function () {
      el.querySelectorAll('.donutSeg').forEach(function (s) { s.style.strokeDashoffset = '0'; });
    });
  }
  function spark(el) {
    var vals = el.getAttribute('data-values').split(',').map(Number);
    var W = 240, H = 60, max = Math.max.apply(null, vals), min = Math.min.apply(null, vals);
    var id = uid();
    var pts = vals.map(function (v, i) {
      var x = i / (vals.length - 1) * W;
      var y = H - 6 - (v - min) / (max - min || 1) * (H - 16);
      return [x, y];
    });
    var line = 'M' + pts.map(function (p) { return p[0].toFixed(1) + ' ' + p[1].toFixed(1); }).join(' L');
    var area = line + ' L' + W + ' ' + H + ' L0 ' + H + ' Z';
    el.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="' + H + '" preserveAspectRatio="none">' +
      '<defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="#2f6fed" stop-opacity=".28"/><stop offset="1" stop-color="#2f6fed" stop-opacity="0"/></linearGradient></defs>' +
      '<path d="' + area + '" fill="url(#' + id + ')"/>' +
      '<path class="sparkLine" d="' + line + '" fill="none" stroke="#2f6fed" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    var p = el.querySelector('.sparkLine'), L = p.getTotalLength();
    p.style.strokeDasharray = L; p.style.strokeDashoffset = L;
    requestAnimationFrame(function () { p.style.transition = 'stroke-dashoffset 1.3s ease'; p.style.strokeDashoffset = '0'; });
  }

  /* ============================================================
     CRUD modal engine — view / edit / add  (fields grounded in fcsJar)
     ============================================================ */
  function cre(tag, cls, html) { var n = document.createElement(tag); if (cls) n.className = cls; if (html != null) n.innerHTML = html; return n; }
  function esc(s) { return (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function clean(s) { return (s || '').replace(/\s+/g, ' ').trim(); }

  // grounded entity schemas (key, label, optional col = table header it maps to, type, options, wide)
  var SCHEMAS = {
    applicant: [
      { key: 'code', label: 'รหัสผู้สมัคร', col: 'รหัสผู้สมัคร' },
      { key: 'title', label: 'คำนำหน้า', type: 'select', options: ['นาย', 'นาง', 'นางสาว'] },
      { key: 'name', label: 'ชื่อ - สกุล', col: 'ชื่อ-สกุล', wide: true },
      { key: 'idcard', label: 'เลขบัตรประชาชน', col: 'เลขบัตรประชาชน' },
      { key: 'stype', label: 'ประเภทร้าน', col: 'ประเภทร้าน', type: 'select', options: ['OP (ลงทุนเอง)', 'SBP (บริษัทร่วมลงทุน)'] },
      { key: 'region', label: 'ภาค', type: 'select', options: ['RN', 'RS', 'RE', 'RW'] },
      { key: 'tel', label: 'เบอร์โทรศัพท์' },
      { key: 'email', label: 'อีเมล' },
      { key: 'status', label: 'สถานะ', col: 'สถานะ', type: 'status' },
      { key: 'date', label: 'วันที่สมัคร', col: 'วันที่สมัคร', type: 'date' }
    ],
    aduser: [
      { key: 'empid', label: 'Employee ID (EMP_ID)', col: 'Employee ID' },
      { key: 'title', label: 'คำนำหน้า (TITLE_NAME_TH)', type: 'select', options: ['นาย', 'นาง', 'นางสาว'] },
      { key: 'name', label: 'ชื่อ - สกุล (FIRST/LAST_NAME_TH)', col: 'ชื่อ-สกุล', wide: true },
      { key: 'idcard', label: 'เลขบัตรประชาชน (ID_CARD)' },
      { key: 'pos', label: 'ตำแหน่ง (POSITION_NAME)', col: 'ตำแหน่ง' },
      { key: 'store', label: 'รหัสสาขา (STORE_ID)', col: 'สาขา' },
      { key: 'etype', label: 'ประเภทพนักงาน (EMP_TYPE)', type: 'select', options: ['Full-time', 'Part-time'] },
      { key: 'domain', label: 'Domain (DOMAIN_AD)', col: 'Domain' },
      { key: 'status', label: 'สถานะ AD', col: 'สถานะ AD', type: 'status' }
    ],
    store: [
      { key: 'sid', label: 'รหัสร้าน (STORE_ID)', col: 'รหัสร้าน' },
      { key: 'sname', label: 'ชื่อร้าน (STORE_NAME)', col: 'ชื่อร้าน', wide: true },
      { key: 'prov', label: 'จังหวัด', col: 'จังหวัด' },
      { key: 'amphur', label: 'อำเภอ/เขต' },
      { key: 'stype', label: 'ประเภท (STORE_TYPE)', col: 'ประเภท', type: 'select', options: ['OP', 'SBP'] },
      { key: 'avg', label: 'ยอดขายเฉลี่ย/เดือน (บาท)', col: 'ยอดขายเฉลี่ย/เดือน (บาท)' },
      { key: 'qssi', label: 'QSSI', col: 'QSSI' }
    ],
    employee: [
      { key: 'eid', label: 'รหัสพนักงาน (EMP_ID)', col: 'รหัสพนักงาน' },
      { key: 'name', label: 'ชื่อ - สกุล', col: 'ชื่อ-สกุล', wide: true },
      { key: 'store', label: 'สาขา (STORE_ID)', col: 'สาขา' },
      { key: 'pos', label: 'ตำแหน่ง (POSITION_NAME)', col: 'ตำแหน่ง' },
      { key: 'shift', label: 'กะ', col: 'กะ', type: 'select', options: ['เช้า', 'บ่าย', 'ดึก'] },
      { key: 'etype', label: 'ประเภทพนักงาน (EMP_TYPE)', type: 'select', options: ['Full-time', 'Part-time (P/T)'] },
      { key: 'status', label: 'สถานะ', col: 'สถานะ', type: 'status' }
    ],
    operator: [
      { key: 'name', label: 'ชื่อผู้ปฏิบัติงาน (employee_name)', col: 'ชื่อผู้ปฏิบัติงาน', wide: true },
      { key: 'email', label: 'E-Mail (employee_email)', col: 'E-Mail', wide: true },
      { key: 'position', label: 'ชื่อตำแหน่ง (section_code)', col: 'ชื่อตำแหน่ง', type: 'select', options: ['ฝ่าย SBP DSA', 'เจ้าหน้าที่ SBP DSA', 'ส่งเสริมธุรกิจพันธมิตรฯ', 'GM ส่งเสริมธุรกิจฯ', 'ผู้บริหารสำนักบริหาร SBP (AVP)', 'ฝ่ายบัญชี SBP', 'บัญชีปฏิบัติการภาค'] },
      { key: 'zone', label: 'ภาคที่รับผิดชอบ (zone_code)', col: 'ภาคที่รับผิดชอบ', type: 'select', options: ['BE', 'BN', 'BS', 'BW', 'RC', 'RE', 'RN', 'RS', '-'] },
      { key: 'reason', label: 'เหตุผลการแก้ไขข้อมูล (บันทึกลง audit_logs)', wide: true }
    ],
    factor: [
      { key: 'code', label: 'รหัสปัจจัยภายนอก (factor_code)', col: 'รหัสปัจจัย' },
      { key: 'name', label: 'ชื่อปัจจัยภายนอก (factor_name)', col: 'ชื่อปัจจัย', wide: true },
      { key: 'remark', label: 'รายละเอียดเพิ่มเติม (factor_remark)', col: 'รายละเอียดเพิ่มเติม', wide: true },
      { key: 'reason', label: 'เหตุผลการแก้ไขข้อมูล (บันทึกลง audit_logs)', wide: true }
    ],
    competitor: [
      { key: 'name', label: 'ร้านคู่แข่ง (Master)', col: 'ร้านคู่แข่ง', wide: true, type: 'select',
        options: ['108 Shop', 'V Shop', 'Lotus Express', 'AM PM', 'Joy', 'Max Valu', 'Bai Chak', 'Lawson 108', 'Mini Big C', 'BATAGRO SHOP', 'Lemon Green', 'Rak Ban Kerd', 'CJ Express', 'Tops Daily', 'StarMart', 'CP FreshMark', 'Golden Place', 'Super Cheap', 'Family Mart', 'Jiffy', 'Suria', 'Fresh Mart', 'Tigermart', 'Thai Shop'] },
      { key: 'date', label: 'วันที่เปิดกระทบ', col: 'วันที่เปิดกระทบ', type: 'date' },
      { key: 'remark', label: 'รายละเอียดเพิ่มเติม', col: 'รายละเอียดเพิ่มเติม', wide: true }
    ],
    factordoc: [
      { key: 'factor', label: 'ปัจจัยภายนอก', col: 'ปัจจัยภายนอก', wide: true, type: 'select',
        options: ['ร้านคู่แข่งเปิดใหม่', 'ห้างค้าปลีกขนาดใหญ่', 'การก่อสร้าง / ปิดถนน', 'ทำเล/สถานีเปลี่ยน'] },
      { key: 'start', label: 'วันที่เริ่มต้น', col: 'วันที่เริ่มต้น', type: 'date' },
      { key: 'end', label: 'วันที่สิ้นสุด', col: 'วันที่สิ้นสุด', type: 'date' },
      { key: 'remark', label: 'รายละเอียดเพิ่มเติม', col: 'รายละเอียดเพิ่มเติม', wide: true }
    ],
    contract: [
      { key: 'sid', label: 'รหัสสาขา (STORE_ID)', col: 'รหัสสาขา' },
      { key: 'sname', label: 'ชื่อสาขา / คู่ค้า', col: 'ชื่อสาขา', wide: true },
      { key: 'ccode', label: 'เลขที่สัญญา (ContractCode)', col: 'เลขที่สัญญา' },
      { key: 'cstart', label: 'วันเริ่มสัญญา', col: 'วันเริ่มสัญญา' },
      { key: 'cend', label: 'วันหมดอายุสัญญา (EndContractDate)', col: 'วันหมดอายุ' },
      { key: 'prob', label: 'สถานะทดลองงาน (Probation)', col: 'ทดลองงาน', type: 'select', options: ['อยู่ระหว่างทดลองงาน', 'ผ่านทดลองงาน', 'ไม่ผ่าน'] },
      { key: 'invest', label: 'เงินลงทุน/ค่าธรรมเนียม (บาท)', col: 'เงินลงทุน (บาท)' },
      { key: 'goodwill', label: 'ค่า Goodwill (GoodwillFee)' },
      { key: 'guarantee', label: 'ค่าประกันความเสียหาย (DamageGuaranteeFee)' },
      { key: 'status', label: 'สถานะสัญญา', col: 'สถานะ', type: 'status' }
    ],
    grade: [
      { key: 'sid', label: 'รหัสสาขา (STORE_ID)', col: 'รหัสสาขา' },
      { key: 'sname', label: 'ชื่อสาขา', col: 'ชื่อสาขา', wide: true },
      { key: 'round', label: 'รอบประเมิน (evalMonth/Year)', col: 'รอบประเมิน' },
      { key: 'grade', label: 'เกรด (grade)', col: 'เกรด', type: 'select', options: ['A', 'B', 'C', 'D'] },
      { key: 'point', label: 'คะแนนรวม % (totalPointPercent)', col: 'คะแนน (%)' },
      { key: 'bank', label: 'เลขบัญชีธนาคาร (bankAccount)', col: 'บัญชีธนาคาร' },
      { key: 'bankname', label: 'ธนาคาร (bankName)', type: 'select', options: ['ธ.กสิกรไทย', 'ธ.ไทยพาณิชย์', 'ธ.กรุงเทพ', 'ธ.กรุงไทย'] },
      { key: 'ias', label: 'สถานะส่ง IAS', col: 'สถานะส่ง IAS', type: 'status' }
    ],
    survey: [
      { key: 'sid', label: 'รหัสแบบสอบถาม', col: 'รหัสแบบสอบถาม' },
      { key: 'sname', label: 'ชื่อแบบสอบถาม', col: 'ชื่อแบบสอบถาม', wide: true },
      { key: 'store', label: 'สาขา (Map to Store)', col: 'สาขา' },
      { key: 'resp', label: 'ผู้ตอบ (Participant)', col: 'ผู้ตอบ' },
      { key: 'status', label: 'สถานะ', col: 'สถานะ', type: 'status' },
      { key: 'date', label: 'วันที่', col: 'วันที่', type: 'date' }
    ],
    abnormal: [
      { key: 'docno', label: 'เลขที่เอกสาร', col: 'เลขที่เอกสาร' },
      { key: 'store', label: 'รหัสร้าน', col: 'รหัสร้าน' },
      { key: 'name', label: 'ชื่อร้านถูกกระทบ', col: 'ชื่อร้าน', wide: true },
      { key: 'region', label: 'ภาค', col: 'ภาค', type: 'select', options: ['BE', 'BN', 'BS', 'BW', 'RC', 'RE', 'RN', 'RS'] },
      { key: 'reason', label: 'สาเหตุผิดปกติ', col: 'สาเหตุผิดปกติ', wide: true, type: 'select', options: ['ยอดขายไม่ครบ 60 วัน', 'ข้อมูลร้านไม่ครบ', 'ไม่มีข้อมูลสาขา', 'ระยะห่างผิดปกติ'] },
      { key: 'assignee', label: 'ผู้รับผิดชอบ (แจกงาน)', col: 'ผู้รับผิดชอบ', type: 'select', options: ['- ยังไม่แจกงาน -', 'นายสมชาย ใจดี', 'นางสาวมาลี ศรีสุข', 'นายวีรพล มั่นคง', 'Phatcharida P.'] },
      { key: 'status', label: 'สถานะ', col: 'สถานะ', type: 'status' }
    ]
  };

  function tableMeta(table) {
    var ths = [].slice.call(table.querySelectorAll('thead th')), headers = [];
    var sample = table.querySelector('tbody tr');
    ths.forEach(function (th, i) {
      if (th.classList.contains('col-chk') || th.querySelector('input')) return;
      var label = clean(th.textContent);
      if (th.classList.contains('col-action') || /^Action$|จัดการ/i.test(label)) return;
      var h = { label: label, idx: i, status: false, num: false };
      if (sample && sample.children[i]) { h.status = !!sample.children[i].querySelector('.pill'); h.num = sample.children[i].classList.contains('num'); }
      headers.push(h);
    });
    return { headers: headers };
  }
  function resolveFields(table, meta) {
    var ent = table.getAttribute('data-entity');
    var base = (ent && SCHEMAS[ent]) ? SCHEMAS[ent].map(function (f) { var o = {}; for (var k in f) o[k] = f[k]; return o; })
      : meta.headers.map(function (h) { return { key: 'c' + h.idx, label: h.label, col: h.label, type: h.status ? 'status' : 'text' }; });
    base.forEach(function (f) {
      f.colIdx = -1;
      if (f.col) for (var i = 0; i < meta.headers.length; i++) {
        if (clean(meta.headers[i].label) === clean(f.col)) { f.colIdx = meta.headers[i].idx; if (meta.headers[i].status) f.type = 'status'; break; }
      }
    });
    return base;
  }
  function statusMap(table) {
    var m = {}; table.querySelectorAll('tbody .pill').forEach(function (p) {
      m[clean(p.textContent)] = [].slice.call(p.classList).filter(function (x) { return x !== 'pill'; }).join(' ');
    }); return m;
  }
  function readVal(row, f) {
    if (!row) return '';
    if (f.colIdx >= 0 && row.children[f.colIdx]) { var c = row.children[f.colIdx]; var p = c.querySelector('.pill'); return clean((p || c).textContent); }
    return row.dataset[f.key] || '';
  }
  function writeVal(row, f, val, smap) {
    if (f.colIdx >= 0 && row.children[f.colIdx]) {
      var c = row.children[f.colIdx];
      if (f.type === 'status') c.innerHTML = '<span class="pill ' + (smap[val] || 'info') + '">' + esc(val) + '</span>';
      else if (f.type === 'date') c.textContent = dateToBE(val);
      else c.textContent = val;
    } else row.dataset[f.key] = val;
  }
  function valByLabel(row, meta, label) {
    for (var i = 0; i < meta.headers.length; i++) if (clean(meta.headers[i].label) === clean(label)) {
      var c = row.children[meta.headers[i].idx]; var p = c.querySelector('.pill'); return clean((p || c).textContent);
    } return '';
  }

  /* วันที่ในตารางแสดงเป็น dd/mm/พ.ศ. แต่ input[type=date] ใช้ ISO ค.ศ. — แปลงไปกลับ */
  function dateToISO(s) {
    s = s || '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    var m = s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    if (!m) return '';
    var y = +m[3]; if (y > 2400) y -= 543;
    return y + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
  }
  function dateToBE(s) {
    var m = (s || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return s || '';
    return m[3] + '/' + m[2] + '/' + (+m[1] + 543);
  }
  function buildField(f, value, sopts) {
    var wrap = cre('div', 'field' + (f.wide ? ' col-2' : ''));
    wrap.appendChild(cre('label', null, esc(f.label)));
    var ctrl;
    if (f.type === 'status' || f.type === 'select') {
      ctrl = cre('select');
      var opts = f.type === 'status' ? (sopts && sopts.length ? sopts.slice() : [value]) : (f.options || []).slice();
      if (value && opts.indexOf(value) < 0) opts.unshift(value);
      opts.forEach(function (o) { var op = cre('option', null, esc(o)); op.value = o; if (o === value) op.selected = true; ctrl.appendChild(op); });
    } else if (f.type === 'date') {
      ctrl = cre('input'); ctrl.type = 'date'; ctrl.value = dateToISO(value);
    } else { ctrl = cre('input'); ctrl.type = 'text'; ctrl.value = value || ''; }
    ctrl.setAttribute('data-fk', f.key);
    wrap.appendChild(ctrl); return wrap;
  }
  function renderForm(fields, row, sopts) {
    var form = cre('div', 'form-grid');
    fields.forEach(function (f) { form.appendChild(buildField(f, readVal(row, f), sopts)); });
    return form;
  }
  function renderView(fields, row, table) {
    var smap = statusMap(table), grid = cre('div', 'doc-meta');
    fields.forEach(function (f) {
      var v = readVal(row, f);
      var vh = f.type === 'status' ? '<span class="pill ' + (smap[v] || 'info') + '">' + esc(v || '-') + '</span>' : esc(v || '-');
      grid.appendChild(cre('div', 'dm', '<span class="k">' + esc(f.label) + '</span><span class="v">' + vh + '</span>'));
    });
    return grid;
  }

  /* modal shell */
  function ensureOverlay() {
    var o = document.getElementById('modalOverlay');
    if (o) return o;
    o = cre('div', 'modal-overlay'); o.id = 'modalOverlay'; o.innerHTML = '<div class="modal"></div>';
    document.body.appendChild(o);
    o.addEventListener('click', function (e) { if (e.target === o) closeModal(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(); });
    return o;
  }
  function openModal(opt) {
    var o = ensureOverlay(), m = o.querySelector('.modal');
    m.className = 'modal' + (opt.lg ? ' lg' : ''); m.innerHTML = '';
    var head = cre('div', 'modal-head',
      '<div class="mh-ic">' + svg(opt.icon || I.eye, '', 20) + '</div>' +
      '<div style="flex:1"><h3>' + esc(opt.title) + '</h3>' + (opt.sub ? '<div class="mh-sub">' + esc(opt.sub) + '</div>' : '') + '</div>');
    var x = cre('button', 'modal-close', svg('M18 6 6 18M6 6l12 12', '', 18)); x.onclick = closeModal; head.appendChild(x);
    m.appendChild(head);
    var body = cre('div', 'modal-body'); if (opt.body) body.appendChild(opt.body); m.appendChild(body);
    if (opt.footer && opt.footer.length) { var foot = cre('div', 'modal-foot'); opt.footer.forEach(function (b) { foot.appendChild(b); }); m.appendChild(foot); }
    o.style.display = 'flex'; requestAnimationFrame(function () { o.classList.add('show'); });
  }
  function closeModal() { var o = document.getElementById('modalOverlay'); if (!o) return; o.classList.remove('show'); setTimeout(function () { o.style.display = 'none'; }, 200); }
  function footBtn(html, cls, fn) { var b = cre('button', 'btn ' + cls); b.innerHTML = html; b.onclick = fn; return b; }

  function subtitleOf(fields, row) {
    var f = null;
    for (var i = 0; i < fields.length; i++) if (/ชื่อ|name/i.test(fields[i].label)) { f = fields[i]; break; }
    return readVal(row, f || fields[1] || fields[0]);
  }
  function openView(table, row) {
    if (table.getAttribute('data-entity') === 'k2doc') return openK2Doc(table, row, tableMeta(table));
    var meta = tableMeta(table), fields = resolveFields(table, meta);
    var foot = [footBtn('ปิด', 'btn-ghost', closeModal)];
    if (table.getAttribute('data-entity') === 'applicant')
      foot.unshift(footBtn(svg(I.recruit, '', 17) + ' เปิดใบสมัครเต็ม', 'btn-primary', function () { location.href = 'application.html'; }));
    openModal({ title: 'รายละเอียดข้อมูล', sub: subtitleOf(fields, row), icon: I.eye, body: renderView(fields, row, table), footer: foot });
  }
  function openEdit(table, row) {
    var meta = tableMeta(table), fields = resolveFields(table, meta), sopts = Object.keys(statusMap(table));
    var body = renderForm(fields, row, sopts);
    openModal({ title: 'แก้ไขข้อมูล', sub: subtitleOf(fields, row), icon: I.edit, body: body,
      footer: [footBtn('ยกเลิก', 'btn-ghost', closeModal), footBtn('บันทึก', 'btn-primary', function () { commit(table, row, fields, body, 'edit'); })] });
  }
  function openAdd(table) {
    var meta = tableMeta(table), fields = resolveFields(table, meta), sopts = Object.keys(statusMap(table));
    var body = renderForm(fields, null, sopts);
    openModal({ title: 'เพิ่มข้อมูล', icon: I.plus, body: body,
      footer: [footBtn('ยกเลิก', 'btn-ghost', closeModal), footBtn(svg(I.plus, '', 16) + ' เพิ่มข้อมูล', 'btn-primary', function () { commit(table, null, fields, body, 'add'); })] });
  }
  function pdate(s) {
    var iso = (s || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (iso) return new Date(+iso[1], +iso[2] - 1, +iso[3]).getTime();
    var m = (s || '').match(/(\d{1,2})\/(\d{1,2})\/(\d{2,4})/); if (!m) return null;
    return new Date(+m[3], +m[2] - 1, +m[1]).getTime();
  }
  function commit(table, row, fields, form, mode) {
    var smap = statusMap(table), tb = table.querySelector('tbody'), target = row;
    // ---- validation ตาม SRS (ร้านคู่แข่ง / ปัจจัยอื่นๆ) ----
    var ent = table.getAttribute('data-entity');
    function fv(k) { var el = form.querySelector('[data-fk="' + k + '"]'); return el ? (el.value || '').trim() : ''; }
    function warn(msg) { var p = document.getElementById('k2pop'); if (p) { document.getElementById('k2popMsg').textContent = msg; p.classList.add('show'); } else toast(msg, 'del'); }
    if (ent === 'competitor' && !fv('name')) { warn('กรุณาเลือกร้านคู่แข่งที่ท่านต้องการ'); return; }
    if (ent === 'factordoc') {
      if (!fv('factor')) { warn('กรุณาเลือกปัจจัยอื่นๆ ที่ท่านต้องการ'); return; }
      var ds = pdate(fv('start')), de = pdate(fv('end'));
      if (ds && de && de < ds) { warn('วันที่สิ้นสุดต้องมีค่าเท่ากับหรือมากกว่าวันที่เริ่มต้น'); return; }
    }
    if (mode === 'add') {
      var tmpl = tb.querySelector('tr:last-child'); if (!tmpl) { closeModal(); return; }
      target = tmpl.cloneNode(true); target.classList.remove('flag-red');
      target.querySelectorAll('input.cbx').forEach(function (c) { c.checked = false; });
    }
    fields.forEach(function (f) { var inp = form.querySelector('[data-fk="' + f.key + '"]'); if (inp) writeVal(target, f, inp.value, smap); });
    if (mode === 'add') { tb.appendChild(target); target.style.background = '#f0fff7'; setTimeout(function () { target.style.background = ''; }, 1000); toast('เพิ่มข้อมูลใหม่เรียบร้อย', 'ok'); }
    else toast('บันทึกการแก้ไขเรียบร้อย', 'ok');
    closeModal();
  }

  // K2 inbox: เปิดเอกสารด้วยการอัปเดตส่วน "เอกสารข้อมูลร้านถูกกระทบ" ด้านล่าง + เลื่อนไป
  // (ไม่ใช้ modal — ใช้ description ด้านล่างซึ่งมีปุ่มผลการพิจารณาอยู่แล้ว)
  function openK2Doc(table, row, meta) {
    var g = function (l) { return valByLabel(row, meta, l) || '-'; };
    var docno = g('เลขที่เอกสาร'), store = g('รหัสร้าน'), name = g('ชื่อร้านถูกกระทบ'), region = g('ภาค'),
      drop = g('ยอดขายที่ลดลง'), comp = g('จำนวนเงินที่ชดเชย'), status = g('สถานะ');
    var sec = document.getElementById('openedDoc');
    if (!sec) return;
    function set(id, txt) { var el = document.getElementById(id); if (el) el.textContent = txt; }
    set('odDocNoTitle', docno); set('odDocNo', docno); set('odStore', store);
    set('odName', name); set('odRegion', region);
    if (drop && drop !== '-') set('odDrop', drop);
    if (comp && comp !== '-') set('odComp', comp + ' ฿');
    var st = document.getElementById('odStatus');
    if (st) { st.className = 'pill ' + (statusMap(table)[status] || 'info'); st.textContent = status; }
    sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    sec.classList.remove('flash'); void sec.offsetWidth; sec.classList.add('flash');
    toast('เปิดเอกสาร ' + docno + ' — ดูรายละเอียดและผลการพิจารณาด้านล่าง', 'ok');
  }

  /* ---------- init ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    buildHeader();
    buildSidebar();
    wire();
    revealOnLoad();
    countUp();
    renderCharts();
    // open a section from URL hash (links arriving from step 1/3 pages)
    if (document.body.getAttribute('data-page') === 'application' && location.hash) {
      var key = location.hash.slice(1);
      var link = document.querySelector('#sidebar .nav-item[data-section="' + key + '"]');
      if (link) switchSection(key, link);
    }
    // set initial app section title
    var hd = document.getElementById('appSubTitle');
    if (hd) {
      var cur = document.querySelector('[data-app-section]:not([hidden])');
      if (cur) hd.textContent = cur.getAttribute('data-app-title') || hd.textContent;
    }
  });
})();
