// ==UserScript==
// @name        Fix white screen on tikzcd-editor
// @namespace   userDefinedJavascript
// @match       https://tikzcd.yichuanshen.de/
// @grant       GM_info
// @version     1.0
// ==/UserScript==
'use strict';

let scriptCfg = {
    debugVerbose: true
};

let debugPrint = (scriptCfg.debugVerbose ? (x)=>console.log(`[${GM_info.script.name}] ` + x.toString()) : ()=>void 0);

debugPrint("Script starting ...");

(new MutationObserver(
    (mutationList, observer) => mutationList.forEach(
        (m) => m.target.style.setProperty('display', 'unset', 'important'))
)).observe(document.querySelector('div#root'),
           {attributes: true, attributeFilter: ['style']});

