/* ============================================================================
   hero3d.js — Elite Bot Studios hero scene
   A hand-written WebGL2 renderer. No libraries, no CDN, no network beyond the
   two local textures. Renders the EB-01 board: soldermask, copper, silkscreen,
   real component geometry, a receding test-bench grid and dust motes, with a
   hand-rolled post chain (bright-pass -> separable blur -> ACES tonemap).

   Degradation is deliberate and layered:
     1. prefers-reduced-motion  -> never initialises; the poster stays.
     2. no WebGL2               -> never initialises; the poster stays.
     3. shader/context failure  -> contextlost handler bails to the poster.
     4. slow frame budget       -> drops render scale, then bloom taps.

   The poster image is the LCP element in every path. The GPU work only ever
   runs after it has painted, and never while the section is off-screen.
   ========================================================================= */

const P=[{"id":"J1","k":"terminal","x":-0.41,"z":-0.165,"hx":0.03,"hz":0.075,"h":0.075,"c":[0.1255,0.3765,0.2902]},{"id":"J9","k":"terminal","x":-0.41,"z":0.205,"hx":0.03,"hz":0.075,"h":0.075,"c":[0.1255,0.3765,0.2902]},{"id":"F1","k":"fuse","x":-0.305,"z":-0.165,"hx":0.028,"hz":0.011,"h":0.014,"c":[0.8471,0.8471,0.8235]},{"id":"D3","k":"smd","x":-0.305,"z":-0.29,"hx":0.026,"hz":0.015,"h":0.01,"c":[0.0941,0.102,0.1137]},{"id":"C1","k":"can","x":-0.185,"z":-0.29,"hx":0.048,"hz":0.048,"h":0.075,"c":[0.5961,0.6196,0.651]},{"id":"C2","k":"can","x":-0.185,"z":-0.04,"hx":0.048,"hz":0.048,"h":0.075,"c":[0.5961,0.6196,0.651]},{"id":"L1","k":"ind","x":-0.305,"z":0.08,"hx":0.05,"hz":0.05,"h":0.05,"c":[0.1176,0.1333,0.149]},{"id":"U2","k":"smd","x":-0.185,"z":0.205,"hx":0.03,"hz":0.02,"h":0.01,"c":[0.0941,0.102,0.1137]},{"id":"U1","k":"module","x":-0.035,"z":-0.02,"hx":0.072,"hz":0.06,"h":0.035,"c":[0.1176,0.1333,0.149]},{"id":"Y1","k":"smd","x":-0.035,"z":-0.115,"hx":0.018,"hz":0.011,"h":0.01,"c":[0.5961,0.6196,0.651]},{"id":"J4","k":"header","x":-0.035,"z":0.18,"hx":0.055,"hz":0.012,"h":0.012,"c":[0.0941,0.102,0.1137]},{"id":"C4","k":"smd","x":0.07,"z":0.235,"hx":0.012,"hz":0.008,"h":0.01,"c":[0.1176,0.1333,0.149]},{"id":"C5","k":"smd","x":0.115,"z":0.235,"hx":0.012,"hz":0.008,"h":0.01,"c":[0.1176,0.1333,0.149]},{"id":"Q1","k":"dpak","x":0.09,"z":0.095,"hx":0.024,"hz":0.032,"h":0.014,"c":[0.0941,0.102,0.1137]},{"id":"Q2","k":"dpak","x":0.09,"z":0.005,"hx":0.024,"hz":0.032,"h":0.014,"c":[0.0941,0.102,0.1137]},{"id":"D1","k":"smd","x":0.185,"z":0.005,"hx":0.021,"hz":0.012,"h":0.01,"c":[0.1176,0.1333,0.149]},{"id":"K1","k":"relay","x":0.3,"z":-0.15,"hx":0.095,"hz":0.07,"h":0.055,"c":[0.1098,0.3059,0.5412]},{"id":"C6","k":"can","x":0.38,"z":0.07,"hx":0.04,"hz":0.04,"h":0.045,"c":[0.5961,0.6196,0.651]},{"id":"J3","k":"terminal","x":0.45,"z":0.235,"hx":0.03,"hz":0.07,"h":0.075,"c":[0.1255,0.3765,0.2902]},{"id":"J5","k":"usb","x":0.445,"z":-0.29,"hx":0.036,"hz":0.026,"h":0.03,"c":[0.5961,0.6196,0.651]},{"id":"R5","k":"smd","x":0.185,"z":-0.29,"hx":0.022,"hz":0.011,"h":0.01,"c":[0.0941,0.102,0.1137]},{"id":"D4","k":"led","x":0.035,"z":0.3,"hx":0.013,"hz":0.013,"h":0.009,"c":[0.9608,0.651,0.1373]},{"id":"D5","k":"led","x":0.09,"z":0.3,"hx":0.013,"hz":0.013,"h":0.009,"c":[0.1765,0.8314,0.749]},{"id":"R6","k":"smd","x":0.15,"z":0.3,"hx":0.013,"hz":0.008,"h":0.01,"c":[0.0941,0.102,0.1137]},{"id":"R7","k":"smd","x":0.205,"z":0.3,"hx":0.013,"hz":0.008,"h":0.01,"c":[0.0941,0.102,0.1137]},{"id":"TP1","k":"pad","x":0.075,"z":-0.215,"hx":0.017,"hz":0.017,"h":0.0012,"c":[0.8392,0.698,0.3451]},{"id":"TP2","k":"pad","x":0.145,"z":-0.215,"hx":0.017,"hz":0.017,"h":0.0012,"c":[0.8392,0.698,0.3451]},{"id":"TP3","k":"pad","x":-0.07,"z":-0.23,"hx":0.017,"hz":0.017,"h":0.0012,"c":[0.8392,0.698,0.3451]}];
const BW = 1.0, BD = 0.75, BT = 0.016, R = 0.030;   // board: 100 x 75 x 1.6 mm
const FLOOR_Y = -0.62;
const D2R = Math.PI / 180;

