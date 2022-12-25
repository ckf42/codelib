// ==UserScript==
// @name        AoC show full star ratio
// @namespace   userDefinedJavascript
// @match       https://adventofcode.com/*/stats
// @grant       GM_info
// @version     1.0
// ==/UserScript==
'use strict';

let scriptCfg = {
    debugVerbose: true
};

let debugPrint = (scriptCfg.debugVerbose ? (x)=>console.log(`[${GM_info.script.name}] ` + x.toString()) : ()=>void 0);

debugPrint("Script starting ...");

document.querySelectorAll('pre.stats > a span.stats-both:nth-child(1)').forEach(function(pre){
    let twoStar = parseInt(pre.textContent);
    let oneStar = parseInt(pre.nextElementSibling.textContent);
    let valStr = (twoStar / (oneStar + twoStar) * 100).toFixed(1);
    debugPrint(parseInt(pre.previousSibling.textContent) + " " + valStr);
    pre.textContent += ` (${valStr}%)`;
});

