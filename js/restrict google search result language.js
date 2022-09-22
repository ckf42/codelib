// ==UserScript==
// @name        restrict google search result language
// @namespace   userDefinedJavascript
// @match       https://www.google.com/search
// @grant       GM_registerMenuCommand
// @version     1.0
// ==/UserScript==
'use strict';

let langCodeDict = new Map([
    ['zhtw', 'zh-TW'],
    ['zhcn', 'zh-CN'],
    ['en', 'en'],
    ['ja', 'ja'],
    ['de', 'de'],
    ['eo', 'eo'],
]);

function chooseLanguage(langCode){
    let currentURL = new URL(window.location.href);
    if (langCode === null){
        currentURL.searchParams.delete('lr');
    } else {
        currentURL.searchParams.set('lr', 'lang_' + langCode);
    }
    window.location.href = currentURL.toString();
}

function addPendingLang(){
    let newURL = new URL(window.location.href);
    newURL.searchParams.delete('lr');
    window.history.pushState('Added language filter', '', newURL.toString() + '&lr=lang_');
}

for (let localeName of langCodeDict.keys()){
    GM_registerMenuCommand(`Search ${localeName} only`,
                           ()=>chooseLanguage(langCodeDict.get(localeName)));
}

if (new URL(window.location.href).searchParams.has('lr')){
    GM_registerMenuCommand("Remove language filter",
                           ()=>chooseLanguage(null));
}

GM_registerMenuCommand("Pending language filter",
                       addPendingLang);