/* ---------------------------------------------------------------- mat4 ---- */
function m4id_UNUSED(){ return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]); }
function m4mul(a,b,o){
  o = o || new Float32Array(16);
  for (let c=0;c<4;c++){
    const b0=b[c*4], b1=b[c*4+1], b2=b[c*4+2], b3=b[c*4+3];
    o[c*4  ] = a[0]*b0 + a[4]*b1 + a[8 ]*b2 + a[12]*b3;
    o[c*4+1] = a[1]*b0 + a[5]*b1 + a[9 ]*b2 + a[13]*b3;
    o[c*4+2] = a[2]*b0 + a[6]*b1 + a[10]*b2 + a[14]*b3;
    o[c*4+3] = a[3]*b0 + a[7]*b1 + a[11]*b2 + a[15]*b3;
  }
  return o;
}
function m4persp(fovy, aspect, near, far, o){
  o = o || new Float32Array(16);
  const f = 1/Math.tan(fovy/2), nf = 1/(near-far);
  o[0]=f/aspect; o[1]=0; o[2]=0; o[3]=0;
  o[4]=0; o[5]=f; o[6]=0; o[7]=0;
  o[8]=0; o[9]=0; o[10]=(far+near)*nf; o[11]=-1;
  o[12]=0; o[13]=0; o[14]=2*far*near*nf; o[15]=0;
  return o;
}
function m4lookAt(eye, target, up, o){
  o = o || new Float32Array(16);
  let zx=eye[0]-target[0], zy=eye[1]-target[1], zz=eye[2]-target[2];
  let l=Math.hypot(zx,zy,zz)||1; zx/=l; zy/=l; zz/=l;
  let xx=up[1]*zz-up[2]*zy, xy=up[2]*zx-up[0]*zz, xz=up[0]*zy-up[1]*zx;
  l=Math.hypot(xx,xy,xz)||1; xx/=l; xy/=l; xz/=l;
  const yx=zy*xz-zz*xy, yy=zz*xx-zx*xz, yz=zx*xy-zy*xx;
  o[0]=xx; o[1]=yx; o[2]=zx; o[3]=0;
  o[4]=xy; o[5]=yy; o[6]=zy; o[7]=0;
  o[8]=xz; o[9]=yz; o[10]=zz; o[11]=0;
  o[12]=-(xx*eye[0]+xy*eye[1]+xz*eye[2]);
  o[13]=-(yx*eye[0]+yy*eye[1]+yz*eye[2]);
  o[14]=-(zx*eye[0]+zy*eye[1]+zz*eye[2]);
  o[15]=1;
  return o;
}
function m4trs(tx,ty,tz, rx,ry, o){
  o = o || new Float32Array(16);
  const cx=Math.cos(rx), sx=Math.sin(rx), cy=Math.cos(ry), sy=Math.sin(ry);
  // R = Ry * Rx   (yaw then pitch)
  o[0]=cy;      o[1]=0;      o[2]=-sy;    o[3]=0;
  o[4]=sy*sx;   o[5]=cx;     o[6]=cy*sx;  o[7]=0;
  o[8]=sy*cx;   o[9]=-sx;    o[10]=cy*cx; o[11]=0;
  o[12]=tx;     o[13]=ty;    o[14]=tz;    o[15]=1;
  return o;
}

/* --------------------------------------------------------- gl plumbing ---- */
function compile(gl, type, src, label){
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
    const log = gl.getShaderInfoLog(s);
    gl.deleteShader(s);
    throw new Error('['+label+'] '+(log||'shader compile failed'));
  }
  return s;
}
function program(gl, vsSrc, fsSrc, label){
  const p = gl.createProgram();
  gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, vsSrc, label+'.vert'));
  gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, fsSrc, label+'.frag'));
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS))
    throw new Error('['+label+'] '+(gl.getProgramInfoLog(p)||'link failed'));
  const u = {}, a = {};
  const nu = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for (let i=0;i<nu;i++){ const n=gl.getActiveUniform(p,i).name.replace(/\[0\]$/,''); u[n]=gl.getUniformLocation(p,n); }
  const na = gl.getProgramParameter(p, gl.ACTIVE_ATTRIBUTES);
  for (let i=0;i<na;i++){ const n=gl.getActiveAttrib(p,i).name; a[n]=gl.getAttribLocation(p,n); }
  return {p, u, a};
}
function vbo(gl, data, Target){
  const b = gl.createBuffer();
  gl.bindBuffer(Target || gl.ARRAY_BUFFER, b);
  gl.bufferData(Target || gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
  return b;
}
function attrib(gl, loc, buf, size, divisor){
  if (loc === undefined || loc === null || loc < 0) return;
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
  if (divisor !== undefined) gl.vertexAttribDivisor(loc, divisor);
}

/* ------------------------------------------------------------ geometry ---- */
// unit cube, positions -1..1, flat normals, 24 verts
function cube(){
  const F=[
    [[1,-1,-1],[1,-1,1],[1,1,1],[1,1,-1]],       // +x
    [[-1,-1,1],[-1,-1,-1],[-1,1,-1],[-1,1,1]],   // -x
    [[-1,1,-1],[1,1,-1],[1,1,1],[-1,1,1]],       // +y
    [[-1,-1,1],[1,-1,1],[1,-1,-1],[-1,-1,-1]],   // -y
    [[1,-1,1],[-1,-1,1],[-1,1,1],[1,1,1]],       // +z
    [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1]]    // -z
  ];
  const N=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
  const pos=[], nrm=[];
  for (let f=0;f<6;f++){
    const q=F[f], n=N[f];
    for (const i of [0,1,2, 0,2,3]){ pos.push(...q[i]); nrm.push(...n); }
  }
  return { pos:new Float32Array(pos), nrm:new Float32Array(nrm), count:pos.length/3 };
}
// unit cylinder: radius 1 in xz, y -1..1, 28 sides, non-indexed
function cylinder(sides){
  sides = sides || 28;
  const pos=[], nrm=[];
  const ring=[];
  for (let i=0;i<sides;i++){
    const a=i/sides*Math.PI*2;
    ring.push([Math.cos(a), Math.sin(a)]);
  }
  for (let i=0;i<sides;i++){
    const c0=ring[i], c1=ring[(i+1)%sides];
    const A=[c0[0],-1,c0[1]], B=[c1[0],-1,c1[1]], C=[c1[0],1,c1[1]], D=[c0[0],1,c0[1]];
    const n0=[c0[0],0,c0[1]], n1=[c1[0],0,c1[1]];
    const V=[A,B,C,A,C,D], N=[n0,n1,n1,n0,n1,n1];
    for (let k=0;k<6;k++){ pos.push(V[k][0],V[k][1],V[k][2]); nrm.push(N[k][0],N[k][1],N[k][2]); }
  }
  for (let i=0;i<sides;i++){
    const c0=ring[i], c1=ring[(i+1)%sides];
    pos.push(0,1,0, c0[0],1,c0[1], c1[0],1,c1[1]);
    nrm.push(0,1,0, 0,1,0, 0,1,0);
    pos.push(0,-1,0, c1[0],-1,c1[1], c0[0],-1,c0[1]);
    nrm.push(0,-1,0, 0,-1,0, 0,-1,0);
  }
  return { pos:new Float32Array(pos), nrm:new Float32Array(nrm), count:pos.length/3 };
}
// rounded-rect prism for the PCB slab. The top face is a polar grid radiating
// from the centre out to an analytic rounded-rect rim, so (a) the silhouette is
// exact and (b) UVs interpolate over ~2 mm cells instead of one huge fan, which
// is what stops the 2048px soldermask atlas from smearing.
function slab(opt){
  opt = opt || {};
  const hx=BW/2, hz=BD/2, r=R;
  const rimSeg = opt.rim || 160;          // rim samples around the perimeter
  const rings  = opt.rings || 20;         // radial subdivisions
  const sideV  = 3;                       // vertical subdivisions on the wall

  // ---- analytic rim: 4 arcs + 4 straight runs, roughly even arc length ----
  const corners=[[hx-r, hz-r, 0],[-hx+r, hz-r, Math.PI/2],
                 [-hx+r,-hz+r, Math.PI],[hx-r,-hz+r, Math.PI*1.5]];
  const arcN = Math.max(4, Math.round(rimSeg * (Math.PI/2*r) / (2*(BW+BD))));
  const runN = Math.max(4, Math.round(rimSeg * (BW-2*r) / (2*(BW+BD))));
  const rim=[];
  function arc(cx,cz,a0,n){ for(let i=0;i<n;i++){ const a=a0+(i/n)*(Math.PI/2); rim.push([cx+r*Math.cos(a), cz+r*Math.sin(a)]); } }
  function run(x0,z0,x1,z1,n){ for(let i=0;i<n;i++){ const t=i/n; rim.push([x0+(x1-x0)*t, z0+(z1-z0)*t]); } }
  // walk the perimeter anticlockwise: +x run, then corner arcs and runs in order
  arc(corners[0][0], corners[0][1], corners[0][2], arcN);                 // (hx-r, hz-r) 0->90
  run(-hx+r, hz, hx-r, hz, runN);                                        // top edge
  arc(corners[1][0], corners[1][1], corners[1][2], arcN);                // (-hx+r, hz-r) 90->180
  run(-hx, -hz+r, -hx, hz-r, runN);                                      // left edge
  arc(corners[2][0], corners[2][1], corners[2][2], arcN);                // 180->270
  run(-hx+r, -hz, hx-r, -hz, runN);                                      // bottom edge
  arc(corners[3][0], corners[3][1], corners[3][2], arcN);                // 270->360
  run(hx, -hz+r, hx, hz-r, runN);                                        // right edge
  const N = rim.length;

  const pos=[], nrm=[], uv=[], side=[], idx=[];
  const U = x => (x+BW/2)/BW, V = z => (z+BD/2)/BD;

  // ---- top face: polar grid ----
  const base = pos.length/3;
  for (let k=0;k<=rings;k++){
    const t = k/rings;
    for (let i=0;i<N;i++){
      const x = rim[i][0]*t, z = rim[i][1]*t;
      pos.push(x, 0, z); nrm.push(0,1,0); uv.push(U(x), V(z)); side.push(0);
    }
  }
  const centre = pos.length/3;
  pos.push(0,0,0); nrm.push(0,1,0); uv.push(U(0), V(0)); side.push(0);
  for (let k=0;k<rings;k++){
    const a0 = base + k*N, a1 = base + (k+1)*N;
    for (let i=0;i<N;i++){
      const j=(i+1)%N;
      if (k === 0){ idx.push(centre, a1+i, a1+j); }
      else { idx.push(a0+i, a1+i, a1+j, a0+i, a1+j, a0+j); }
    }
  }
  // ---- underside: coarse fan ----
  const botBase = pos.length/3;
  for (let i=0;i<N;i++){ pos.push(rim[i][0],-BT,rim[i][1]); nrm.push(0,-1,0); uv.push(0,0); side.push(2); }
  const botC = pos.length/3;
  pos.push(0,-BT,0); nrm.push(0,-1,0); uv.push(0,0); side.push(2);
  for (let i=0;i<N;i++){ const j=(i+1)%N; idx.push(botC, botBase+j, botBase+i); }
  // ---- walls, subdivided vertically so the edge-light gradient is smooth ----
  for (let i=0;i<N;i++){
    const j=(i+1)%N;
    const x0=rim[i][0], z0=rim[i][1], x1=rim[j][0], z1=rim[j][1];
    let nx=z1-z0, nz=-(x1-x0); const l=Math.hypot(nx,nz)||1; nx/=l; nz/=l;
    for (let v=0;v<sideV;v++){
      const ya = -BT*(v/sideV), yb = -BT*((v+1)/sideV);
      const a = pos.length/3;
      pos.push(x0,ya,z0, x1,ya,z1, x1,yb,z1, x0,yb,z0);
      for (let q=0;q<4;q++) nrm.push(nx,0,nz);
      uv.push(0,1, 1,1, 1,0, 0,0);
      for (let q=0;q<4;q++) side.push(1);
      idx.push(a,a+1,a+2, a,a+2,a+3);
    }
  }
  return { pos:new Float32Array(pos), nrm:new Float32Array(nrm), uv:new Float32Array(uv),
           side:new Float32Array(side), idx:new Uint32Array(idx) };
}
function quad2d(){
  return { pos:new Float32Array([-1,-1, 3,-1, -1,3]) };
}


