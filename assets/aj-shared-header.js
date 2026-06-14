(function(){
  "use strict";

  function readTheme(){
    return "dark";
  }
  function writeTheme(theme){
    try{localStorage.setItem("theme","dark")}catch(e){}
    try{document.cookie="theme=dark;path=/;max-age=31536000;SameSite=Lax"}catch(e){}
  }
  function applyTheme(theme){
    document.documentElement.setAttribute("data-theme","dark");
    writeTheme("dark");
  }
  function socialLinks(){
    return '<div class="social-links" aria-label="AwesomeJobs social links">'+
      '<a class="social-link" href="https://x.com/_AwesomeJobs_" target="_blank" rel="noopener" aria-label="AwesomeJobs on X"><svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.9 2h3.3l-7.2 8.2L23.5 22h-6.7l-5.2-6.8L5.6 22H2.3l7.7-8.8L1.8 2h6.8l4.7 6.2L18.9 2Zm-1.2 18h1.8L7.6 3.9H5.7L17.7 20Z"/></svg></a>'+
      '<a class="social-link" href="https://www.instagram.com/awesome_jobs_/" target="_blank" rel="noopener" aria-label="AwesomeJobs on Instagram"><svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7.8 2h8.4A5.8 5.8 0 0 1 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8A5.8 5.8 0 0 1 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2Zm0 2A3.8 3.8 0 0 0 4 7.8v8.4A3.8 3.8 0 0 0 7.8 20h8.4a3.8 3.8 0 0 0 3.8-3.8V7.8A3.8 3.8 0 0 0 16.2 4H7.8Zm4.2 3.4a4.6 4.6 0 1 1 0 9.2 4.6 4.6 0 0 1 0-9.2Zm0 2a2.6 2.6 0 1 0 0 5.2 2.6 2.6 0 0 0 0-5.2Zm4.9-2.6a1.1 1.1 0 1 1 0 2.2 1.1 1.1 0 0 1 0-2.2Z"/></svg></a>'+
      '<a class="social-link" href="https://www.linkedin.com/in/awesomejobs" target="_blank" rel="noopener" aria-label="AwesomeJobs on LinkedIn"><svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5ZM.38 8.1h4.24V23H.38V8.1ZM8.02 8.1h4.06v2.04h.06c.57-1.08 1.96-2.22 4.03-2.22 4.31 0 5.11 2.84 5.11 6.53V23h-4.24v-7.58c0-1.81-.03-4.13-2.52-4.13-2.52 0-2.9 1.97-2.9 4V23H8.02V8.1Z"/></svg></a>'+
    '</div>';
  }
  function headerHtml(){
    return '<header class="site-header aj-shared-header">'+
      '<div class="header-inner">'+
        '<a href="/" class="logo" aria-label="AwesomeJobs home">'+
          '<img class="site-logo-img" src="/assets/site-logo.png" alt="AwesomeJobs">'+
          '<span class="logo-text"><span class="logo-awesome">Awesome</span><span class="logo-jobs">Jobs</span></span>'+
          '<span class="logo-live-badge"><span class="logo-live-dot" aria-hidden="true"></span><span id="live-count">Jobs Online</span></span>'+
        '</a>'+
        '<nav class="header-links" aria-label="Primary navigation">'+
          '<a href="/remote-developer-jobs.html">Dev</a>'+
          '<a href="/remote-devops-jobs.html">DevOps</a>'+
          '<a href="/remote-data-jobs.html">Data</a>'+
          '<a href="/remote-design-jobs.html">Design</a>'+
          '<a href="/remote-finance-jobs.html">Finance</a>'+
          '<a href="/remote-hr-jobs.html">HR</a>'+
          '<a href="/remote-qa-jobs.html">QA</a>'+
          '<a href="/remote-sales-jobs.html">Sales</a>'+
          '<a href="/remote-support-jobs.html">Support</a>'+
          '<a href="/remote-translation-jobs.html">Translation</a>'+
          '<a href="/remote-writing-jobs.html">Writing</a>'+
          '<a href="/remote-marketing-jobs.html">Marketing</a>'+
        '</nav>'+
        socialLinks()+
      '</div>'+
    '</header>';
  }
  function normalizeActiveLinks(){
    var here=(location.pathname || "/").replace(/\/index\.html$/,"/") || "/";
    document.querySelectorAll(".aj-shared-header .header-links a").forEach(function(a){
      var path=new URL(a.getAttribute("href"),location.origin).pathname.replace(/\/index\.html$/,"/") || "/";
      var active=path===here;
      a.classList.toggle("active",active);
      if(active) a.setAttribute("aria-current","page");
      else a.removeAttribute("aria-current");
    });
  }
  function updateLiveCount(){
    var el=document.getElementById("live-count");
    if(!el) return;
    fetch("/data/jobs.json?t="+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(data){
      var count=(data.jobs||[]).length;
      if(count) el.textContent=count.toLocaleString()+" Jobs Online";
    }).catch(function(){});
  }
  function enhanceInnerHeroHeading(){
    var path=location.pathname || "";
    var isJobPage=/^\/remote-(?!salary-report)[^/]*(?:\.html)?$/.test(path) || /^\/country\/remote-jobs-[^/]*(?:\.html)?$/.test(path);
    if(!isJobPage) return;
    var h1=document.querySelector(".hero h1");
    if(!h1 || h1.dataset.awesomeEnhanced==="true") return;
    var text=(h1.textContent || "").trim();
    if(!text || /^awesome\b/i.test(text)) return;
    h1.textContent="";
    var awesome=document.createElement("span");
    awesome.className="aj-awesome-heading-word";
    awesome.textContent="Awesome";
    h1.appendChild(awesome);
    h1.appendChild(document.createTextNode(" "+text));
    h1.dataset.awesomeEnhanced="true";
  }
  function categoryAccentFromPath(){
    var path=(location.pathname || "").toLowerCase();
    var accents={
      devops:"#6366f1",
      data:"#06b6d4",
      design:"#ec4899",
      finance:"#22c55e",
      hr:"#f59e0b",
      qa:"#8b5cf6",
      sales:"#f97316",
      support:"#0ea5e9",
      translation:"#14b8a6",
      writing:"#a855f7",
      marketing:"#f43f5e",
      product:"#94a3b8",
      developer:"#3b82f6"
    };
    var key=Object.keys(accents).find(function(k){return path.indexOf(k)!==-1});
    return accents[key] || "#3b82f6";
  }
  function applyInnerCategoryAccent(){
    var path=location.pathname || "";
    var isJobPage=/^\/remote-(?!salary-report)[^/]*(?:\.html)?$/.test(path) || /^\/country\/remote-jobs-[^/]*(?:\.html)?$/.test(path);
    if(!isJobPage) return;
    document.documentElement.style.setProperty("--aj-page-category-color",categoryAccentFromPath());
  }
  function placeInnerHeroWithStats(){
    var path=location.pathname || "";
    var isJobPage=/^\/remote-(?!salary-report)[^/]*(?:\.html)?$/.test(path) || /^\/country\/remote-jobs-[^/]*(?:\.html)?$/.test(path);
    if(!isJobPage) return;
    var hero=document.querySelector(".hero");
    var h1=hero && hero.querySelector("h1");
    var p=hero && hero.querySelector("p");
    var stats=document.querySelector(".stats");
    if(!hero || !h1 || !stats || stats.querySelector(".aj-stats-heading")) return;
    var heading=document.createElement("div");
    heading.className="aj-stats-heading";
    heading.appendChild(h1);
    if(p) heading.appendChild(p);
    stats.appendChild(heading);
    hero.classList.add("aj-hero-moved");
  }
  function boot(){
    applyTheme(readTheme());
    var old=document.querySelector(".site-header");
    if(old) old.outerHTML=headerHtml();
    else document.body.insertAdjacentHTML("afterbegin",headerHtml());
    normalizeActiveLinks();
    applyInnerCategoryAccent();
    enhanceInnerHeroHeading();
    placeInnerHeroWithStats();
    updateLiveCount();
    document.querySelectorAll(".theme-toggle,#theme-toggle,[aria-label='Toggle dark mode']").forEach(function(toggle){toggle.remove()});
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot);
  else boot();
})();
