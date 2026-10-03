# Claude Code 2.1.288 本地安装二进制片段

Binary: `/Users/zhoujie/.local/share/claude/versions/2.1.288`
SHA-256: `bbe93063f7a0879a1021b2891e5c9354e5b3b98433e32efe6750f7710afed750`
Build commit: `17fe1eb736e5b1433d6ca86a1db334cec8520450`

来自安装文件中以 `// @bun @bytecode` 开头的 UTF-8 模块；保留压缩符号名，未改写代码。
这些片段不是公开 GitHub 引擎源码；官方仓库提供的是 Mods 示例及旧版本类型。

## event-registry
二进制字节位置：`182329107`。
```js
var oEn=["model.complete","model.classify","model.fork","audio.play","audio.speak","mcp.call","mcp.connect","session.cwd","session.root","session.model","session.turns","session.id","session.messages","session.repo","session.surface","session.surfaces","session.authorize","session.usage","session.version","turn.abort","prompt.read","flag.value","tool.list","tool.register","command.list","command.register","config.list","agent.list","agent.register","ui.toast","ui.status","ui.log","ui.notice","ui.invalidate","ui.open","ui.close","ui.panes","ui.selection","ui.copy","ui.blit","fs.read","fs.write","fs.list","fs.exists","fs.stat","fs.ancestors","store.get","store.set","store.delete","store.keys","state.get","state.set","clock.now","clock.sleep","clock.after","clock.every","http.fetch","process.run","process.spawn","settings.read","env.get","env.set"];var jJe=[...Xe,"tool.call","tool.check","ui.render","ui.resolve","ui.press","ui.input","ui.select","ui.message","ui.scroll","ui.focus","agent.offer","agent.spawn","prompt.submit","prompt.fill","prompt.suggest","prompt.edit","prompt.section","prompt.context","prompt.attachment","prompt.compose","tool.describe","command.run","command.describe","config.set","config.describe","telemetry.log","telemetry.mark","skill.prompt","attribution.text","session.start","session.receive","session.append","session.send","session.compact","session.attach","session.detach","session.measure","session.end","plugin.register","turn.start","turn.step","turn.complete","engine.create",...oEn];var kis=Xe.filter((e)=>e!=="classic.PreToolUse");var X_t=(e)=>jJe.includes(e);var m4r=(e)=>oEn.includes(e);var Eer=["turn.step","process.spawn"];var T6t=(e)=>Eer.includes(e);var it=new Set(jJe.filter((e)=>e.includes(".")).map((e)=>e.slice(0,e.indexOf("."))));var Ye=String.raw`(?!\p{Default_Ignorable_Code_Point})[\p{ID_Start}$_]`+String.raw`(?:(?!\p{Default_Ignorable_Code_Point})[\p{ID_Continue}$])*`;var at=new RegExp(String.raw`^${Ye}\.${Ye}$`,"u");var sEn=(e)=>at.test(e)&&!it.has(e.slice(0,e.indexOf(".")));var r4o=["managed","user","project","local","memory"];
```

## env-host-setter
二进制字节位置：`188202816`。
```js
function Nco(e){if(e.value===void 0)return delete process.env[e.name],Promise.resolve();return process.env[e.name]=e.value,Promise.resolve()}var BB=et(()=>ut().mountedImages,(e)=>e().clear()
```

## env-live-read
二进制字节位置：`179258976`。
```js
function Ntt(o,t){let _=Object.create(t);for(let[r,s]of Object.entries(o)){let n=_,e;Object.defineProperty(_,r,{get:()=>{let C=process.env[r];if(C!==n)e=s.parse(C),n=C;return e},enumerable:!0,configurable:!0})}return Object.defineProperties(_,{set:{value:(r,s)=>{process.env[r]=Its(s)}},unset:{value:(r)=>{delete process.env[r]}}}),_}var a=Ntt(_x,p),Ex={},Ln=Ntt(Ex,null),rx=import.meta.require("/$bunfs/root/chunk-4pasfk09.js").udsInboxShape,_v=Ntt(rx,null);
export{EO,
```

## session-model-reader
二进制字节位置：`188039169`。
```js
async function qoe(e,n){let r=cx();if(r===void 0)t(`$.session (${e}): no session bound; id, cwd and model answered from the process`);return{id:String(q()),cwd:n??oe(),root:Ee(),model:r?.model()??tt()}}function $Tt(){let e=new Map;return{hold:(n,r)=>{let s=Symbol(n);return e.set(n,{token:s,messages:r}),()=>{if(e.get(n)?.token===s)e.delete(n)}},current:(n)=>e
```

