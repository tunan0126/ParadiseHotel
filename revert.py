import re
import subprocess

content = open('index.html', encoding='utf-8').read()
old_content = subprocess.check_output(['git', 'show', 'HEAD:index.html']).decode('utf-8')
old_about = re.search(r'<main id="about-screen".*?</main>', old_content, re.DOTALL).group(0)
new_content = re.sub(r'<main id="about-screen".*?</main>', old_about, content, flags=re.DOTALL)
open('index.html', 'w', encoding='utf-8').write(new_content)
