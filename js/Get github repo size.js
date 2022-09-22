// ==UserScript==
// @name        Get github repo size
// @namespace   userDefinedJavascript
// @match       https://github.com/*
// @grant       GM_info
// @version     1.0
// ==/UserScript==
'use strict';

let scriptCfg = {
    debugVerbose: true
};

let debugPrint = (scriptCfg.debugVerbose ? (x)=>console.log(`[${GM_info.script.name}] ` + x.toString()) : ()=>void 0);

debugPrint("Script starting ...");

let downloadCodeBtn = document.querySelector('details[data-action="toggle:get-repo#onDetailsToggle"]');
if (downloadCodeBtn){
    debugPrint("Repo download button found");
    let gitDLAsZip = document.querySelector('get-repo a[data-open-app="link"]');
    let repoSize = -1;
    debugPrint("Getting repo size");
    gitDLAsZip.textContent = gitDLAsZip.textContent.replace("Download ZIP", "Download ZIP (getting repo size)");
    let responseJson = fetch("https://api.github.com/repos/" + window.location.href.replace(/^https?:\/\/github.com\//, ""))
                       .then(function(response){
                           return response.json();
                       }).then(function(response){
                           repoSize = response.size;
                           debugPrint("repo size: " + repoSize);
                           gitDLAsZip.textContent = gitDLAsZip.textContent
                                                              .replace("Download ZIP (getting repo size)", 
                                                                       "Download ZIP (approx. " + repoSize + " KB)");
                       }).catch(function(err){
                           debugPrint(err);
                           gitDLAsZip.textContent = gitDLAsZip.textContent
                                                              .replace("Download ZIP (getting repo size)", 
                                                                       "Download ZIP (size unknown)");
                       });
}