## request-hook-consumption
二进制字节位置：`194360294`。
```js
function _s(e,s){let{options:n}=e.args,r=s.effort!==e.sent.effort&&s.effort!==void 0,g=n.resumeIncompleteThinking===!0&&s.model!==n.model&&!WFn(e.args.messages,s.model);if(g&&!e.state.isResumeKeptTold)e.state.isResumeKeptTold=!0,Xn(n.model);return{...n,model:g?n.model:Gn(s.model,n.model),...r&&{hookEffortValue:s.effort}}}var Ts=({callModel:e,args:s,sent:n,refs:r,state:g})=>({name:"core",isCore:!0,budgetMs:0
```

## transport-client
二进制字节位置：`185932795`。
```js
let Ve={apiKey:$e.apiKey,authToken:$e.authToken,...a.ANTHROPIC_BASE_URL?{baseURL:a.ANTHROPIC_BASE_URL}:!1,...yt,...vV()&&{logger:ds()}};return new hue(Ve)}async function sJ(e,n){let r=Ir()&&Jp({skipRetrievingKeyFromApiKeyHelper:!0}).source==="no
```

## transport-fetch
二进制字节位置：`185940310`。
```js
function gJ(e,n,r,s,h){let g=e??zJ,b=He(),w=Aw(b);return async(x,A)=>{let M=new Headers(A?.headers),D=x instanceof Request?x.url:String(x),{method:K}=hRn(x,A);DZr(g,K,D);let B=M.get(Cue)??void 0;if(w&&!M.has(Cue))M.set(Cue,oJ());if(w&&(vB()&&RI()||JHe())){M.set(wI,"true");let Xe=efn(dro());if(Xe!==void 0)M.set(EI,Xe)}if(cd(D)&&Ka()&&T1e())M.set(I8e,x4n);if(w){let Xe=Q9r();if(Xe!==void 0)M.set(X9r,Xe)}try{let Xe=M.get(Cue);if(t(`[API REQUEST] ${ne
```

## mod-http-fetch
二进制字节位置：`188191102`。
```js
async function Ido({url:e,init:n},r,s){let{pluginName:g}=r,h=Bse(e,r,S_),b=n?.auth,w=b===void 0,M=w?void 0:xdo();if(M!==void 0)throw new Oe(`${g}: ${S_}: refused: ${M}`);let B=w?void 0:LTt.resolve(g,b);if(n?.auth!==void 0&&B===void 0)throw new Oe(`${g}: ${S_}: unknown auth handle; $.session.authorize() mints one`);if(n?.body!==void 0&&n.body.length>FB)throw new Oe(`${g}: ${S_}: ${h.href} refused: a request body of ${n.body.len
```

## builtin-model-apply
二进制字节位置：`199633446`。
```js
async function pNe(e,o,r,s,n,d,i,c){let u=r().fastMode;if(oae(),K_(e,r(),o,d),s((g)=>({...g,mainLoopModel:o,mainLoopModelForSession:null})),i!==void 0)p("model_switch","family_alias_stepped_down");else y("model_switch");let f=Io()?Yk(o,u):!!u;if(Io()){if(UU(),f!==!!u)s((g)=>({...g,fastMode:f})),Xk(u,f)}let M=n?await bat(o,c):null,_=M?.kind==="saved",S=`${Mke}${Yb(RE(o))}${_?" and saved as your default for new sessions":" for this session only"}`;return S+=Jhe(u,f,o,{announceKeptOn:!0}),S+=wat(M),S+=(_?uAr(o):"")||pAr(o),S}var A=3000;async function bat(e,o,r=A){let s=_n("userSettings",{model:e??void 0},void 0,o);s.then((d)=>d.error?void 0:k(e)).catch(()=>{});let n=await lt(s,r);if(n===void 0)return p("model_set_default","unconfirmed"),{kind:"unconfirmed"};if(n.error)return m("model_set_default","write_failed"),{kind:"failed",error:n.error};return y("model_set
```

## builtin-model-persistence
二进制字节位置：`199633985`。
```js
async function bat(e,o,r=A){let s=_n("userSettings",{model:e??void 0},void 0,o);s.then((d)=>d.error?void 0:k(e)).catch(()=>{});let n=await lt(s,r);if(n===void 0)return p("model_set_default","unconfirmed"),{kind:"unconfirmed"};if(n.error)return m("model_set_default","write_failed"),{kind:"failed",error:n.error};return y("model_set_default"),{kind:"saved"}}function wat(
```
