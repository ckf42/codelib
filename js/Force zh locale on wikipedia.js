// ==UserScript==
// @name        Force zh locale on wikipedia
// @namespace   userDefinedJavascript
// @match       https://zh.wikipedia.org/*
// @match       https://zh.m.wikipedia.org/*
// @grant       none
// @version     1.0
// @run-at      document-start
// ==/UserScript==
'use strict';

let targetLocale = 'zh-tw';

let hostName = `^https?://${window.location.hostname}/`;
let targetHostStr = `${window.location.protocol}//${window.location.hostname}/${targetLocale}/`;
// for link to article
if (new RegExp(hostName + '(?:wiki|zh-hans)/').test(window.location.href)
    || window.location.href.match(new RegExp(hostName + '(zh(?:-\\w{2,4})?)/'))[1] != targetLocale){
    window.stop();
    window.location.replace(window.location.href.replace(new RegExp(hostName + '[^/]+/'),
                                                         targetHostStr));
} else if (new RegExp(hostName + 'w/').test(window.location.href)){ // for link to new page
    window.stop();
    window.location.replace(window.location.href.replace(new RegExp(hostName + 'w/index.php\?title='),
                                                         targetHostStr)
                            .replace(/&action=edit&redlink=1$/, ''));
} else {
    // replace all wiki links in article
    // BUG: affect hover float
    // window.addEventListener(
    //     'DOMContentLoaded',
    //     (event) => document.querySelectorAll('a')
    //                        .forEach((ele) => ele.href = (ele.classList.contains('new'))
    //                                                     ? (targetHostStr + ele.textContent)
    //                                                     : (ele.href.replace(new RegExp(hostName + 'wiki/'),
    //                                                                         targetHostStr)))
    // );
}
