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
    badge:'M9 12l2 2 4-4M7.5 4.2a2 2 0 0 1 1.4-.6h6.2a2 2 0 0 1 1.4.6l1.3 1.3a2 2 0 0 1 .6 1.4v6.2a2 2 0 0 1-.6 1.4l-1.3 1.3a2 2 0 0 1-1.4.6H8.9a2 2 0 0 1-1.4-.6l-1.3-1.3a2 2 0 0 1-.6-1.4V6.9a2 2 0 0 1 .6-1.4Z',
    save:'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2ZM17 21v-8H7v8M7 3v5h8',
    plus:'M12 5v14M5 12h14', trash:'M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6',
    edit:'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z',
    eye:'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7ZM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
    search:'M21 21l-4.3-4.3M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z',
    download:'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
    upload:'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12',
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
    { key:'home',       label:'หน้าหลัก',              href:'index.html',       icon:I.home,      group:'' },
    { key:'recruitment',label:'สรรหา & ใบสมัคร',        href:'recruitment.html', icon:I.recruit,   group:'งานปฏิบัติการ' },
    { key:'statement',  label:'บัญชีแฟรนไชส์',          href:'statement.html',   icon:I.statement, group:'งานปฏิบัติการ' },
    { key:'manpower',   label:'กำลังคน',                href:'manpower.html',    icon:I.users,     group:'งานปฏิบัติการ' },
    { key:'training',   label:'อบรม',                   href:'training.html',    icon:I.cap,       group:'งานปฏิบัติการ' },
    { key:'fgi',        label:'ประกันรายได้ · ภาพรวม',   href:'fgi.html',         icon:I.shield,    group:'ประกันรายได้ (FGI)' },
    { key:'fgi-flow',   label:'ผังกระบวนการ FGI',       href:'fgi-flow.html',    icon:I.route,     group:'ประกันรายได้ (FGI)' },
    { key:'k2',         label:'ยืนยัน K2 / BPM',        href:'k2.html',          icon:I.badge,     group:'ประกันรายได้ (FGI)' },
    { key:'masterdata', label:'ข้อมูลหลัก',             href:'masterdata.html',  icon:I.db,        group:'ระบบ' },
    { key:'useradmin',  label:'ผู้ใช้ & Active Directory', href:'useradmin.html',icon:I.idcog,    group:'ระบบ' },
    { key:'workflow',   label:'อนุมัติงาน',             href:'workflow.html',    icon:I.flow,      group:'ระบบ' }
  ];
  function moduleByKey(k){ for (var i=0;i<MODULES.length;i++) if (MODULES[i].key===k) return MODULES[i]; return null; }

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
        '<div class="seven-logo"><span class="band b1"></span><span class="band b2"></span><span class="band b3"></span><span class="seven">7</span></div>' +
        '<div class="brand-text"><div class="l1">STORE</div><div class="l2">BUSINESS PARTNER</div></div>' +
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
  window.SBP = { toast: toast };

  /* ---------- wire interactions ---------- */
  function wire() {
    // hamburger: collapse on desktop, slide-in on mobile
    var btn = document.getElementById('btnMenu');
    if (btn) btn.addEventListener('click', function () {
      if (window.matchMedia('(max-width:860px)').matches) document.body.classList.toggle('sidebar-open');
      else document.body.classList.toggle('sidebar-collapsed');
    });

    // delegated clicks
    document.addEventListener('click', function (e) {
      var el = e.target.closest('[data-toast],[data-href],[data-section],[data-step],[data-add-row],.icon-del,.hide-toggle');
      if (!el) return;

      if (el.hasAttribute('data-href')) { window.location.href = el.getAttribute('data-href'); return; }

      if (el.hasAttribute('data-section')) {
        e.preventDefault();
        switchSection(el.getAttribute('data-section'), el);
        return;
      }
      if (el.hasAttribute('data-step')) { e.preventDefault(); switchStep(el.getAttribute('data-step')); return; }

      if (el.hasAttribute('data-add-row')) { e.preventDefault(); addRow(el.getAttribute('data-add-row')); return; }

      if (el.classList.contains('icon-del')) {
        e.preventDefault();
        var tr = el.closest('tr');
        if (tr && confirm('ยืนยันการลบรายการนี้?')) { tr.remove(); toast('ลบรายการแล้ว', 'del'); }
        return;
      }

      if (el.classList.contains('hide-toggle')) { e.preventDefault(); toggleCard(el); return; }

      if (el.hasAttribute('data-toast')) { e.preventDefault(); toast(el.getAttribute('data-toast'), el.getAttribute('data-kind') || ''); return; }
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

    // generic action buttons that should just acknowledge
    document.querySelectorAll('[data-ack]').forEach(function (b) {
      b.addEventListener('click', function () { toast(b.getAttribute('data-ack'), b.getAttribute('data-kind') || 'ok'); });
    });
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
