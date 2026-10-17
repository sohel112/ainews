// Ady — interactions: theme, mobile nav, search, reveal, progress, share, newsletter
(function(){
  "use strict";
  var root = document.documentElement;

  /* ---- theme ---- */
  var saved = null;
  try { saved = localStorage.getItem("aibrief-theme"); } catch(e){}
  if (saved) root.setAttribute("data-theme", saved);
  else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    root.setAttribute("data-theme", "dark");
  }
  function paintTheme(){
    var dark = root.getAttribute("data-theme") === "dark";
    document.querySelectorAll(".theme-toggle").forEach(function(b){ b.textContent = dark ? "☀️" : "🌙"; });
  }
  paintTheme();
  document.querySelectorAll(".theme-toggle").forEach(function(btn){
    btn.addEventListener("click", function(){
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("aibrief-theme", next); } catch(e){}
      paintTheme();
    });
  });

  /* ---- mobile nav ---- */
  var burger = document.getElementById("hamburger");
  var nav = document.getElementById("mainNav");
  if (burger && nav) burger.addEventListener("click", function(){
    nav.classList.toggle("open");
    burger.textContent = nav.classList.contains("open") ? "✕" : "☰";
  });

  /* ---- search ---- */
  var overlay = document.getElementById("searchOverlay");
  var input = document.getElementById("searchInput");
  var results = document.getElementById("searchResults");
  var index = [];
  fetch("search.json").then(function(r){ return r.ok ? r.json() : []; })
    .then(function(d){ index = d; }).catch(function(){});
  function openSearch(){ if(overlay){ overlay.classList.add("open"); if(input){ input.value=""; renderSearch(""); setTimeout(function(){input.focus();},50);} } }
  function closeSearch(){ if(overlay) overlay.classList.remove("open"); }
  document.querySelectorAll("[data-search-open]").forEach(function(b){ b.addEventListener("click", openSearch); });
  if(overlay) overlay.addEventListener("click", function(e){ if(e.target === overlay) closeSearch(); });
  document.addEventListener("keydown", function(e){
    if(e.key === "Escape") closeSearch();
    if((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k"){ e.preventDefault(); openSearch(); }
  });
  function esc(s){ return String(s||"").replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
  function renderSearch(q){
    q = q.trim().toLowerCase();
    if(!q){ results.innerHTML = '<div class="search-empty">Type to search articles…</div>'; return; }
    var hits = index.filter(function(a){
      return (a.title+" "+a.excerpt+" "+(a.tags||[]).join(" ")+" "+a.category).toLowerCase().indexOf(q) !== -1;
    }).slice(0,8);
    if(!hits.length){ results.innerHTML = '<div class="search-empty">No articles found for "'+esc(q)+'"</div>'; return; }
    results.innerHTML = hits.map(function(a){
      return '<a href="'+esc(a.url)+'"><div class="sr-art art" style="background:'+esc(a.grad)+'"><span class="art-letter" style="font-size:1.6rem">'+esc(a.letter)+'</span></div>'+
        '<div><h4>'+esc(a.title)+'</h4><div class="meta">'+esc(a.category)+' · '+esc(a.date)+'</div></div></a>';
    }).join("");
  }
  if(input) input.addEventListener("input", function(){ renderSearch(input.value); });

  /* ---- scroll reveal ---- */
  var io = null;
  if("IntersectionObserver" in window){
    io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add("visible"); io.unobserve(en.target); } });
    }, {threshold:.08});
    document.querySelectorAll(".reveal").forEach(function(el){ io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function(el){ el.classList.add("visible"); });
  }

  /* ---- reading progress ---- */
  var bar = document.getElementById("progressBar");
  var articleBody = document.querySelector(".article-body");
  if(bar && articleBody){
    window.addEventListener("scroll", function(){
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    }, {passive:true});
  }

  /* ---- share buttons ---- */
  document.querySelectorAll("[data-share]").forEach(function(btn){
    btn.addEventListener("click", function(){
      var type = btn.getAttribute("data-share");
      var url = encodeURIComponent(window.location.href);
      var title = encodeURIComponent(document.title);
      if(type === "x") window.open("https://twitter.com/intent/tweet?url="+url+"&text="+title, "_blank", "width=550,height=420");
      else if(type === "linkedin") window.open("https://www.linkedin.com/sharing/share-offsite/?url="+url, "_blank", "width=550,height=540");
      else if(type === "copy"){
        var done = function(){ btn.textContent = "✓"; setTimeout(function(){ btn.textContent = "🔗"; }, 1500); };
        if(navigator.clipboard) navigator.clipboard.writeText(window.location.href).then(done).catch(done);
        else done();
      }
    });
  });

  /* ---- header subscribe button → scroll to newsletter ---- */
  document.querySelectorAll("[data-subscribe]").forEach(function(b){
    b.addEventListener("click", function(){
      var nl = document.querySelector(".newsletter");
      if(nl) nl.scrollIntoView({behavior:"smooth", block:"center"});
      else if(input){ openSearch(); }
    });
  });

  /* ---- newsletter forms ---- */
  function wireForm(formId, noteId){
    var form = document.getElementById(formId);
    if(!form) return;
    form.addEventListener("submit", function(e){
      e.preventDefault();
      var em = form.querySelector('input[type="email"]').value;
      var note = document.getElementById(noteId);
      if(note) note.textContent = "You're on the list! We'll email " + em + " when the newsletter launches.";
      form.reset();
    });
  }
  wireForm("nlForm", "nlNote");
  wireForm("nlFormFooter", "nlNoteFooter");
  wireForm("nlFormSide", "nlNoteSide");
})();