/* ------------------------------------------------------- instance groups -- */
function newGroup(){ return { iA:[], iB:[], iC:[], iD:[], n:0 }; }
const G = { box:newGroup(), cyl:newGroup() };
let seed = 0;
function push(shape, cx, cy, cz, hx, hy, hz, col, opt){
  opt = opt || {};
  const g = shape > 0.5 ? G.cyl : G.box;
  g.iA.push(cx, cy, cz, (seed++ * 0.6180339887) % 1);
  g.iB.push(hx, hy, hz, opt.rot || 0);
  const lc = col.__lin || (col.__lin = srgbLinRaw(col));
  g.iC.push(lc[0], lc[1], lc[2], shape);
  g.iD.push(opt.emissive || 0,
             opt.ao === undefined ? 0.42 : opt.ao,
             opt.detail === undefined ? 0.5 : opt.detail,
             opt.pulse ? 1 : 0);
  g.n++;
}
const box = (cx,cy,cz,hx,hy,hz,c,o) => push(0, cx,cy,cz, hx,hy,hz, c,o);
const cyl = (cx,cy,cz,r,h,c,o)      => push(1, cx,cy,cz, r,h,r, c,o);
function srgbLinRaw(c){
  const f = v => v <= 0.04045 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
  return [f(c[0]), f(c[1]), f(c[2])];
}
const A0 = srgbLinRaw([.84,.70,.34]);              // ENIG gold
const AL = srgbLinRaw([.62,.65,.68]);              // brushed aluminium

function buildInstances(){
  for (const p of P){
    const x=p.x, z=p.z, hx=p.hx, hz=p.hz, h=p.h, k=p.k, cy=h/2;
    const c = p.lc || (p.lc = srgbLinRaw(p.c));
    switch (k){
      case 'can':
        cyl(x, cy, z, Math.min(hx,hz), h/2, c, {detail:.85, ao:.50});
        cyl(x, 0.0009, z, Math.min(hx,hz)+0.005, 0.0009, srgbLinRaw([.30,.32,.34]), {detail:0, ao:0});
        break;
      case 'terminal':
        box(x, cy, z, hx, h/2, hz, c, {detail:.35, ao:.55});
        for (let i=-1;i<2;i++)
          cyl(x, h+0.0016, z+i*0.052, 0.0115, 0.0016, A0, {detail:.9, ao:.2});
        break;
      case 'module':
        box(x, cy, z, hx, h/2, hz, c, {detail:.30, ao:.60});
        box(x, h+0.0020, z-hz*0.14, hx*0.88, 0.0020, hz*0.66, AL, {detail:.95, ao:.30});
        box(x, h+0.0022, z+hz*0.78, hx*0.80, 0.0022, hz*0.15, srgbLinRaw([.80,.78,.72]), {detail:.20, ao:.30});
        for (let i=-4;i<=4;i++){
          box(x+i*hx*0.20, h+0.0010, -hz*1.01, hx*0.070, 0.0010, hz*0.032, A0, {detail:.6, ao:.2});
          box(x+i*hx*0.20, h+0.0010,  hz*1.01, hx*0.070, 0.0010, hz*0.032, A0, {detail:.6, ao:.2});
        }
        break;
      case 'relay':
        box(x, cy, z, hx, h/2, hz, c, {detail:.30, ao:.58});
        box(x, h+0.0016, z, hx*0.86, 0.0016, hz*0.86,
            srgbLinRaw([Math.min(1,c[0]*1.3), Math.min(1,c[1]*1.3), Math.min(1,c[2]*1.3)]), {detail:.75, ao:.30});
        break;
      case 'ind':
        box(x, cy, z, hx, h/2, hz, c, {detail:.30, ao:.55});
        for (const f of [-0.5, 0, 0.5])
          box(x, h+0.0014, z+f*hz*1.10, hx*0.78, 0.0014, hz*0.075, srgbLinRaw([.72,.74,.76]), {detail:.95, ao:.2});
        break;
      case 'usb':
        box(x, cy, z, hx, h/2, hz, c, {detail:.85, ao:.50});
        box(x, cy, z+hz*0.92, hx*0.70, h/2*0.52, hz*0.20, srgbLinRaw([.09,.10,.11]), {detail:.1, ao:.3});
        break;
      case 'led':
        box(x, cy, z, hx, h/2, hz, c, {detail:.90, ao:.35, emissive:0.55, pulse:true});
        break;
      case 'fuse':
        box(x, cy, z, hx, h/2, hz, c, {detail:.50, ao:.50});
        box(x, h+0.0010, z, hx*0.90, 0.0010, hz*0.50, c, {detail:.60, ao:.30});
        break;
      case 'header':
        box(x, cy, z, hx, h/2, hz, c, {detail:.40, ao:.60});
        for (let i=-3;i<=3;i++)
          box(x+i*hx*0.28, h+0.0012, z, hx*0.060, 0.0012, hz*0.50, A0, {detail:.9, ao:.2});
        break;
      case 'dpak':
        box(x, cy, z, hx, h/2, hz, c, {detail:.35, ao:.50});
        box(x, h+0.0012, z-hz*0.55, hx*0.95, 0.0012, hz*0.30, AL, {detail:.9, ao:.25});
        break;
      case 'pad':
        cyl(x, 0.0007, z, hx, 0.0007, A0, {detail:.9, ao:.15});
        break;
      default:
        box(x, cy, z, hx, h/2, hz, c, {detail:.45, ao:.45});
        for (const sgn of [-1,1])
          box(x+sgn*hx*1.14, 0.0011, z, hx*0.16, 0.0011, hz*1.02, A0, {detail:.85, ao:.2});
        break;
    }
  }
  const out = {};
  for (const key of ['box','cyl']){
    const g = G[key];
    out[key] = { n:g.n,
      iA:new Float32Array(g.iA), iB:new Float32Array(g.iB),
      iC:new Float32Array(g.iC), iD:new Float32Array(g.iD) };
  }
  return out;
}

