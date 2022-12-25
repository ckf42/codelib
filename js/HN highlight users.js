// ==UserScript==
// @name        HN highlight users
// @namespace   userDefinedJavascript
// @match       https://news.ycombinator.com/item
// @grant       GM_info
// @grant       GM_addStyle
// @run-at      document-idle
// @version     1.0
// ==/UserScript==
'use strict';

let scriptCfg = {
    debugVerbose: true
};

let debugPrint = (scriptCfg.debugVerbose ? (x)=>console.log(`[${GM_info.script.name}] ` + x.toString()) : ()=>void 0);

debugPrint("Script starting ...");

let htmlToElement = function(html) {
    // from https://stackoverflow.com/a/35385518
    let template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.firstChild;
}
function shuffleArray(array) {
    // https://stackoverflow.com/a/12646864
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}
function unif(mean, d){
    return mean + (Math.random() - 0.5) * d;
}

debugPrint('getting user list');
let aArr = Array.from(document.querySelectorAll('table.comment-tree a.hnuser'));
let userArr = shuffleArray([...new Set(aArr.map((a) => a.text))]);
debugPrint(`total ${userArr.length} commentors`);

debugPrint('deciding color');
let hueMap = new Map();
for (let i = 0; i < userArr.length; ++i){
    hueMap.set(userArr[i], `hsl(${360.0 * i / userArr.length}, ${unif(92, 8)}%, ${unif(80, 16)}%)`);
}
function getNameStyle(n){
    return `color: black; background: ${hueMap.get(n)}; border-radius: 15%; padding: 2px`;
}

debugPrint('counting posts');
let postCountMap = new Map();
for (let u of userArr){
    postCountMap.set(u, aArr.filter((a) => a.text == u).length);
}

debugPrint('painting color');
aArr.forEach(function(a){
    a.style = getNameStyle(a.text);
    a.title = (postCountMap.get(a.text) == 1 ? "unique comment" : postCountMap.get(a.text) + " comments") + " in this post";
    a.addEventListener('click', function(e){
        e.preventDefault();
        let toHaveBorder = a.parentNode.parentNode.parentNode.style.getPropertyValue('border') == '';
        if (toHaveBorder){
            debugPrint(`highlighting ${a.text}`);
        } else {
            debugPrint(`removing highlight on ${a.text}`);
        }
        aArr.filter((aa) => aa.text == a.text).forEach(function(aa){
            let p = aa.parentNode.parentNode.parentNode;
            if (toHaveBorder){
                p.style.setProperty('border', `solid ${hueMap.get(a.text)}`);
                p.style.setProperty('border-radius', '4px');
            } else {
                p.style.removeProperty('border');
                p.style.removeProperty('border-radius');
            }
        });
    });
});

debugPrint('noting OP');
let opTag = document.querySelector('table.fatitem a.hnuser');
if (hueMap.has(opTag.text)){
    opTag.style = getNameStyle(opTag.text);
    aArr.filter((a) => a.text == opTag.text).forEach((a) => a.text += ' (OP)');
}

// NOTE: css does not come in effect until manually triggered `flex`
// debugPrint('adding contract bar');
// GM_addStyle('td.votelinks {height: 100%; align-items: center; display: flex !important; flex-direction: column !important;}');
// aArr.forEach(function(a){
//     a.parentNode.parentNode.parentNode.previousSibling
//         .append(htmlToElement(`<div class="commentContract" style="height: 100%;background: ${hueMap.get(a.text)};width: 3px;display: block;"><i></i></div>`));
// });
// document.querySelectorAll('div.commentContract').forEach(function(div){
//     div.addEventListener('click', function(){

//     });
// });
