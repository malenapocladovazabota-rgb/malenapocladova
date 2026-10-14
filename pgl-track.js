/* Трекинг визитов в Agency Board (Сайты и квизы → «Сайт · New SMM»).
   Общий код PGL + расширение для New SMM:
   · время на странице считается только пока вкладка открыта на экране;
   · в сторис-страницах каждый показанный слайд записывается как шаг «страница/слайд»;
   · визит привязывается к лиду: по ответу newsmm-lead (cid) и по ссылке ?c=<id контакта>;
   · в события не попадают имя, почта и телефон, кроме контакта, который человек сам ввёл в форму.
   Лиды и заметки на доске собирает функция newsmm_site_sync в базе доски. */
(function(){
  var KEY=window.PGL_SITE; if(!KEY||window.PGL&&window.PGL._v) return;
  var URL_='https://ifrufkgqwrkexuzffzaw.supabase.co/functions/v1/track';
  function uid(){ return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,function(c){var r=Math.random()*16|0;return (c=='x'?r:(r&3|8)).toString(16);}); }
  function ls(k,v){ try{ if(v===undefined) return localStorage.getItem(k); localStorage.setItem(k,v); }catch(e){} }
  function ss(k,v){ try{ if(v===undefined) return sessionStorage.getItem(k); sessionStorage.setItem(k,v); }catch(e){} }
  var vid=ls('pgl_vid')||uid(); ls('pgl_vid',vid);
  var sk='pgl_sid_'+KEY, sid=ss(sk)||uid(); ss(sk,sid);
  var q=new URLSearchParams(location.search), utm={};
  ['utm_source','utm_medium','utm_campaign','utm_content','utm_term','fbclid','gclid','ttclid'].forEach(function(k){ var v=q.get(k); if(v) utm[k]=v.slice(0,200); });
  var saved=ss('pgl_utm'); if(Object.keys(utm).length) ss('pgl_utm',JSON.stringify(utm)); else if(saved){ try{ utm=JSON.parse(saved); }catch(e){} }
  var dev=/Mobi|Android|iPhone/i.test(navigator.userAgent)?'mobile':(/iPad|Tablet/i.test(navigator.userAgent)?'tablet':'desktop');
  var queue=[], first=true, timer=null;
  /* активное время: только пока вкладка видна */
  var act=0, lastT=Date.now(), vis=document.visibilityState!=='hidden';
  function tickA(){ var n=Date.now(); if(vis) act+=n-lastT; lastT=n; }
  document.addEventListener('visibilitychange',function(){ tickA(); vis=document.visibilityState!=='hidden'; });
  function base(){ var b={k:KEY,s:sid,v:vid,e:queue.splice(0,60)}; if(first){ b.url=location.href.slice(0,500); b.ref=document.referrer.slice(0,500); b.utm=utm; b.dev=dev; b.lang=(navigator.language||'').slice(0,10); first=false; } return b; }
  function flush(beacon){ if(!queue.length&&!first) return; var body=JSON.stringify(base());
    if(beacon&&navigator.sendBeacon){ try{ if(navigator.sendBeacon(URL_,new Blob([body],{type:'text/plain'}))) return; }catch(e){} }
    try{ fetch(URL_,{method:'POST',body:body,headers:{'Content-Type':'text/plain'},keepalive:true}).catch(function(){}); }catch(e){} }
  function push(t,step,d,now){ queue.push({t:t,step:step||null,d:d||null,ts:Date.now()}); clearTimeout(timer); if(now) flush(false); else timer=setTimeout(function(){flush(false);},1500); }
  var PGL={_v:1,
    step:function(k,label){ push('step',String(k),label?{label:String(label)}:null); },
    answer:function(k,v,label){ push('answer',String(k),{v:v,label:label?String(label):undefined}); },
    contact:function(c){ push('contact',null,{contact:c||{}}); },
    submit:function(o){ o=o||{}; push('submit',o.step||'submit',{contact:{name:o.name,email:o.email,phone:o.phone},answers:o.answers||null},true); },
    event:function(name,d){ push('event',String(name),d||null); }
  };
  window.PGL=PGL;
  push('view',null,{title:document.title.slice(0,200),path:location.pathname},true);
  function leave(){ tickA(); push('leave',null,{sec:Math.round(act/1000)}); flush(true); }
  addEventListener('pagehide',leave); document.addEventListener('visibilitychange',function(){ if(document.visibilityState==='hidden') leave(); });

  /* ── New SMM: шаги, привязка к лиду ── */
  var page=(location.pathname.replace(/^\/+|\.html$/g,'')||'home');
  var CID=/^[A-Za-z0-9]{12,40}$/;
  var cid=q.get('c'); if(cid&&CID.test(cid)) ls('pgl_cid',cid); else cid=ls('pgl_cid');
  if(cid&&CID.test(cid)) PGL.event('cid',{cid:cid});
  var sts=[].slice.call(document.querySelectorAll('section.st'));
  if(sts.length){
    var cur='';
    var chk=function(){ var s=document.querySelector('section.st.on'); if(!s) return;
      var n=s.getAttribute('data-name')||('s'+(sts.indexOf(s)+1)), k=page+'/'+n; if(k!==cur){ cur=k; PGL.step(k); } };
    try{ var mo=new MutationObserver(chk); sts.forEach(function(s){ mo.observe(s,{attributes:true,attributeFilter:['class']}); }); }catch(e){}
    chk(); setTimeout(chk,600);
  } else PGL.step(page);
  /* заявка: ответ newsmm-lead содержит cid контакта */
  var of=window.fetch;
  if(of) window.fetch=function(u){ var p=of.apply(this,arguments);
    try{ if(String(u).indexOf('/functions/v1/newsmm-lead')>-1){
        var b={}; try{ b=JSON.parse((arguments[1]||{}).body)||{}; }catch(e){}
        if(b.email||b.phone) PGL.contact({name:b.name,email:b.email,phone:b.phone});
        p.then(function(r){ return r.clone().json(); }).then(function(d){ if(d&&d.cid&&CID.test(d.cid)){ ls('pgl_cid',d.cid); PGL.event('cid',{cid:d.cid}); } }).catch(function(){});
    } }catch(e){}
    return p; };
})();
