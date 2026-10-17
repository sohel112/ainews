// AI Brief — theme toggle + newsletter placeholder
(function(){
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem("aibrief-theme"); } catch(e){}
  if (saved) root.setAttribute("data-theme", saved);
  var btn = document.getElementById("themeToggle");
  function paint(){
    if(btn) btn.textContent = root.getAttribute("data-theme")==="dark" ? "☀️" : "🌙";
  }
  paint();
  if(btn) btn.addEventListener("click", function(){
    var next = root.getAttribute("data-theme")==="dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("aibrief-theme", next); } catch(e){}
    paint();
  });
  var form = document.getElementById("nlForm");
  if(form) form.addEventListener("submit", function(e){
    e.preventDefault();
    var em = document.getElementById("nlEmail").value;
    document.getElementById("nlNote").textContent = "Thanks! Newsletter signup opens soon — we'll email " + em + " when it launches.";
    form.reset();
  });
})();
