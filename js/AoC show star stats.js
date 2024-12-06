// ==UserScript==
// @name        AoC show star stats
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

debugPrint("Adding two star ratio");
document.querySelectorAll('pre.stats > a span.stats-both:first-child').forEach(function(span){
    let twoStar = parseInt(span.textContent);
    let oneStar = parseInt(span.nextElementSibling.textContent);
	let total = twoStar + oneStar;
    let valStr = (twoStar / total * 100).toFixed(1);
    debugPrint(`${span.previousSibling.textContent}: ${valStr}% / ${total}`);
    span.textContent += ` (${valStr}%)`;
	span.parentNode.append(document.createTextNode(" "));
	span.parentNode.append(document.createTextNode(`${total}`));
});

debugPrint("Adding remain rate");
document.querySelectorAll('pre.stats > a:not(:last-child)').forEach(function(a){
    let oneStar = parseInt(a.lastChild.textContent);
	let prevOneStar = parseInt(a.nextElementSibling.lastChild.textContent);
	let valStr = (oneStar / prevOneStar * 100).toFixed(1);
	debugPrint(`${parseInt(a.firstChild.textContent)}: ${oneStar} / ${prevOneStar} = ${valStr}%`);
	a.append(document.createTextNode(" "));
	a.append(document.createTextNode(`(${valStr}%)`));
});

