(function(){
  "use strict";

  var forcing=false;

  function forceDark(){
    if(forcing) return;
    forcing=true;
    document.documentElement.setAttribute("data-theme","dark");
    document.documentElement.style.colorScheme="dark";
    try{localStorage.setItem("theme","dark")}catch(e){}
    try{document.cookie="theme=dark;path=/;max-age=31536000;SameSite=Lax"}catch(e){}
    document.querySelectorAll(".theme-toggle,#theme-toggle,[aria-label='Toggle dark mode']").forEach(function(el){
      el.remove();
    });
    forcing=false;
  }

  forceDark();
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",forceDark);
  else forceDark();
  setTimeout(forceDark,0);
  setTimeout(forceDark,250);
  setTimeout(forceDark,1000);

  try{
    new MutationObserver(function(){setTimeout(forceDark,0)}).observe(document.body || document.documentElement,{childList:true,subtree:true});
  }catch(e){}
  window.addEventListener("storage",forceDark);
})();
