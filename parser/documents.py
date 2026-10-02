import re
from pathlib import Path
from pypdf import PdfReader
from docx import Document

CLAUSE = re.compile(r'^\s*(?:第\s*)?(\d+(?:\.\d+){2,5})(?:\s*条)?(?:[\s、．:：]+|(?=[\u4e00-\u9fff]))(.*)$')
CHAPTER = re.compile(r'^\s*((?:第[一二三四五六七八九十\d]+章|\d{1,2})[\s　]+[^。；]{1,60})\s*$')
SECTION = re.compile(r'^\s*(\d+\.\d+)\s+([^。；]{1,60})\s*$')

def read_pages(path: Path):
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        pdf = PdfReader(path)
        if len(pdf.pages) > 2000:
            raise ValueError('文件超过 2000 页，请拆分后导入。')
        return [p.extract_text() or '' for p in pdf.pages], 'PDF物理页'
    if suffix == '.docx':
        doc = Document(path)
        # Word 无可靠排版页码，不伪造物理页；按显式分页或逻辑段保存。
        from docx.oxml.ns import qn
        pages, lines = [], []
        for block in doc.element.body:
            if block.tag == qn('w:p'):
                lines.append(''.join(block.xpath('.//w:t/text()')))
                if block.xpath('.//w:br[@w:type="page"]'):
                    pages.append('\n'.join(lines)); lines = []
            elif block.tag == qn('w:tbl'):
                for row in block.xpath('./w:tr'):
                    lines.append(' | '.join(''.join(cell.xpath('.//w:t/text()')) for cell in row.xpath('./w:tc')))
        pages.append('\n'.join(lines))
        return pages, 'DOCX逻辑页（非排版页码）'
    if suffix == '.txt':
        raw = path.read_bytes()
        for encoding in ('utf-8-sig', 'gb18030'):
            try:
                return raw.decode(encoding).split('\f'), 'TXT逻辑页（以分页符分隔）'
            except UnicodeDecodeError:
                pass
        raise ValueError('无法识别文本编码，请转为 UTF-8。')
    raise ValueError('仅支持 PDF、DOCX、TXT；XLSX/HTML 接口待扩展。')

def parse(path: Path):
    pages, page_kind = read_pages(path)
    if not any(p.strip() for p in pages):
        raise ValueError('未提取到文本。扫描 PDF 需要先进行 OCR，系统不会生成虚构条文。')
    records = []
    chapter = section = ''
    current = None
    def flush():
        nonlocal current
        if current and current['text'].strip():
            records.append(current)
        current = None
    for page, text in enumerate(pages, 1):
        for raw in text.splitlines():
            line = raw.strip()
            if not line or re.fullmatch(r'[-—]?\s*\d+\s*[-—]?', line):
                continue
            match = CLAUSE.match(line)
            heading = CHAPTER.match(line)
            sub = SECTION.match(line)
            if match:
                flush()
                current = dict(chapter=chapter, section=section, clause=match[1], title=section or chapter,
                    text=line, page=page, page_end=page, page_kind=page_kind, parse_quality='条文级')
            elif sub or heading:
                flush()
                if sub:
                    section = line
                else:
                    chapter, section = line, ''
                current = dict(chapter=chapter, section=section, clause='', title=line,
                    text=line, page=page, page_end=page, page_kind=page_kind, parse_quality='章节级')
            else:
                if current is None:
                    current = dict(chapter=chapter, section=section, clause='', title=section or chapter,
                        text='', page=page, page_end=page, page_kind=page_kind, parse_quality='章节级')
                # 完整条文可跨页；章节退化片段按页保留定位。
                if not current['clause'] and current['page'] != page:
                    flush()
                    current = dict(chapter=chapter, section=section, clause='', title=section or chapter,
                        text='', page=page, page_end=page, page_kind=page_kind, parse_quality='章节级')
                current['text'] += ('\n' if current['text'] else '') + line
                current['page_end'] = page
    flush()
    blank = sum(not p.strip() for p in pages)
    warning = f'{blank} 页没有提取到文本，可能需要 OCR。' if blank else ''
    if not any(r['clause'] for r in records):
        warning += ' 未识别可靠条号，已按章节/页退化切分。'
    return records, warning.strip()
