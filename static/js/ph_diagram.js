(function () {
  'use strict';
  let timer, controller, generation = 0;
  const NS = 'http://www.w3.org/2000/svg';
  function node(tag, attrs, text) {
    const el = document.createElementNS(NS, tag);
    Object.entries(attrs || {}).forEach(([k,v]) => el.setAttribute(k,v));
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function display(data, mode) {
    const panel = document.querySelector('.ph-panel[data-mode="' + mode + '"]');
    const svg = panel.querySelector('svg'); svg.replaceChildren();
    const L=76,R=686,T=40,B=372;
    const all = [...data.envelope.liquid,...data.envelope.vapor,...data.points.map(p=>[p.h,p.p])];
    const hs=all.map(p=>p[0]), ps=all.map(p=>p[1]).concat([data.low_pressure,data.high_pressure]);
    const hmin=Math.floor((Math.min(...hs)-25)/50)*50,hmax=Math.ceil((Math.max(...hs)+25)/50)*50;
    const pmin=Math.min(...ps)*0.85,pmax=Math.max(...ps)*1.22;
    const x=h=>L+(h-hmin)/(hmax-hmin)*(R-L);
    const y=p=>B-Math.log(p/pmin)/Math.log(pmax/pmin)*(B-T);
    const add=(tag,attrs,text)=>{const el=node(tag,attrs,text);svg.append(el);return el;};
    add('title',{},data.refrigerant+' pressure–enthalpy diagram');
    add('desc',{},'Absolute pressure on a logarithmic axis, specific enthalpy on the horizontal axis.');
    add('rect',{x:L,y:T,width:R-L,height:B-T,rx:8,fill:'#f8fbfe'});
    const ticks=[0.04,0.06,0.1,0.2,0.4,0.6,1,2,4,6,8,10];
    ticks.filter(p=>p>pmin&&p<pmax).forEach(p=>{
      add('line',{x1:L,x2:R,y1:y(p),y2:y(p),stroke:'#dce5ef','stroke-width':1});
      add('text',{x:L-10,y:y(p)+4,'text-anchor':'end',fill:'#64748b','font-size':12},p.toString());
    });
    const step=(hmax-hmin)>650?100:50;
    for(let h=hmin;h<=hmax;h+=step){
      add('line',{x1:x(h),x2:x(h),y1:T,y2:B,stroke:'#e5edf4','stroke-width':1});
      add('text',{x:x(h),y:B+23,'text-anchor':'middle',fill:'#64748b','font-size':12},String(h));
    }
    add('text',{x:20,y:(T+B)/2,transform:'rotate(-90 20 '+((T+B)/2)+')','text-anchor':'middle',fill:'#334155','font-size':13,'font-weight':600},'Pressure · MPa(abs) · log scale');
    add('text',{x:(L+R)/2,y:B+55,'text-anchor':'middle',fill:'#334155','font-size':13,'font-weight':600},'Specific enthalpy h · kJ/kg');
    const path=arr=>arr.map((p,i)=>(i?'L':'M')+x(p[0])+','+y(p[1])).join(' ');
    const dome=[...data.envelope.liquid,...[...data.envelope.vapor].reverse()];
    add('path',{d:path(dome)+' Z',fill:'#e5f1fa',opacity:0.65});
    [data.envelope.liquid,data.envelope.vapor].forEach(arr=>add('path',{d:path(arr),fill:'none',stroke:'#547590','stroke-width':2.2}));
    add('text',{x:L+20,y:T+21,fill:'#547590','font-size':12,'font-weight':700},data.refrigerant+' · saturation envelope');
    add('text',{x:L+20,y:B-17,fill:'#64748b','font-size':11},'Liquid');
    add('text',{x:(x(data.envelope.liquid[10][0])+x(data.envelope.vapor[10][0]))/2,y:B-17,'text-anchor':'middle',fill:'#64748b','font-size':11},'Liquid + vapor');
    add('text',{x:R-14,y:B-17,'text-anchor':'end',fill:'#64748b','font-size':11},'Vapor');
    [data.high_pressure,data.low_pressure].forEach((p,i)=>{
      add('line',{x1:L,x2:R,y1:y(p),y2:y(p),stroke:i?'#2788cd':'#e05252','stroke-dasharray':'4 5',opacity:0.6});
      add('text',{x:R-6,y:y(p)-8,'text-anchor':'end',fill:i?'#1675b6':'#c43e3e','font-size':11},(i?'Low ':'High ')+p.toFixed(3)+' MPa(abs)');
    });
    if(data.points.length){
      const colors=['#885bc8','#e05252','#d79a27','#2788cd'];
      data.points.forEach((p,i)=>{
        const q=data.points[(i+1)%4],x1=x(p.h),y1=y(p.p),x2=x(q.h),y2=y(q.p);
        add('line',{x1,y1,x2,y2,stroke:colors[i],'stroke-width':3.2,'stroke-linecap':'round',...(i===0?{'stroke-dasharray':'6 4'}:{})});
        const mx=(x1+x2)/2,my=(y1+y2)/2,angle=Math.atan2(y2-y1,x2-x1)*180/Math.PI;
        add('path',{d:'M -5 -4 L 5 0 L -5 4 Z',fill:colors[i],transform:'translate('+mx+' '+my+') rotate('+angle+')'});
      });
      data.points.forEach(p=>{
        const g=add('g',{});g.append(node('circle',{cx:x(p.h),cy:y(p.p),r:11,fill:'#fff',stroke:'#233f59','stroke-width':2}));
        g.append(node('text',{x:x(p.h),y:y(p.p)+4,'text-anchor':'middle',fill:'#183247','font-size':12,'font-weight':800},p.n));
        g.append(node('title',{},'Point '+p.n+': '+p.h.toFixed(2)+' kJ/kg; '+p.p.toFixed(3)+' MPa(abs)'));
      });
      const sat=data.saturation;
      [[data.points[2].h,sat.liquid_high,data.high_pressure,'SC'],[sat.vapor_low,data.points[0].h,data.low_pressure,'SH'],[sat.vapor_high,data.points[1].h,data.high_pressure,'DSH']].forEach(([a,b,p,label])=>{
        const yy=y(p)+(label==='SH'?30:-30);
        add('path',{d:`M ${x(a)} ${yy-4} V ${yy+4} M ${x(a)} ${yy} H ${x(b)} M ${x(b)} ${yy-4} V ${yy+4}`,stroke:'#334155',fill:'none'});
        add('text',{x:(x(a)+x(b))/2,y:yy-7,'text-anchor':'middle','font-size':11,fill:'#334155','font-weight':700},label);
      });
    }
    panel.querySelector('.ph-status').textContent=data.warnings.length
      ? data.warnings.join(' • ')+(data.points.length?' • The chart shows measured points; please verify abnormal readings.':' — Only the saturation envelope is shown until the readings are corrected.')
      :'Point 1: Suction → 2: Discharge → 3: Condenser outlet → 4: Expansion valve outlet • h₃ = h₄';
    panel.querySelector('.ph-status').classList.toggle('is-warning',!!data.warnings.length);
    panel.querySelector('.ph-saturation').textContent='High: bubble '+data.high_temperature.toFixed(2)+' °C / dew '+data.high_dew.toFixed(2)+' °C • Low: dew '+data.low_temperature.toFixed(2)+' °C';
    const states=panel.querySelector('.ph-states');states.replaceChildren();
    if(data.points.length){
      const table=document.createElement('table');
      const head=document.createElement('tr');
      ['Point','Position','P abs · MPa','h · kJ/kg','T · °C'].forEach(t=>{const th=document.createElement('th');th.textContent=t;head.append(th);});table.append(head);
      const names=['Compressor inlet','Compressor outlet',mode==='cooling'?'Outdoor outlet':'Indoor outlet','Expansion outlet'];
      data.points.forEach((p,i)=>{const tr=document.createElement('tr');[p.n,names[i],p.p.toFixed(3),p.h.toFixed(2),p.t===null?'—':p.t.toFixed(1)].forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td);});table.append(tr);});states.append(table);
    }
  }
  function clear(mode,message) {
    const panel=document.querySelector('.ph-panel[data-mode="'+mode+'"]');
    panel.querySelector('svg').replaceChildren();panel.querySelector('.ph-states').replaceChildren();
    panel.querySelector('.ph-saturation').textContent='';
    panel.querySelector('.ph-status').textContent=message;
    const prefix=mode==='cooling'?'c':'h';
    ['sc','sh','dsh'].forEach(k=>{document.getElementById(prefix+'_'+k+'_badge').textContent='—';document.getElementById('ph_'+prefix+'_'+k).textContent='—';});
    ['agHiTemp','agLowTemp'].forEach(id=>document.getElementById(id).textContent='—');
    ['ngHiTemp','ngLowTemp','ngHiPress','ngLowPress'].forEach(id=>document.getElementById(id).value='');
  }
  window.updatePHDiagram=function(payload,mode,missing){
    clearTimeout(timer);if(controller)controller.abort();const version=++generation;
    clear(mode,missing?'Enter at least one coil temperature in each row.':'Calculating…');
    if(missing)return;
    timer=setTimeout(async()=>{
      controller=new AbortController();
      try{
        const response=await fetch(document.body.dataset.phUrl+'?'+new URLSearchParams(payload),{signal:controller.signal});
        const data=await response.json();if(version!==generation)return;
        if(!response.ok)throw new Error(data.error||'Unable to calculate.');
        const prefix=mode==='cooling'?'c':'h';
        ['sc','sh','dsh'].forEach(k=>{document.getElementById(prefix+'_'+k+'_badge').textContent=data[k].toFixed(1);document.getElementById('ph_'+prefix+'_'+k).textContent=data[k].toFixed(1);});
        document.getElementById('agHiTemp').textContent=data.high_temperature.toFixed(3);
        document.getElementById('agLowTemp').textContent=data.low_temperature.toFixed(3);
        document.getElementById('ngHiTemp').value=data.high_temperature.toFixed(2);
        document.getElementById('ngLowTemp').value=data.low_temperature.toFixed(2);
        document.getElementById('ngHiPress').value=data.high_gauge.toFixed(3);
        document.getElementById('ngLowPress').value=data.low_gauge.toFixed(3);
        display(data,mode);
      }catch(error){if(error.name!=='AbortError'&&version===generation)clear(mode,error.message);}
    },220);
  };
  window.resetPHDiagrams=function(message){
    if(controller)controller.abort();
    clearTimeout(timer);generation++;
    clear('cooling',message||'Enter data to calculate.');
    clear('heating',message||'Enter data to calculate.');
  };
})();
