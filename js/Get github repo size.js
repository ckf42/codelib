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

function toReadableUnit(i, decimalPlace=2) {
    let unitArr = ['KB', 'MB', 'GB', 'TB'];
    let unitIdx = 0;
    while (i >= 1000 && unitIdx < unitArr.length - 1){
        i /= 1000;
        unitIdx += 1;
    }
    return i.toFixed(decimalPlace) + ' ' + unitArr[unitIdx];
}

let downloadCodeBtn = document.querySelector('details[data-action="toggle:get-repo#onDetailsToggle"]');
if (downloadCodeBtn){
    debugPrint("Repo download button found");
    let gitDLAsZip = document.querySelector('get-repo a[data-open-app="link"]');
    let repoSize = -1;
    debugPrint("Getting repo size");
    gitDLAsZip.textContent = gitDLAsZip.textContent.replace("Download ZIP", "Download ZIP (getting repo size)");
    fetch("https://api.github.com/repos/" + window.location.href.replace(/^https?:\/\/github.com\//, ""))
        .then((response) => response.json()).then(function(response){
            repoSize = response.size;
            debugPrint("repo size: " + repoSize);
            gitDLAsZip.textContent = gitDLAsZip.textContent
                .replace("Download ZIP (getting repo size)", "Download ZIP (approx. " + toReadableUnit(repoSize) + ")");
        }).catch(function(err){
            debugPrint(err);
            gitDLAsZip.textContent = gitDLAsZip.textContent.replace("Download ZIP (getting repo size)", "Download ZIP (size unknown)");
        });
}
