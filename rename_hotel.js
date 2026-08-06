const fs = require('fs');

function replaceInFile(file, replacements) {
    let content = fs.readFileSync(file, 'utf8');
    for (const [oldStr, newStr] of replacements) {
        content = content.split(oldStr).join(newStr);
    }
    fs.writeFileSync(file, content, 'utf8');
}

const htmlFiles = ['index.html', 'admin.html', 'about.html'];
for (const file of htmlFiles) {
    if (fs.existsSync(file)) {
        let content = fs.readFileSync(file, 'utf8');
        content = content.replace(/HUCE HOTEL/g, 'Paradise');
        content = content.replace(/HUCE Hotel/g, 'Paradise');
        content = content.replace(/HUCE hotel/gi, 'Paradise');
        fs.writeFileSync(file, content, 'utf8');
    }
}
console.log('Renamed hotel to Paradise');