function buildMotes(count){
  const a = new Float32Array(count*4), b = new Float32Array(count*4);
  for (let i=0;i<count;i++){
    const r = 0.22 + Math.random()*1.15, t = Math.random()*Math.PI*2;
    a[i*4  ] = Math.cos(t)*r*1.30;
    a[i*4+1] = FLOOR_Y + 0.03 + Math.random()*0.92;
    a[i*4+2] = Math.sin(t)*r;
    a[i*4+3] = Math.random();
    b[i*4  ] = 0.0020 + Math.random()*0.0060;
    b[i*4+1] = 0.40 + Math.random()*1.20;
    b[i*4+2] = Math.random()*0.90;
    b[i*4+3] = Math.random();
  }
  return { a, b, count };
}

const SH = {
slabVert:"#version 300 es\nprecision highp float;\nin vec3 aPos;\nin vec3 aNrm;\nin vec2 aUV;\nin float aSide;\nuniform mat4 uVP;\nuniform mat4 uModel;\nout vec3 vN;\nout vec3 vW;\nout vec2 vUV;\nout float vSide;\nout vec3 vLocal;\nvoid main(){\n  vec4 w = uModel * vec4(aPos, 1.0);\n  vW = w.xyz;\n  vN = mat3(uModel) * aNrm;\n  vUV = aUV;\n  vSide = aSide;\n  vLocal = aPos;\n  gl_Position = uVP * w;\n}\n",
slabFrag:"#version 300 es\nprecision highp float;\nin vec3 vN; in vec3 vW; in vec2 vUV; in float vSide; in vec3 vLocal;\nuniform sampler2D uAtlas;\nuniform vec2 uAtlasScale;\nuniform vec3 uCamPos;\nuniform vec3 uKeyDir; uniform vec3 uKeyCol;\nuniform vec3 uFillDir; uniform vec3 uFillCol;\nuniform vec3 uRimCol;\nuniform float uTime;\nout vec4 outColor;\nfloat fres(float nv){ return pow(1.0 - clamp(nv,0.0,1.0), 3.0); }\nvoid main(){\n  vec3 N = normalize(vN);\n  vec3 V = normalize(uCamPos - vW);\n  float nv = max(dot(N, V), 0.0);\n  vec3 base;\n  float gloss = 0.35;\n  if (vSide < 0.5) {\n    base = texture(uAtlas, vUV * uAtlasScale).rgb;\n    gloss = 0.85;\n  } else if (vSide < 1.5) {\n    float band = smoothstep(-1.0, 1.0, vLocal.y);\n    base = mix(vec3(0.012,0.052,0.044), vec3(0.035,0.115,0.098), band);\n    base += vec3(1.0,0.72,0.34) * 0.10 * smoothstep(0.90, 1.0, vLocal.y);\n    gloss = 0.30;\n  } else {\n    base = vec3(0.015,0.022,0.026);\n    gloss = 0.12;\n  }\n  float kd = max(dot(N, uKeyDir), 0.0);\n  float fd = max(dot(N, uFillDir), 0.0);\n  vec3 col = base * (uKeyCol * kd * 1.25 + uFillCol * fd * 0.85 + vec3(0.075,0.085,0.095));\n  vec3 H = normalize(uKeyDir + V);\n  col += uKeyCol * pow(max(dot(N,H), 0.0), 42.0) * gloss;\n  col += uRimCol * fres(nv) * (vSide < 0.5 ? 0.85 : 1.35);\n  outColor = vec4(col, 1.0);\n}\n",
instVert:"#version 300 es\nprecision highp float;\nin vec3 aPos;\nin vec3 aNrm;\nin vec4 iA;   // centre.xyz, seed\nin vec4 iB;   // half.xyz, rotY\nin vec4 iC;   // colour.rgb, shape (0 box / 1 cyl)\nin vec4 iD;   // emissive, aoStrength, topDetail, pulse\nuniform mat4 uVP;\nuniform mat4 uModel;\nuniform float uTime;\nout vec3 vN; out vec3 vW; out vec3 vCol; out float vEmis;\nout vec3 vLocal; out float vAo; out float vDetail; out float vTop;\nvoid main(){\n  vec3 hp = iB.xyz;\n  vec3 lp;\n  if (iC.w > 0.5) {\n    lp = vec3(aPos.x * hp.x, aPos.y * hp.y, aPos.z * hp.x);\n  } else {\n    lp = aPos * hp;\n  }\n  float r = iB.w;\n  float c = cos(r), s = sin(r);\n  vec3 rp = vec3(lp.x*c - lp.z*s, lp.y, lp.x*s + lp.z*c);\n  vec3 rn = vec3(aNrm.x*c - aNrm.z*s, aNrm.y, aNrm.x*s + aNrm.z*c);\n  vec3 local = rp + iA.xyz;\n  vec4 w = uModel * vec4(local, 1.0);\n  vW = w.xyz;\n  vN = mat3(uModel) * rn;\n  vCol = iC.rgb;\n  vEmis = iD.x;\n  vAo = iD.y;\n  vDetail = iD.z;\n  vLocal = aPos;\n  vTop = step(0.5, aNrm.y);\n  float pulse = iD.w > 0.5 ? (0.55 + 0.45*sin(uTime*2.6 + iA.w*6.283)) : 1.0;\n  vEmis *= pulse;\n  gl_Position = uVP * w;\n}\n",
instFrag:"#version 300 es\nprecision highp float;\nin vec3 vN; in vec3 vW; in vec3 vCol;\nin float vEmis; in vec3 vLocal; in float vAo; in float vDetail; in float vTop;\nuniform vec3 uCamPos;\nuniform vec3 uKeyDir; uniform vec3 uKeyCol;\nuniform vec3 uFillDir; uniform vec3 uFillCol;\nuniform vec3 uRimCol;\nuniform float uTime;\nout vec4 outColor;\nfloat hash12(vec2 p){\n  vec3 p3 = fract(vec3(p.xyx)*0.1031);\n  p3 += dot(p3, p3.yzx+33.33);\n  return fract((p3.x+p3.y)*p3.z);\n}\n\nfloat fres(float nv){ return pow(1.0 - clamp(nv,0.0,1.0), 3.0); }\nvoid main(){\n  vec3 N = normalize(vN);\n  vec3 V = normalize(uCamPos - vW);\n  float nv = max(dot(N,V), 0.0);\n  vec3 base = vCol;\n  // top-face micro detail: brushed metal / moulded plastic / printed lid\n  if (vTop > 0.5 && vDetail > 0.5) {\n    float seam = smoothstep(0.86, 0.99, max(abs(vLocal.x), abs(vLocal.z)));\n    base *= mix(0.72, 1.06, seam);\n    base *= 0.94 + 0.06 * hash12(floor(vLocal.xz * 26.0));\n  }\n  float kd = max(dot(N, uKeyDir), 0.0);\n  float fd = max(dot(N, uFillDir), 0.0);\n  vec3 col = base * (uKeyCol * kd * 1.30 + uFillCol * fd * 0.80 + vec3(0.10,0.11,0.12));\n  vec3 H = normalize(uKeyDir + V);\n  float spec = pow(max(dot(N,H), 0.0), mix(28.0, 90.0, vDetail));\n  col += uKeyCol * spec * mix(0.20, 0.55, vDetail);\n  col += uRimCol * fres(nv) * 0.95;\n  // contact darkening at the base\n  float ao = 1.0 - vAo * (1.0 - smoothstep(-1.0, -0.15, vLocal.y));\n  col *= ao;\n  col += vCol * vEmis;\n  outColor = vec4(col, 1.0);\n}\n",
floorVert:"#version 300 es\nprecision highp float;\nin vec2 aXZ;\nuniform mat4 uVP;\nuniform float uFloorY;\nout vec3 vW;\nvoid main(){\n  vec3 p = vec3(aXZ.x, uFloorY, aXZ.y);\n  vW = p;\n  gl_Position = uVP * vec4(p, 1.0);\n}\n",
floorFrag:"#version 300 es\nprecision highp float;\nin vec3 vW;\nuniform vec3 uCamPos;\nuniform vec3 uTintA;\nuniform vec3 uTintB;\nuniform float uTime;\nuniform vec2 uBoardHalf;\nout vec4 outColor;\nfloat gridLine(vec2 p, float w){\n  vec2 g = abs(fract(p - 0.5) - 0.5) / max(fwidth(p), vec2(1e-5));\n  float l = min(g.x, g.y);\n  return 1.0 - min(l, 1.0);\n}\nvoid main(){\n  vec2 p = vW.xz;\n  float d = length(p - uCamPos.xz * 0.0);\n  float major = gridLine(p * 8.0, 1.0);\n  float minor = gridLine(p * 32.0, 1.0) * 0.34;\n  float g = max(major, minor);\n  // plasma sweep that drifts outward \u2014 the \"energised bench\" motif\n  float r = length(p);\n  float sweep = sin(r * 11.0 - uTime * 1.15);\n  sweep = smoothstep(0.90, 1.0, sweep);\n  float radial = smoothstep(1.55, 0.15, r);\n  float under = smoothstep(1.30, 0.0, length((p) / (uBoardHalf * 1.35)));\n  vec3 col = mix(uTintB, uTintA, g);\n  col += uTintA * sweep * 0.55 * radial;\n  col += uTintA * under * 0.28;\n  float a = (g * 0.34 + sweep * 0.22 + under * 0.16) * radial;\n  outColor = vec4(col * a, a);\n}\n",
moteVert:"#version 300 es\nprecision highp float;\nin vec4 iA;      // pos.xyz, seed\nin vec4 iB;      // size, speed, tint, life\nuniform mat4 uVP;\nuniform float uTime;\nuniform float uPointScale;\nout float vFade;\nout vec3 vTint;\nvoid main(){\n  float seed = iA.w;\n  float t = fract(iB.w + uTime * iB.y * 0.055);\n  vec3 c = iA.xyz;\n  c.y += t * 0.52;\n  c.x += sin(uTime * 0.31 + seed * 6.283) * 0.030;\n  c.z += cos(uTime * 0.26 + seed * 5.114) * 0.030;\n  vec4 clip = uVP * vec4(c, 1.0);\n  gl_Position = clip;\n  gl_PointSize = clamp(iB.x * uPointScale / max(clip.w, 0.05), 1.0, 26.0);\n  vFade = (1.0 - t) * smoothstep(0.0, 0.22, t) * (0.18 + 0.82 * iB.z);\n  vTint = mix(vec3(0.30,0.95,0.88), vec3(1.0,0.72,0.30), step(0.74, seed));\n}\n",
moteFrag:"#version 300 es\nprecision highp float;\nin float vFade;\nin vec3 vTint;\nout vec4 outColor;\nvoid main(){\n  vec2 q = gl_PointCoord * 2.0 - 1.0;\n  float d = 1.0 - smoothstep(0.10, 1.0, length(q));\n  outColor = vec4(vTint * d * vFade, d * vFade);\n}\n",
postVert:"#version 300 es\nprecision highp float;\nin vec2 aPos;\nout vec2 vUV;\nvoid main(){\n  vUV = aPos * 0.5 + 0.5;\n  gl_Position = vec4(aPos, 0.0, 1.0);\n}\n",
brightFrag:"#version 300 es\nprecision highp float;\nin vec2 vUV;\nuniform sampler2D uScene;\nuniform float uThreshold;\nout vec4 outColor;\nvoid main(){\n  vec3 c = texture(uScene, vUV).rgb;\n  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));\n  float k = max(l - uThreshold, 0.0) / max(l, 1e-4);\n  outColor = vec4(c * k, 1.0);\n}\n",
blurFrag:"#version 300 es\nprecision highp float;\nin vec2 vUV;\nuniform sampler2D uSrc;\nuniform vec2 uDir;          // texel-sized direction\nout vec4 outColor;\nvoid main(){\n  float w[5];\n  w[0]=0.227027; w[1]=0.194594; w[2]=0.121621; w[3]=0.054054; w[4]=0.016216;\n  vec3 sum = texture(uSrc, vUV).rgb * w[0];\n  for (int i = 1; i < 5; i++){\n    vec2 o = uDir * float(i) * 1.35;\n    sum += texture(uSrc, vUV + o).rgb * w[i];\n    sum += texture(uSrc, vUV - o).rgb * w[i];\n  }\n  outColor = vec4(sum, 1.0);\n}\n",
compFrag:"#version 300 es\nprecision highp float;\nin vec2 vUV;\nuniform sampler2D uScene;\nuniform sampler2D uBloom;\nuniform float uBloomAmt;\nuniform float uExposure;\nuniform float uTime;\nuniform float uVignette;\nuniform float uGrain;\nuniform vec2 uRes;\nout vec4 outColor;\nvec3 aces(vec3 x){\n  const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14;\n  return clamp((x*(a*x+b))/(x*(c*x+d)+e), 0.0, 1.0);\n}\nfloat hash12(vec2 p){\n  vec3 p3 = fract(vec3(p.xyx)*0.1031);\n  p3 += dot(p3, p3.yzx+33.33);\n  return fract((p3.x+p3.y)*p3.z);\n}\nvoid main(){\n  vec2 d = vUV - 0.5;\n  float r2 = dot(d,d);\n  // chromatic aberration, zero at centre\n  vec2 ca = d * r2 * 0.0075;\n  vec3 col;\n  col.r = texture(uScene, vUV + ca).r;\n  col.g = texture(uScene, vUV).g;\n  col.b = texture(uScene, vUV - ca).b;\n  col += texture(uBloom, vUV).rgb * uBloomAmt;\n  col *= uExposure;\n  col = aces(col);\n  col *= 1.0 - uVignette * smoothstep(0.18, 0.86, r2 * 1.9);\n  col += (hash12(vUV * uRes + uTime) - 0.5) * uGrain;\n  outColor = vec4(col, 1.0);\n}\n"
};


