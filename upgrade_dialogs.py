import re

def update_html_admin(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all <div id="..." class="admin-modal-overlay"...>
    modals = re.findall(r'<div id="([^"]+)" class="admin-modal-overlay"[^>]*>', content)
    
    for modal_id in modals:
        start_pattern = r'<div id="' + modal_id + r'" class="admin-modal-overlay"[^>]*>'
        match = re.search(start_pattern, content)
        if match:
            start_idx = match.start()
            end_idx = match.end()
            brace_count = 1
            idx = end_idx
            while brace_count > 0 and idx < len(content):
                if content[idx:idx+4] == '<div':
                    brace_count += 1
                    idx += 4
                elif content[idx:idx+6] == '</div>':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                    idx += 6
                else:
                    idx += 1
            
            if brace_count == 0:
                new_opening = f'<dialog id="{modal_id}" class="modern-dialog admin-dialog">'
                content = content[:start_idx] + new_opening + content[end_idx:idx] + '</dialog>' + content[idx+6:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_html_admin('admin.html')
