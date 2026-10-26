#!/usr/bin/env node
"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),os=require("node:os"),path=require("node:path"),http=require("node:http"),{spawn}=require("node:child_process");
const ROOT=path.resolve(__dirname,".."),proxySources=[path.join(ROOT,"examples/minimal-html/proxy.js"),path.join(ROOT,"examples/desktop-dashboard/proxy.js")];
const NODE_BIN=process.env.NODE_BIN||(path.basename(process.execPath).toLowerCase()==="linker64"?"node":process.execPath);
function freePort(){return new Promise((resolve,reject)=>{const s=http.createServer();s.once("error",reject);s.listen(0,"127.0.0.1",()=>{const a=s.address();s.close(e=>e?reject(e):resolve(a.port));});});}
function request(port,options={},body=""){return new Promise((resolve,reject)=>{const req=http.request({host:"127.0.0.1",port,method:options.method||"GET",path:options.path||"/",headers:{...(options.headers||{})},timeout:1500},res=>{let data="";res.setEncoding("utf8");res.on("data",c=>data+=c);res.on("end",()=>resolve({status:res.statusCode,headers:res.headers,body:data}));});req.on("timeout",()=>req.destroy(new Error("test request timed out")));req.on("error",reject);if(body)req.write(body);req.end();});}
async function waitForProxy(port,child){const start=Date.now();while(Date.now()-start<4000){if(child.exitCode!==null)throw Error("proxy exited early");try{const r=await request(port);if(r.status===200)return;}catch{}await new Promise(r=>setTimeout(r,50));}throw Error("proxy did not start in time");}
async function runProxyTests(source){const upPort=await freePort(),proxyPort=await freePort(),temp=fs.mkdtempSync(path.join(os.tmpdir(),"lifeup-proxy-test-"));let child,upstream,token=null,captured="";
try{
upstream=http.createServer((req,res)=>{token=req.headers["x-test-token"]||null;let body="";req.on("data",c=>body+=c);req.on("end",()=>{captured=body;res.writeHead(200,{"Content-Type":"application/json"});res.end(JSON.stringify({code:200,message:"success",data:{test:true}}));});});
await new Promise((resolve,reject)=>upstream.listen(upPort,"127.0.0.1",resolve).once("error",reject));
fs.copyFileSync(source,path.join(temp,"proxy.js"));fs.writeFileSync(path.join(temp,"config.json"),JSON.stringify({host:"127.0.0.1:"+upPort,port:proxyPort,tokenHeader:"X-Test-Token",token:"test-token-only"}));fs.writeFileSync(path.join(temp,"index.html"),"proxy-test-page");
child=spawn(NODE_BIN,[path.join(temp,"proxy.js")],{cwd:temp,stdio:["ignore","ignore","pipe"]});await waitForProxy(proxyPort,child);
const page=await request(proxyPort);assert.equal(page.status,200,"serves the local page");assert.equal(page.body,"proxy-test-page");assert.equal(page.headers["access-control-allow-origin"],undefined,"does not enable wildcard CORS");
const hidden=await request(proxyPort,{path:"/config.json"});assert.equal(hidden.status,404,"does not expose config.json");
const traversal=await request(proxyPort,{path:"/..%2fconfig.json"});assert.ok([403,404].includes(traversal.status),"blocks directory traversal");
const badHost=await request(proxyPort,{headers:{Host:"attacker.example"}});assert.equal(badHost.status,403,"rejects unexpected Host header");
const badOrigin=await request(proxyPort,{headers:{Origin:"http://attacker.example"}});assert.equal(badOrigin.status,403,"rejects cross-origin requests");
const badMethod=await request(proxyPort,{method:"PUT",path:"/cloud/info"});assert.equal(badMethod.status,405,"rejects unsupported proxy methods");
const addr=await request(proxyPort,{path:"/__upstream"});assert.equal(addr.status,200,"GET /__upstream returns 200");assert.ok(JSON.parse(addr.body).port,"GET /__upstream body contains port");
const invalid=await request(proxyPort,{method:"POST",path:"/__upstream",headers:{"Content-Type":"application/json"}},JSON.stringify({host:"abc/def"}));assert.equal(invalid.status,400,"POST /__upstream rejects malformed host");
const wrong=await request(proxyPort,{method:"PUT",path:"/__upstream"});assert.equal(wrong.status,405,"PUT /__upstream is rejected");
const read=await request(proxyPort,{path:"/cloud/info"});assert.equal(read.status,200);assert.equal(token,"test-token-only","adds token only to upstream request");assert.equal(read.headers["access-control-allow-origin"],undefined,"does not add CORS headers to upstream response");
const body=JSON.stringify({urls:["lifeup://api/toast?text=test"]}),write=await request(proxyPort,{method:"POST",path:"/cloud/api/contentprovider",headers:{"Content-Type":"application/json"}},body);assert.equal(write.status,200);assert.equal(captured,body,"forwards POST body unchanged");
console.log("✓ "+path.relative(ROOT,source)+"：本地代理集成测试通过（静态资源、配置保护、路径边界、Host/Origin、方法限制、Token 转发、POST body、/__upstream 三项断言）。");
}finally{if(child&&child.exitCode===null)child.kill("SIGTERM");if(upstream)await new Promise(r=>upstream.close(()=>r()));fs.rmSync(temp,{recursive:true,force:true});}}
(async()=>{for(const source of proxySources)await runProxyTests(source);console.log("✓ 两份 proxy.js 的集成测试全部通过。");})().catch(e=>{console.error("✖ 本地代理集成测试失败：",e);process.exitCode=1;});