/* ============================== the renderer ============================== */
function beamExtent(aspect, az, el, fov, target, pts, d){
  const a = az*D2R, e = el*D2R;
  const eye = [Math.cos(e)*Math.sin(a)*d + target[0],
               Math.sin(e)*d + target[1],
               Math.cos(e)*Math.cos(a)*d + target[2]];
  const view = m4lookAt(eye, target, [0,1,0]);
  const proj = m4persp(fov*D2R, aspect, 0.05, 30);
  const vp = m4mul(proj, view);
  let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
  for (const p of pts){
    const cx = vp[0]*p[0]+vp[4]*p[1]+vp[8]*p[2]+vp[12];
    const cy = vp[1]*p[0]+vp[5]*p[1]+vp[9]*p[2]+vp[13];
    const cw = vp[3]*p[0]+vp[7]*p[1]+vp[11]*p[2]+vp[15];
    const w = cw || 1e-6;
    x0=Math.min(x0,cx/w); x1=Math.max(x1,cx/w);
    y0=Math.min(y0,cy/w); y1=Math.max(y1,cy/w);
  }
  return { w:(x1-x0)/2, h:(y1-y0)/2 };
}
function solveDistance(aspect, az, el, fov, target, pts, fill){
    let lo = 0.7, hi = 7.0;
  for (let i=0;i<26;i++){
    const mid = (lo+hi)/2, c = beamExtent(aspect, az, el, fov, target, pts, mid);
    if (c.w > fill.w || c.h > fill.h) lo = mid; else hi = mid;
  }
  return hi;
}

