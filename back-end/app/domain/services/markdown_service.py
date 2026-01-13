"""
Servicio de procesamiento de Markdown.
Maneja sanitización, extensiones y transformaciones de Markdown.
"""

import re
import html
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TOCItem:
    """Elemento del índice de contenidos."""
    id: str
    text: str
    level: int
    children: List['TOCItem'] = field(default_factory=list)


@dataclass
class MarkdownRenderResult:
    """Resultado del procesamiento de Markdown."""
    html: str
    toc: List[TOCItem]
    word_count: int
    read_time_minutes: int
    has_code_blocks: bool
    languages_used: List[str]


class MarkdownService:
    """
    Servicio para procesamiento seguro de Markdown.
    Toda la lógica de renderizado reside en el backend.
    """
    
    # Patrones para callouts tipo Obsidian/Admonitions
    CALLOUT_PATTERN = re.compile(
        r'^:::(\w+)\s*(.*?)\n(.*?)^:::',
        re.MULTILINE | re.DOTALL
    )
    
    # Patrones para autolinks
    CTF_LINK_PATTERN = re.compile(r'\[\[ctf:([a-f0-9-]+)\]\]', re.IGNORECASE)
    WRITEUP_LINK_PATTERN = re.compile(r'\[\[writeup:([a-f0-9-]+)\]\]', re.IGNORECASE)
    USER_LINK_PATTERN = re.compile(r'@(\w+)')
    
    # Bloques de código
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    
    # Headers para TOC
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    # Tags HTML peligrosos que deben eliminarse
    DANGEROUS_TAGS = [
        'script', 'iframe', 'object', 'embed', 'form', 'input',
        'button', 'select', 'textarea', 'style', 'link', 'meta',
        'base', 'applet', 'frame', 'frameset', 'layer', 'ilayer',
        'bgsound', 'title', 'head', 'html', 'body', 'xml',
    ]
    
    # Atributos peligrosos
    DANGEROUS_ATTRS = [
        'onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout',
        'onkeydown', 'onkeyup', 'onkeypress', 'onfocus', 'onblur',
        'onsubmit', 'onreset', 'onchange', 'oninput', 'onscroll',
        'ondrag', 'ondrop', 'oncontextmenu', 'formaction', 'action',
        'href', 'xlink:href', 'src', 'data', 'dynsrc', 'lowsrc',
    ]
    
    # Callout types con iconos y clases
    CALLOUT_TYPES = {
        'info': {'icon': 'ℹ️', 'class': 'callout-info'},
        'warning': {'icon': '⚠️', 'class': 'callout-warning'},
        'danger': {'icon': '🚨', 'class': 'callout-danger'},
        'tip': {'icon': '💡', 'class': 'callout-tip'},
        'note': {'icon': '📝', 'class': 'callout-note'},
        'success': {'icon': '✅', 'class': 'callout-success'},
        'question': {'icon': '❓', 'class': 'callout-question'},
        'quote': {'icon': '💬', 'class': 'callout-quote'},
        'example': {'icon': '📋', 'class': 'callout-example'},
        'bug': {'icon': '🐛', 'class': 'callout-bug'},
        'abstract': {'icon': '📄', 'class': 'callout-abstract'},
        'todo': {'icon': '📌', 'class': 'callout-todo'},
        'flag': {'icon': '🚩', 'class': 'callout-flag'},
        'shell': {'icon': '💻', 'class': 'callout-shell'},
        'exploit': {'icon': '🔓', 'class': 'callout-exploit'},
    }
    
    # Lenguajes soportados para syntax highlighting
    SUPPORTED_LANGUAGES = {
        'python', 'py', 'javascript', 'js', 'typescript', 'ts',
        'bash', 'sh', 'shell', 'zsh', 'powershell', 'ps1', 'cmd',
        'sql', 'mysql', 'postgresql', 'c', 'cpp', 'csharp', 'cs',
        'java', 'kotlin', 'go', 'rust', 'ruby', 'php', 'perl',
        'html', 'css', 'scss', 'sass', 'less', 'xml', 'json', 'yaml',
        'markdown', 'md', 'dockerfile', 'makefile', 'nginx', 'apache',
        'ini', 'toml', 'env', 'gitignore', 'http', 'graphql',
        'assembly', 'asm', 'nasm', 'x86', 'arm', 'mips',
        'lua', 'r', 'matlab', 'julia', 'haskell', 'scala', 'swift',
        'diff', 'patch', 'plaintext', 'text', 'log', 'output',
        # Lenguajes específicos de seguridad/CTF
        'exploit', 'payload', 'shellcode', 'hexdump', 'binary',
        'wireshark', 'pcap', 'nmap', 'metasploit', 'gdb',
    }
    
    def __init__(self):
        self._code_blocks_placeholder: Dict[str, str] = {}
    
    def process_markdown(self, content: str, base_url: str = "") -> MarkdownRenderResult:
        """
        Procesa Markdown de forma segura y genera HTML sanitizado.
        
        Args:
            content: Contenido Markdown raw
            base_url: URL base para links internos
            
        Returns:
            MarkdownRenderResult con HTML, TOC, y metadata
        """
        if not content:
            return MarkdownRenderResult(
                html="",
                toc=[],
                word_count=0,
                read_time_minutes=0,
                has_code_blocks=False,
                languages_used=[]
            )
        
        # Estadísticas
        word_count = len(content.split())
        languages_used = []
        has_code_blocks = bool(self.CODE_BLOCK_PATTERN.search(content))
        
        # 1. Proteger bloques de código (evitar que se procesen)
        processed, code_blocks = self._protect_code_blocks(content)
        languages_used = list(set(lang for lang, _ in code_blocks.values() if lang))
        
        # 2. Procesar callouts
        processed = self._process_callouts(processed)
        
        # 3. Procesar autolinks
        processed = self._process_autolinks(processed, base_url)
        
        # 4. Generar TOC y añadir IDs a headers
        processed, toc = self._process_headers(processed)
        
        # 5. Procesar elementos Markdown básicos
        processed = self._process_basic_markdown(processed)
        
        # 6. Restaurar bloques de código con syntax highlighting
        processed = self._restore_code_blocks(processed)
        
        # 7. Sanitizar HTML final
        html_output = self._sanitize_html(processed)
        
        # 8. Calcular tiempo de lectura
        read_time = max(1, word_count // 200)
        
        return MarkdownRenderResult(
            html=html_output,
            toc=toc,
            word_count=word_count,
            read_time_minutes=read_time,
            has_code_blocks=has_code_blocks,
            languages_used=languages_used
        )
    
    def _protect_code_blocks(self, content: str) -> Tuple[str, Dict[str, Tuple[str, str]]]:
        """Reemplaza bloques de código con placeholders."""
        blocks = {}
        
        def replace_block(match):
            lang = match.group(1).lower() if match.group(1) else ''
            code = match.group(2)
            placeholder = f"__CODE_BLOCK_{hashlib.md5(code.encode()).hexdigest()}__"
            blocks[placeholder] = (lang, code)
            return placeholder
        
        processed = self.CODE_BLOCK_PATTERN.sub(replace_block, content)
        self._code_blocks_placeholder = blocks
        return processed, blocks
    
    def _restore_code_blocks(self, content: str) -> str:
        """Restaura bloques de código con formato HTML."""
        for placeholder, (lang, code) in self._code_blocks_placeholder.items():
            # Escapar HTML en el código
            escaped_code = html.escape(code)
            
            # Determinar clase de lenguaje
            lang_class = f"language-{lang}" if lang else "language-plaintext"
            
            # Crear botón de copiar
            copy_button = '<button class="code-copy-btn" title="Copiar código">📋</button>'
            
            # Header con lenguaje si está especificado
            lang_label = f'<span class="code-lang-label">{lang}</span>' if lang else ''
            
            # Crear bloque de código HTML
            code_html = f'''<div class="code-block">
                <div class="code-header">{lang_label}{copy_button}</div>
                <pre><code class="{lang_class}">{escaped_code}</code></pre>
            </div>'''
            
            content = content.replace(placeholder, code_html)
        
        return content
    
    def _process_callouts(self, content: str) -> str:
        """Procesa callouts/admonitions estilo Obsidian."""
        
        def replace_callout(match):
            callout_type = match.group(1).lower()
            title = match.group(2).strip()
            body = match.group(3).strip()
            
            # Obtener configuración del callout
            config = self.CALLOUT_TYPES.get(callout_type, {
                'icon': '📌',
                'class': 'callout-note'
            })
            
            # Usar tipo como título si no hay título personalizado
            display_title = title if title else callout_type.capitalize()
            
            return f'''<div class="callout {config['class']}">
                <div class="callout-header">
                    <span class="callout-icon">{config['icon']}</span>
                    <span class="callout-title">{html.escape(display_title)}</span>
                </div>
                <div class="callout-body">{body}</div>
            </div>'''
        
        return self.CALLOUT_PATTERN.sub(replace_callout, content)
    
    def _process_autolinks(self, content: str, base_url: str) -> str:
        """Procesa autolinks a CTFs, writeups y usuarios."""
        
        # Links a CTFs: [[ctf:uuid]]
        def ctf_link(match):
            ctf_id = match.group(1)
            return f'<a href="{base_url}/ctf/{ctf_id}" class="autolink autolink-ctf">🎯 CTF</a>'
        
        content = self.CTF_LINK_PATTERN.sub(ctf_link, content)
        
        # Links a writeups: [[writeup:uuid]]
        def writeup_link(match):
            writeup_id = match.group(1)
            return f'<a href="{base_url}/writeups/{writeup_id}" class="autolink autolink-writeup">📝 Writeup</a>'
        
        content = self.WRITEUP_LINK_PATTERN.sub(writeup_link, content)
        
        # Menciones a usuarios: @username
        def user_link(match):
            username = match.group(1)
            return f'<span class="user-mention">@{html.escape(username)}</span>'
        
        content = self.USER_LINK_PATTERN.sub(user_link, content)
        
        return content
    
    def _process_headers(self, content: str) -> Tuple[str, List[TOCItem]]:
        """Procesa headers y genera TOC."""
        toc = []
        header_counts = {}
        
        def replace_header(match):
            level = len(match.group(1))
            text = match.group(2).strip()
            
            # Generar ID único
            base_id = re.sub(r'[^\w\s-]', '', text.lower())
            base_id = re.sub(r'\s+', '-', base_id)
            
            # Manejar duplicados
            if base_id in header_counts:
                header_counts[base_id] += 1
                header_id = f"{base_id}-{header_counts[base_id]}"
            else:
                header_counts[base_id] = 0
                header_id = base_id
            
            # Añadir al TOC
            toc.append(TOCItem(id=header_id, text=text, level=level))
            
            # Crear header con anchor
            return f'<h{level} id="{header_id}" class="writeup-heading">{html.escape(text)}<a href="#{header_id}" class="header-anchor">#</a></h{level}>'
        
        processed = self.HEADER_PATTERN.sub(replace_header, content)
        return processed, toc
    
    def _process_basic_markdown(self, content: str) -> str:
        """Procesa elementos Markdown básicos."""
        
        # Negrita: **text** o __text__
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'__(.+?)__', r'<strong>\1</strong>', content)
        
        # Cursiva: *text* o _text_
        content = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', content)
        content = re.sub(r'_([^_]+)_', r'<em>\1</em>', content)
        
        # Tachado: ~~text~~
        content = re.sub(r'~~(.+?)~~', r'<del>\1</del>', content)
        
        # Código inline: `code`
        content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', content)
        
        # Links: [text](url)
        content = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener noreferrer">{html.escape(m.group(1))}</a>',
            content
        )
        
        # Imágenes: ![alt](url)
        content = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            lambda m: f'<figure class="writeup-image"><img src="{html.escape(m.group(2))}" alt="{html.escape(m.group(1))}" loading="lazy" class="lightbox-trigger"><figcaption>{html.escape(m.group(1))}</figcaption></figure>',
            content
        )
        
        # Blockquotes: > text
        content = re.sub(
            r'^>\s*(.+)$',
            r'<blockquote class="writeup-quote">\1</blockquote>',
            content,
            flags=re.MULTILINE
        )
        
        # Listas no ordenadas: - item o * item
        content = re.sub(
            r'^[-*]\s+(.+)$',
            r'<li class="list-item">\1</li>',
            content,
            flags=re.MULTILINE
        )
        
        # Listas ordenadas: 1. item
        content = re.sub(
            r'^\d+\.\s+(.+)$',
            r'<li class="list-item ordered">\1</li>',
            content,
            flags=re.MULTILINE
        )
        
        # Checkboxes: - [ ] o - [x]
        content = re.sub(
            r'^-\s*\[\s*\]\s*(.+)$',
            r'<li class="checkbox-item"><input type="checkbox" disabled> \1</li>',
            content,
            flags=re.MULTILINE
        )
        content = re.sub(
            r'^-\s*\[x\]\s*(.+)$',
            r'<li class="checkbox-item checked"><input type="checkbox" checked disabled> \1</li>',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        # Líneas horizontales: --- o ***
        content = re.sub(r'^[-*]{3,}$', r'<hr class="writeup-hr">', content, flags=re.MULTILINE)
        
        # Tablas básicas
        content = self._process_tables(content)
        
        # Párrafos (líneas sueltas)
        lines = content.split('\n')
        processed_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('<'):
                line = f'<p>{line}</p>'
            processed_lines.append(line)
        
        content = '\n'.join(processed_lines)
        
        return content
    
    def _process_tables(self, content: str) -> str:
        """Procesa tablas Markdown."""
        # Patrón para detectar tablas
        table_pattern = re.compile(
            r'^\|(.+)\|\s*\n\|[-:|]+\|\s*\n((?:\|.+\|\s*\n?)+)',
            re.MULTILINE
        )
        
        def replace_table(match):
            header_row = match.group(1)
            body_rows = match.group(2).strip().split('\n')
            
            # Procesar header
            headers = [h.strip() for h in header_row.split('|') if h.strip()]
            header_html = ''.join(f'<th>{html.escape(h)}</th>' for h in headers)
            
            # Procesar body
            body_html = ''
            for row in body_rows:
                cells = [c.strip() for c in row.split('|') if c.strip()]
                cells_html = ''.join(f'<td>{html.escape(c)}</td>' for c in cells)
                body_html += f'<tr>{cells_html}</tr>'
            
            return f'''<div class="table-wrapper">
                <table class="writeup-table">
                    <thead><tr>{header_html}</tr></thead>
                    <tbody>{body_html}</tbody>
                </table>
            </div>'''
        
        return table_pattern.sub(replace_table, content)
    
    def _sanitize_html(self, content: str) -> str:
        """Sanitiza HTML para prevenir XSS."""
        
        # Eliminar tags peligrosos
        for tag in self.DANGEROUS_TAGS:
            # Tags de apertura y cierre
            content = re.sub(
                rf'<{tag}[^>]*>.*?</{tag}>',
                '',
                content,
                flags=re.IGNORECASE | re.DOTALL
            )
            # Tags auto-cerrados
            content = re.sub(
                rf'<{tag}[^>]*/?>', '',
                content,
                flags=re.IGNORECASE
            )
        
        # Eliminar atributos peligrosos
        for attr in self.DANGEROUS_ATTRS:
            if attr not in ['href', 'src']:  # Permitir href y src controlados
                content = re.sub(
                    rf'\s*{attr}\s*=\s*["\'][^"\']*["\']',
                    '',
                    content,
                    flags=re.IGNORECASE
                )
        
        # Eliminar javascript: en URLs
        content = re.sub(
            r'(href|src)\s*=\s*["\']javascript:[^"\']*["\']',
            r'\1=""',
            content,
            flags=re.IGNORECASE
        )
        
        # Eliminar data: URIs potencialmente peligrosos (excepto imágenes)
        content = re.sub(
            r'(href|src)\s*=\s*["\']data:(?!image/)[^"\']*["\']',
            r'\1=""',
            content,
            flags=re.IGNORECASE
        )
        
        return content
    
    def extract_summary(self, content: str, max_length: int = 200) -> str:
        """Extrae un resumen del contenido Markdown."""
        # Eliminar código
        text = self.CODE_BLOCK_PATTERN.sub('', content)
        text = self.INLINE_CODE_PATTERN.sub(r'\1', text)
        
        # Eliminar headers
        text = self.HEADER_PATTERN.sub(r'\2', text)
        
        # Eliminar formato Markdown
        text = re.sub(r'[*_~`#>\[\]!|]', '', text)
        text = re.sub(r'\(http[^)]+\)', '', text)
        
        # Limpiar espacios
        text = ' '.join(text.split())
        
        # Truncar
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return text
    
    def validate_content(self, content: str) -> Dict[str, str]:
        """Valida el contenido de un writeup."""
        errors = {}
        
        if not content or len(content.strip()) < 100:
            errors['content'] = 'El contenido debe tener al menos 100 caracteres'
        elif len(content) > 200000:
            errors['content'] = 'El contenido no puede exceder 200,000 caracteres'
        
        # Verificar balance de bloques de código
        code_opens = content.count('```')
        if code_opens % 2 != 0:
            errors['syntax'] = 'Hay bloques de código sin cerrar'
        
        return errors


# Instancia global
markdown_service = MarkdownService()
