// Dynamic job count — updates all elements with class="live-job-count"
(function(){
  fetch('/data/jobs.json?t='+Date.now(),{cache:'no-store'})
    .then(function(r){return r.json()})
    .then(function(d){
      var n=d.jobs?d.jobs.length:0;
      var els=document.querySelectorAll('.live-job-count');
      for(var i=0;i<els.length;i++){
        els[i].textContent=n.toLocaleString();
      }
    })
    .catch(function(){});
})();