const CAM = { az:-19, el:34, fov:34, target:[0.010,0.034,0] };
const FILL = { w:0.82, h:0.90 };

export function boot(canvas, opts){
  opts = opts || {};
  const gl = canvas.getContext('webgl2', {
    alpha:false, antialias:true, depth:true, stencil:false,
    premultipliedAlpha:false, preserveDrawingBuffer:false,
    powerPreference:'high-performance', failIfMajorPerformanceCaveat:false
  });
  if (!gl) return { ok:false, reason:'no-webgl2' };

  let half = null;
  if (gl.getExtension('EXT_color_buffer_half_float')) half = gl.RGBA16F;
  if (!half && gl.getExtension('EXT_color_buffer_float')) half = gl.RGBA16F;
  const HDR = !!half;
  const sceneFmt = HDR ? gl.RGBA16F : gl.RGBA8;
  const sceneType = HDR ? gl.HALF_FLOAT : gl.UNSIGNED_BYTE;

  let P_slab, P_inst, P_floor, P_mote, P_bright, P_blur, P_comp;
  try {
    P_slab   = program(gl, SH.slabVert,   SH.slabFrag,   'slab');
    P_inst   = program(gl, SH.instVert,   SH.instFrag,   'inst');
    P_floor  = program(gl, SH.floorVert,  SH.floorFrag,  'floor');
    P_mote   = program(gl, SH.moteVert,   SH.moteFrag,   'mote');
    P_bright = program(gl, SH.postVert,   SH.brightFrag, 'bright');
    P_blur   = program(gl, SH.postVert,   SH.blurFrag,   'blur');
    P_comp   = program(gl, SH.postVert,   SH.compFrag,   'comp');
  } catch (e) {
    return { ok:false, reason:'shader', error:String(e && e.message || e) };
  }

  /* ---------------------------------------------------------- geometry --- */
  const gSlab = slab();
  const sPos = vbo(gl, gSlab.pos), sNrm = vbo(gl, gSlab.nrm),
        sUV  = vbo(gl, gSlab.uv),  sSid = vbo(gl, gSlab.side);
  const sIdx = vbo(gl, gSlab.idx, gl.ELEMENT_ARRAY_BUFFER);
  const gCube = cube(), gCyl = cylinder();
  const bPos = vbo(gl, gCube.pos), bNrm = vbo(gl, gCube.nrm);
  const cPos = vbo(gl, gCyl.pos),  cNrm = vbo(gl, gCyl.nrm);
  const inst = buildInstances();
  const iBufs = {};
  for (const k of ['box','cyl']){
    iBufs[k] = {
      A: vbo(gl, inst[k].iA), B: vbo(gl, inst[k].iB),
      C: vbo(gl, inst[k].iC), D: vbo(gl, inst[k].iD), n: inst[k].n
    };
  }
  const fQuad = vbo(gl, quad2d().pos);
  const motes = buildMotes(opts.motes || 150);
  const mBufA = vbo(gl, motes.a), mBufB = vbo(gl, motes.b);

  /* ------------------------------------------------------------ atlas ---- */
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.SRGB8_ALPHA8, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
                new Uint8Array([10,44,38,255]));
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  const aniso = gl.getExtension('EXT_texture_filter_anisotropic');
  let atlasReady = false;
  const img = new Image();
  img.decoding = 'async';
  img.onload = () => {
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.SRGB8_ALPHA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    if (aniso){
      const mx = gl.getParameter(aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT);
      gl.texParameterf(gl.TEXTURE_2D, aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, mx));
    }
    atlasReady = true;
  };
  img.src = opts.atlas || 'assets/hero-atlas.webp';

  /* -------------------------------------------------------------- FBOs --- */
  function makeTarget(w, h, withDepth){
    const t = { w, h, fbo:gl.createFramebuffer(), tex:gl.createTexture(), depth:null };
    gl.bindTexture(gl.TEXTURE_2D, t.tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, sceneFmt, w, h, 0, gl.RGBA, sceneType, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.bindFramebuffer(gl.FRAMEBUFFER, t.fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t.tex, 0);
    if (withDepth){
      t.depth = gl.createRenderbuffer();
      gl.bindRenderbuffer(gl.RENDERBUFFER, t.depth);
      gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT24, w, h);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, t.depth);
    }
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return ok ? t : null;
  }

  /* --------------------------------------------------------- view state -- */
  let dpr = Math.min(window.devicePixelRatio || 1, 1.6);
  const BASE = dpr;
  let scale = 1.0;
  let W = 1, H = 1, aspect = 1, dist = 2.4;
  let sceneT = null, bloomA = null, bloomB = null;
  let alive = true, visible = true, ready = false;
  let frames = 0, slow = 0, quality = 2;

  const framePts = [];
  for (const sx of [-1,1]) for (const sz of [-1,1]) framePts.push([sx*BW/2, 0, sz*BD/2]);
  for (const p of P) framePts.push([p.x, p.h, p.z]);


  function resize(){
    const r = canvas.getBoundingClientRect();
    const cw = Math.max(1, Math.round(r.width));
    const ch = Math.max(1, Math.round(r.height));
    const dw = Math.max(1, Math.round(cw * dpr * scale));
    const dh = Math.max(1, Math.round(ch * dpr * scale));
    W = dw; H = dh; aspect = cw / ch;
    canvas.width = dw; canvas.height = dh;
    dist = solveDistance();
    dist = solveDistance(aspect, CAM.az, CAM.el, CAM.fov, CAM.target, framePts, FILL);
    if (sceneT){ gl.deleteTexture(sceneT.tex); gl.deleteFramebuffer(sceneT.fbo);
                 if (sceneT.depth) gl.deleteRenderbuffer(sceneT.depth); }
    if (bloomA){ gl.deleteTexture(bloomA.tex); gl.deleteFramebuffer(bloomA.fbo); }
    if (bloomB){ gl.deleteTexture(bloomB.tex); gl.deleteFramebuffer(bloomB.fbo); }
    sceneT = makeTarget(W, H, true);
    const bw = Math.max(2, W >> 1), bh = Math.max(2, H >> 1);
    bloomA = makeTarget(bw, bh, false);
    bloomB = makeTarget(bw, bh, false);
  }

  /* -------------------------------------------------------- projection --- */
  const proj = new Float32Array(16), view = new Float32Array(16),
        vp = new Float32Array(16), model = new Float32Array(16);
  const eye = [0,0,0];
  let px = 0, py = 0, tx = 0, ty = 0, dragYaw = 0, dragPitch = 0, vy = 0, vpitch = 0;
  let t0 = performance.now() / 1000, elapsed = 0;

  function updateCamera(dt){
    tx += (px - tx) * Math.min(1, dt*4.2);
    ty += (py - ty) * Math.min(1, dt*4.2);
    if (!dragging){
      dragYaw *= 1 - Math.min(1, dt*1.5);
      dragPitch *= 1 - Math.min(1, dt*1.5);
    }
    const idle = Math.sin(elapsed*0.105);
    const az = (CAM.az + idle*2.8 - tx*9.5 + dragYaw) * D2R;
    const el = (CAM.el + Math.sin(elapsed*0.082)*1.5 + ty*6.0 + dragPitch) * D2R;
    const float = Math.sin(elapsed*0.42)*0.016;
    eye[0] = Math.cos(el)*Math.sin(az)*dist + CAM.target[0];
    eye[1] = Math.sin(el)*dist + CAM.target[1] + float;
    eye[2] = Math.cos(el)*Math.cos(az)*dist + CAM.target[2];
    m4lookAt(eye, CAM.target, [0,1,0], view);
    m4persp(CAM.fov*D2R, aspect, 0.05, 30, proj);
    m4mul(proj, view, vp);
  }

  /* ------------------------------------------------------------ passes --- */
  function bindMesh(posBuf, nrmBuf){
    attrib(gl, P_inst.a.aPos, posBuf, 3);
    attrib(gl, P_inst.a.aNrm, nrmBuf, 3);
  }
  function bindInst(k, prog){
    attrib(gl, prog.a.iA, iBufs[k].A, 4, 1);
    attrib(gl, prog.a.iB, iBufs[k].B, 4, 1);
    attrib(gl, prog.a.iC, iBufs[k].C, 4, 1);
    attrib(gl, prog.a.iD, iBufs[k].D, 4, 1);
  }
  function fullscreen(prog){
    const sp = 'aPos' in prog.a ? prog.a.aPos : prog.a.aXZ;
    attrib(gl, sp, fQuad, 2);
  }

  const KEY  = [ 0.42, 0.72, 0.45], KCOL = [1.00, 0.97, 0.92];
  const FILLD= [-0.55, 0.35,-0.62], FCOL = [0.16, 0.42, 0.48];
  const RIM  = [0.10, 0.42, 0.40];
  const KL = Math.hypot(KEY[0],KEY[1],KEY[2]);
  const FL = Math.hypot(FILLD[0],FILLD[1],FILLD[2]);
  const keyN = [KEY[0]/KL, KEY[1]/KL, KEY[2]/KL];
  const fillN= [FILLD[0]/FL, FILLD[1]/FL, FILLD[2]/FL];

  function drawScene(){
    gl.bindFramebuffer(gl.FRAMEBUFFER, sceneT.fbo);
    gl.viewport(0, 0, W, H);
    gl.clearColor(0.010, 0.016, 0.021, 1);
    gl.clearDepth(1);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
    gl.disable(gl.BLEND);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    m4trs(0, 0, 0, 0, 0, model);

    /* --- PCB slab --- */
    gl.useProgram(P_slab.p);
    gl.uniformMatrix4fv(P_slab.u.uVP, false, vp);
    gl.uniformMatrix4fv(P_slab.u.uModel, false, model);
    gl.uniform3fv(P_slab.u.uCamPos, eye);
    gl.uniform3fv(P_slab.u.uKeyDir, keyN);
    gl.uniform3fv(P_slab.u.uKeyCol, KCOL);
    gl.uniform3fv(P_slab.u.uFillDir, fillN);
    gl.uniform3fv(P_slab.u.uFillCol, FCOL);
    gl.uniform3fv(P_slab.u.uRimCol, RIM);
    gl.uniform2f(P_slab.u.uAtlasScale, 1.0, 1.0);
    gl.uniform1f(P_slab.u.uTime, elapsed);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.uniform1i(P_slab.u.uAtlas, 0);
    attrib(gl, P_slab.a.aPos, sPos, 3);
    attrib(gl, P_slab.a.aNrm, sNrm, 3);
    attrib(gl, P_slab.a.aUV,  sUV,  2);
    attrib(gl, P_slab.a.aSide,sSid, 1);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, sIdx);
    gl.drawElements(gl.TRIANGLES, gSlab.idx.length, gl.UNSIGNED_INT, 0);

    /* --- components --- */
    gl.useProgram(P_inst.p);
    gl.uniformMatrix4fv(P_inst.u.uVP, false, vp);
    gl.uniformMatrix4fv(P_inst.u.uModel, false, model);
    gl.uniform3fv(P_inst.u.uCamPos, eye);
    gl.uniform3fv(P_inst.u.uKeyDir, keyN);
    gl.uniform3fv(P_inst.u.uKeyCol, KCOL);
    gl.uniform3fv(P_inst.u.uFillDir, fillN);
    gl.uniform3fv(P_inst.u.uFillCol, FCOL);
    gl.uniform3fv(P_inst.u.uRimCol, RIM);
    gl.uniform1f(P_inst.u.uTime, elapsed);
    for (const k of ['box','cyl']){
      if (!iBufs[k].n) continue;
      bindMesh(k === 'box' ? bPos : cPos, k === 'box' ? bNrm : cNrm);
      bindInst(k, P_inst);
      gl.drawArraysInstanced(gl.TRIANGLES, 0, k === 'box' ? gCube.count : gCyl.count, iBufs[k].n);
    }
    for (const k of ['box','cyl'])
      for (const a of ['iA','iB','iC','iD']) gl.vertexAttribDivisor(P_inst.a[a], 0);

    /* --- bench grid --- */
    gl.useProgram(P_floor.p);
    gl.uniformMatrix4fv(P_floor.u.uVP, false, vp);
    gl.uniform1f(P_floor.u.uFloorY, FLOOR_Y);
    gl.uniform3fv(P_floor.u.uCamPos, eye);
    gl.uniform3fv(P_floor.u.uTintA, [0.36, 0.95, 0.88]);
    gl.uniform3fv(P_floor.u.uTintB, [0.05, 0.16, 0.15]);
    gl.uniform1f(P_floor.u.uTime, elapsed);
    gl.uniform2f(P_floor.u.uBoardHalf, BW/2, BD/2);
    attrib(gl, P_floor.a.aXZ, fQuad, 2);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, null);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.depthMask(false);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.depthMask(true);

    /* --- dust motes --- */
    gl.useProgram(P_mote.p);
    gl.uniformMatrix4fv(P_mote.u.uVP, false, vp);
    gl.uniform1f(P_mote.u.uTime, elapsed);
    gl.uniform1f(P_mote.u.uPointScale, H * 0.28);
    attrib(gl, P_mote.a.iA, mBufA, 4, 1);
    attrib(gl, P_mote.a.iB, mBufB, 4, 1);
    gl.drawArraysInstanced(gl.POINTS, 0, 1, motes.count);
    gl.vertexAttribDivisor(P_mote.a.iA, 0);
    gl.vertexAttribDivisor(P_mote.a.iB, 0);
    gl.disable(gl.BLEND);
    gl.disable(gl.DEPTH_TEST);
  }

  const taps = 1.35;
  function drawPost(){
    // bright pass -> bloomA
    gl.bindFramebuffer(gl.FRAMEBUFFER, bloomA.fbo);
    gl.viewport(0, 0, bloomA.w, bloomA.h);
    gl.useProgram(P_bright.p);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, sceneT.tex);
    gl.uniform1i(P_bright.u.uScene, 0);
    gl.uniform1f(P_bright.u.uThreshold, HDR ? 0.42 : 0.48);
    fullscreen(P_bright);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    // separable blur, quality-dependent iterations
    gl.useProgram(P_blur.p);
    gl.uniform2f(P_blur.u.uDir, taps / bloomA.w, 0);
    for (let i=0;i<quality;i++){
      gl.bindFramebuffer(gl.FRAMEBUFFER, bloomB.fbo);
      gl.viewport(0, 0, bloomB.w, bloomB.h);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, bloomA.tex);
      gl.uniform1i(P_blur.u.uSrc, 0);
      fullscreen(P_blur);
      gl.drawArrays(gl.TRIANGLES, 0, 3);

      gl.bindFramebuffer(gl.FRAMEBUFFER, bloomA.fbo);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, bloomB.tex);
      gl.uniform1i(P_blur.u.uSrc, 0);
      gl.uniform2f(P_blur.u.uDir, 0, taps / bloomA.h);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      gl.uniform2f(P_blur.u.uDir, taps / bloomA.w, 0);
    }

    // composite to the canvas
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, W, H);
    gl.useProgram(P_comp.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, sceneT.tex);
    gl.uniform1i(P_comp.u.uScene, 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, bloomA.tex);
    gl.uniform1i(P_comp.u.uBloom, 1);
    gl.uniform1f(P_comp.u.uBloomAmt, HDR ? 0.85 : 0.42);
    gl.uniform1f(P_comp.u.uExposure, HDR ? 0.66 : 0.58);
    gl.uniform1f(P_comp.u.uTime, elapsed);
    gl.uniform1f(P_comp.u.uVignette, 0.36);
    gl.uniform1f(P_comp.u.uGrain, 0.020);
    gl.uniform2f(P_comp.u.uRes, W, H);
    fullscreen(P_comp);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.activeTexture(gl.TEXTURE0);
  }

  /* ------------------------------------------------------------- loop ---- */
  let raf = 0, prev = 0, acc = 0, samples = 0, started = false;
  function tick(now){
    raf = requestAnimationFrame(tick);
    if (!alive || !visible || !sceneT) return;
    const t = now / 1000;
    let dt = prev ? Math.min(t - prev, 0.05) : 0.016;
    prev = t; elapsed = t - t0;
    updateCamera(dt);
    drawScene();
    drawPost();
    if (!ready){ ready = true; if (opts.onReady) opts.onReady(); }
    // frame-budget probe over the first ~2s, then settle
    if (frames < 120){
      frames++; acc += dt; samples++;
      if (!started && samples >= 30){
        started = true;
        const avg = acc / samples;
        if (avg > 0.030 && quality > 1){ quality = 1; dpr = Math.min(BASE, 1.15); }
        if (avg > 0.046){ scale = 0.78; dpr = Math.min(BASE, 1.0); }
        if (avg > 0.030 || avg > 0.046) resize();
        acc = 0; samples = 0; frames = 120;
      }
    }
  }

  /* ------------------------------------------------------------ events --- */
  let dragging = false, lastX = 0, lastY = 0;
  function onDown(e){
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    if (canvas.setPointerCapture) canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = 'grabbing';
  }
  function onMove(e){
    const r = canvas.getBoundingClientRect();
    px = ((e.clientX - r.left) / r.width) * 2 - 1;
    py = ((e.clientY - r.top) / r.height) * 2 - 1;
    if (dragging){
      dragYaw += (e.clientX - lastX) * 0.28;
      dragPitch = Math.max(-9, Math.min(9, dragPitch + (e.clientY - lastY) * -0.16));
      dragYaw = Math.max(-40, Math.min(40, dragYaw));
      lastX = e.clientX; lastY = e.clientY;
    }
  }
  function onUp(e){
    dragging = false;
    if (canvas.releasePointerCapture && e.pointerId !== undefined){
      try { canvas.releasePointerCapture(e.pointerId); } catch(_){}
    }
    canvas.style.cursor = 'grab';
  }
  function onLeave(){ dragging = false; px = 0; py = 0; }
  let resizeQueued = false;
  function onResize(){
    if (resizeQueued) return;
    resizeQueued = true;
    requestAnimationFrame(() => { resizeQueued = false; if (sceneT) resize(); });
  }
  function onVis(){ visible = !document.hidden; }
  function onLost(e){ e.preventDefault(); alive = false; cancelAnimationFrame(raf); }
  function onRestored(){ if (alive) { prev = 0; } }
  function onEnter(){ visible = true; }
  function onExit(){ visible = false; }

  const fine = matchMedia('(hover:hover) and (pointer:fine)').matches;
  if (fine){
    canvas.addEventListener('pointermove', onMove, {passive:true});
    canvas.addEventListener('pointerleave', onLeave, {passive:true});
    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointercancel', onUp);
  }
  window.addEventListener('resize', onResize, {passive:true});
  document.addEventListener('visibilitychange', onVis);
  canvas.addEventListener('webglcontextlost', onLost, false);
  canvas.addEventListener('webglcontextrestored', onRestored, false);
  canvas.style.cursor = fine ? 'grab' : 'default';
  canvas.style.touchAction = 'pan-y';
  const io = 'IntersectionObserver' in window
    ? new IntersectionObserver(es => es.forEach(e => e.isIntersecting ? onEnter() : onExit()),
                               {rootMargin:'120px 0px'})
    : null;
  if (io) io.observe(canvas); else onEnter();

  resize();
  t0 = performance.now() / 1000; prev = 0;
  raf = requestAnimationFrame(tick);

  return {
    ok:true,
    stop(){ alive = false; cancelAnimationFrame(raf); if (io) io.disconnect(); },
    stats(){ return { hdr:HDR, quality, scale, dpr, w:W, h:H, dist, instances:iBufs.box.n + iBufs.cyl.n }; }
  };
}
