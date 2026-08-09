const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const html = fs.readFileSync('index.html', 'utf8');
const appJs = fs.readFileSync('app.js', 'utf8');

const virtualConsole = new jsdom.VirtualConsole();
virtualConsole.on("error", (e) => { console.error("Error:", e); });

const dom = new JSDOM(html, {
    runScripts: "dangerously",
    resources: "usable", url: "http://localhost/",
    virtualConsole
});

try {
    dom.window.eval(appJs);
    console.log("Evaluated app.js successfully!");
    console.log("Type of openLoginModal:", typeof dom.window.openLoginModal);
} catch (e) {
    console.error("Failed:", e.name, e.message, e.stack);
}
