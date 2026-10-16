  // ── LCS word diff ─────────────────────────────────────────────────────────
  function diffWords(a, b) {
    const A = (a||'').split(/(\s+)/), B = (b||'').split(/(\s+)/);
    const aw = A.filter(t => t.trim()), bw = B.filter(t => t.trim());
    const n = aw.length, m = bw.length;
    const dp = Array.from({length:n+1},()=>new Array(m+1).fill(0));
    for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)
      dp[i][j]=aw[i].toLowerCase()===bw[j].toLowerCase()?dp[i+1][j+1]+1:Math.max(dp[i+1][j],dp[i][j+1]);
    const aFlag=new Array(n).fill(true),bFlag=new Array(m).fill(true);
    let i=0,j=0;
    while(i<n&&j<m){
      if(aw[i].toLowerCase()===bw[j].toLowerCase()){aFlag[i]=false;bFlag[j]=false;i++;j++;}
      else if(dp[i+1][j]>=dp[i][j+1])i++;else j++;
    }
    return{aw,bw,aFlag,bFlag};
  }

  // ── OcrLine ───────────────────────────────────────────────────────────────
  function OcrLine({words,flags,side}){
    return(
      <div className={"pf-ocr "+(side==='A'?'a':'b')}>
        <span className="lab">OCR — {side==='A'?'Master A':'Dostawca B'}</span>
        {words.map((w,i)=>(<React.Fragment key={i}>{flags[i]?<span className="d">{w}</span>:w}{" "}</React.Fragment>))}
      </div>
    );
  }

  // ── ImagePane ─────────────────────────────────────────────────────────────
  const MIN_CROP_HEIGHT = 90; // px — scale up crops shorter than this

  function ImagePane({side,field,onOpen}){
    const MAP={
      a:{tag:'①',title:'MASTER (WZORZEC A)',cls:'a'},
      b:{tag:'②',title:'DOSTAWCA (PLIK B)',cls:'b'},
      c:{tag:'③',title:'DOSTAWCA W SKALI · SIFT',cls:'c'},
      d:{tag:'④',title:'MAPA RÓŻNIC · SSIM',cls:'d'},
    }[side];
    const imgKey={a:'imgA',b:'imgB',c:'imgC',d:'imgD'}[side];
    const src=field.cutout[imgKey];
    const wrapRef=React.useRef(null);

    function scaleThinCrop(img){
      if(!img||!wrapRef.current) return;
      const ar=img.naturalHeight/img.naturalWidth;
      if(!ar||ar===0) return;
      const displayW=img.offsetWidth;
      const displayH=displayW*ar;
      if(displayH>0 && displayH<MIN_CROP_HEIGHT){
        const scale=Math.min(MIN_CROP_HEIGHT/displayH, 6);
        img.style.transformOrigin='top left';
        img.style.transform=`scale(${scale})`;
        img.style.width=`${100/scale}%`;
        wrapRef.current.style.height=`${Math.round(displayH*scale)+2}px`;
        wrapRef.current.style.overflow='hidden';
      }
    }

    return(
      <div className={"pf-pane "+MAP.cls}>
        <div className="pf-pane-tab"><span className="ti">{MAP.tag}</span>{MAP.title}</div>
        <div className="pf-pane-img" ref={wrapRef} onClick={()=>onOpen&&src&&onOpen()}>
          <div className="pf-expand-hint">⤢ Powiększ</div>
          {src
            ? <img src={"data:image/jpeg;base64,"+src} alt={"Kadr — "+MAP.title}
                   onLoad={e=>scaleThinCrop(e.target)} />
            : <div style={{padding:24,textAlign:'center',color:'#9ca3af',fontSize:13}}>Brak obrazu</div>
          }
        </div>
      </div>
    );
  }

  // ── FieldCard ─────────────────────────────────────────────────────────────
  function FieldCard({field,idx,openLb}){
    const stacked=field.layout==='stacked';
    const{aw,bw,aFlag,bFlag}=diffWords(field.ocrA,field.ocrB);
    const hasD=!!field.cutout.imgD;
    // Panel „DOSTAWCA W SKALI · SIFT" (c) ukryty na życzenie — zostają A, B i mapa różnic (d).
    const sides=stacked?['a','b']:['a','b',...(hasD?['d']:[])];
    const cols=stacked?1:sides.length;
    const prioLabel={KR:'KR · krytyczne',W:'W · ważne',I:'I · informacyjne'}[field.priority];
    return(
      <div className={"pf-card r-"+field.result} id={"pf-"+field.id}>
        <div className="pf-card-head">
          <span className="idx">{String(idx+1).padStart(2,'0')}</span>
          <span className="name">{field.name}</span>
          <span className={"pf-badge prio-"+field.priority} title={prioLabel}>
            <span className="pin"/>{field.priority}
          </span>
          <span className={"pf-badge res-"+field.result}>
            {field.result==='diff'?'RÓŻNICA':'ZGODNE'}
          </span>
        </div>
        <div className="pf-card-body">
          <div className={"pf-panes "+(stacked?'stack':'side')} style={{"--cols":cols}}>
            {stacked?(
              <React.Fragment>
                <div>
                  <ImagePane side="a" field={field} onOpen={()=>openLb(field,'a')}/>
                  <OcrLine words={aw} flags={aFlag} side="A"/>
                </div>
                <div>
                  <ImagePane side="b" field={field} onOpen={()=>openLb(field,'b')}/>
                  <OcrLine words={bw} flags={bFlag} side="B"/>
                </div>
              </React.Fragment>
            ):(
              sides.map(s=>(
                <div key={s}>
                  <ImagePane side={s} field={field} onOpen={()=>openLb(field,s)}/>
                  {s==='a'&&<OcrLine words={aw} flags={aFlag} side="A"/>}
                  {s==='b'&&<OcrLine words={bw} flags={bFlag} side="B"/>}
                </div>
              ))
            )}
          </div>
          {field.note&&(
            <div className="pf-card-note">
              <span className="ic">⚠</span>
              <span>{field.note}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Lightbox ──────────────────────────────────────────────────────────────
  function Lightbox({field,onClose}){
    const [zoom,setZoom]=React.useState(1);
    const [off,setOff]=React.useState({x:0,y:0});
    const [rotA,setRotA]=React.useState(0);
    const [rotB,setRotB]=React.useState(0);
    const drag=React.useRef(null);
    const [grabbing,setGrabbing]=React.useState(false);

    const bump=d=>setZoom(z=>Math.min(6,Math.max(0.2,+(z+d).toFixed(2))));
    const reset=React.useCallback(()=>{setZoom(1);setOff({x:0,y:0});setRotA(0);setRotB(0);},[]);

    React.useEffect(()=>{
      const h=e=>{
        if(e.key==='Escape')onClose();
        else if(e.key==='+'||e.key==='=')bump(0.25);
        else if(e.key==='-')bump(-0.25);
        else if(e.key==='0')reset();
      };
      window.addEventListener('keydown',h);
      return()=>window.removeEventListener('keydown',h);
    },[onClose,reset]);

    const onWheel=e=>{e.preventDefault();bump(e.deltaY<0?0.18:-0.18);};
    const onDown=e=>{drag.current={x:e.clientX,y:e.clientY,ox:off.x,oy:off.y};setGrabbing(true);};
    const onMove=e=>{if(!drag.current)return;setOff({x:drag.current.ox+(e.clientX-drag.current.x),y:drag.current.oy+(e.clientY-drag.current.y)});};
    const onUp=()=>{drag.current=null;setGrabbing(false);};

    const holderStyle=rot=>({
      position:'absolute',top:'50%',left:'50%',
      transform:`translate(calc(-50% + ${off.x}px),calc(-50% + ${off.y}px)) scale(${zoom}) rotate(${rot}deg)`,
      transformOrigin:'center',
    });

    const sides=[{key:'a',src:field.cutout.imgA,rot:rotA,setRot:setRotA,tag:'① MASTER A',cls:'a'},
                 {key:'b',src:field.cutout.imgB,rot:rotB,setRot:setRotB,tag:'② DOSTAWCA B',cls:'b'}];

    return(
      <div className="pf-lb" onMouseUp={onUp}>
        <div className="pf-lb-toolbar">
          <div className="pf-lb-title">
            {field.name}
            <span className="b">{field.priority} · {field.result==='diff'?'RÓŻNICA':'ZGODNE'}</span>
          </div>
          <div className="pf-lb-grp">
            <button className="pf-lb-btn" onClick={()=>bump(-0.25)}>−</button>
            <span className="pf-lb-zoom">{Math.round(zoom*100)}%</span>
            <button className="pf-lb-btn" onClick={()=>bump(0.25)}>＋</button>
            <button className="pf-lb-btn" onClick={reset}>↩ Reset</button>
          </div>
          <button className="pf-lb-btn pf-lb-close" onClick={onClose}>✕ Zamknij</button>
        </div>
        <div className="pf-lb-stage">
          {sides.map(({key,src,rot,setRot,tag,cls})=>(
            <div className="pf-lb-panel" key={key}>
              <div className="pf-lb-panel-head">
                <span className={"pf-lb-tag "+cls}>{tag}</span>
                <div className="pf-lb-rot">
                  <button onClick={()=>setRot(r=>r-90)}>↺</button>
                  <button onClick={()=>setRot(r=>r+90)}>↻</button>
                </div>
              </div>
              <div className={"pf-lb-canvas"+(grabbing?' grabbing':'')}
                   onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} onMouseLeave={onUp} onWheel={onWheel}>
                {src&&<img src={"data:image/jpeg;base64,"+src} style={holderStyle(rot)} alt={tag}/>}
                {!src&&<div style={{color:'#9fb0cc',fontSize:14}}>Brak obrazu</div>}
              </div>
              {key==='b'&&<div className="pf-lb-hint">Scroll = zoom · przeciągnij = przesuń · rotacja osobno</div>}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── IconGrid ──────────────────────────────────────────────────────────────
  function IconGrid(){
    const icons=window.REPORT_ICONS||[];
    if(!icons.length)return null;
    const PIP={diff:'≠',layout:'⇅',missing:'∅'};
    const anyDiff=icons.some(i=>i.status!=='ok');
    const counts=[
      {key:'diff',label:'różnica',color:'var(--icon-diff)'},
      {key:'layout',label:'inny układ',color:'var(--icon-layout)'},
      {key:'missing',label:'brak w B',color:'var(--icon-missing)'},
    ].map(g=>({...g,n:icons.filter(i=>i.status===g.key).length})).filter(g=>g.n);
    return(
      <React.Fragment>
        <div className="pf-sec-head">
          <h2>Siatka ikon i symboli</h2>
          <span className="ln"/>
          <span className="cnt">{icons.length} symboli · {icons.filter(i=>i.status!=='ok').length} odchyleń</span>
        </div>
        <div className={"pf-card r-"+(anyDiff?'diff':'ok')}>
          <div className="pf-card-head">
            <span className="idx">∑</span>
            <span className="name">Siatka ikon i symboli</span>
            <span className="pf-badge prio-KR"><span className="pin"/>KR</span>
            <span className={"pf-badge res-"+(anyDiff?'diff':'ok')}>{anyDiff?'RÓŻNICA':'ZGODNE'}</span>
          </div>
          <div className="pf-card-body">
            <div className="pf-panes side" style={{"--cols":2}}>
              {['A','B'].map(side=>(
                <div className={"pf-pane "+(side==='A'?'a':'b')} key={side}>
                  <div className="pf-pane-tab">
                    <span className="ti">{side==='A'?'①':'②'}</span>
                    {side==='A'?'MASTER (WZORZEC A)':'DOSTAWCA (PLIK B)'}
                  </div>
                  <div className="pf-pane-img" style={{cursor:'default'}}>
                    <div className="pf-istrip">
                      {icons.map((ic,n)=>{
                        const showStatus=side==='B'&&ic.status!=='ok';
                        const cls="pf-itile"+(showStatus?" s-"+ic.status:"");
                        return(
                          <div className={cls} key={ic.id} title={ic.label+(showStatus?' — '+ic.status.toUpperCase():'')}>
                            {side==='B'&&ic.status==='missing'?'BRAK':ic.glyph}
                            {showStatus&&<span className="pip">{PIP[ic.status]||'!'}</span>}
                            <span className="num">{n+1}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {counts.length>0&&(
              <div className="pf-ilegend">
                {counts.map(g=>(
                  <div className="pf-ileg-item" key={g.key}>
                    <span className="sw" style={{background:g.color}}/>
                    <b>{g.n}</b> {g.label}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </React.Fragment>
    );
  }

  // ── App ───────────────────────────────────────────────────────────────────
  function PfApp(){
    const fields=window.REPORT_FIELDS||[];
    const [resFilter,setResFilter]=React.useState('all');
    const [prioFilter,setPrioFilter]=React.useState('all');
    const [lb,setLb]=React.useState(null);

    const diffCount=fields.filter(f=>f.result==='diff').length;
    const okCount=fields.length-diffCount;
    const pct=fields.length?Math.round((okCount/fields.length)*100):100;

    const shown=fields.filter(f=>
      (resFilter==='all'||f.result===resFilter)&&
      (prioFilter==='all'||f.priority===prioFilter)
    );

    return(
      <React.Fragment>
        {/* summary bar */}
        <div className="pf-summary">
          <div className="pf-stat diff">
            <span className="num">{diffCount}</span>
            <span className="lbl">różnic do<br/>weryfikacji</span>
          </div>
          <div className="pf-stat ok">
            <span className="num">{okCount}</span>
            <span className="lbl">pól<br/>zgodnych</span>
          </div>
          <div className="pf-compliance">
            <div className="bar"><i style={{width:pct+'%'}}/></div>
            <span className="pct">{pct}%</span>
          </div>
          <div className="pf-filters">
            <button className={"pf-fbtn"+(resFilter==='all'&&prioFilter==='all'?' active':'')}
                    onClick={()=>{setResFilter('all');setPrioFilter('all');}}>Wszystkie</button>
            <button className={"pf-fbtn"+(resFilter==='diff'?' active':'')}
                    onClick={()=>setResFilter(resFilter==='diff'?'all':'diff')}>
              <span className="dot" style={{background:'var(--result-diff)'}}/>
              Różnice<span className="cnt">{diffCount}</span>
            </button>
            <button className={"pf-fbtn"+(prioFilter==='KR'?' active':'')}
                    onClick={()=>setPrioFilter(prioFilter==='KR'?'all':'KR')}>
              <span className="dot" style={{background:'var(--prio-critical)'}}/>
              Krytyczne
            </button>
          </div>
        </div>

        {/* cards */}
        <div style={{display:'grid',gap:'var(--pf-gap-cards)'}}>
          {shown.map((f,i)=>(
            <FieldCard key={f.id} field={f} idx={fields.indexOf(f)}
                       openLb={(field)=>setLb(field)}/>
          ))}
          {shown.length===0&&(
            <div className="pf-empty">Brak pól dla wybranego filtra.</div>
          )}
        </div>

        {/* lightbox */}
        {lb&&<Lightbox field={lb} onClose={()=>setLb(null)}/>}
      </React.Fragment>
    );
  }

  ReactDOM.createRoot(document.getElementById('pfroot')).render(<PfApp/>);
