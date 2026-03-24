"""
report_service.py - Genera reportes HTML y PDF autocontenidos a partir de los resultados de sugerencias IA.

El HTML incluye todo el CSS y JS inline, sin dependencias externas.
El PDF se genera con WeasyPrint a partir de un HTML optimizado para impresion (tema claro, sin JS, sin CSS variables).
"""

from datetime import datetime, timezone
from html import escape


def _severity_color(severity: str) -> str:
    return {"high": "#e74c3c", "medium": "#f39c12", "low": "#3498db"}.get(severity, "#95a5a6")


def _severity_label(severity: str) -> str:
    return {"high": "Alta", "medium": "Media", "low": "Baja"}.get(severity, severity)


def _build_suggestion_rows(suggestions: list) -> str:
    if not suggestions:
        return '<tr><td colspan="5" style="text-align:center;color:#888;">Sin sugerencias</td></tr>'

    rows = ""
    for s in suggestions:
        color = _severity_color(s.get("severity", "low"))
        label = _severity_label(s.get("severity", "low"))
        orig = escape(s.get("original_snippet", ""))
        sugg = escape(s.get("suggested_snippet", ""))
        rows += f"""<tr>
<td><span class="badge" style="background:{color};">{label}</span></td>
<td><strong>{escape(s.get("title", ""))}</strong><br><small>{escape(s.get("description", ""))}</small></td>
<td class="line-ref">L{s.get("line_start", "?")}-L{s.get("line_end", "?")}</td>
<td><pre class="snippet original">{orig}</pre></td>
<td><pre class="snippet suggested">{sugg}</pre></td>
</tr>"""
    return rows


def _build_diff_html(diff: str) -> str:
    if not diff:
        return '<p class="empty">Sin cambios</p>'

    lines_html = ""
    for line in diff.splitlines():
        escaped = escape(line)
        if line.startswith("+++") or line.startswith("---"):
            lines_html += f'<span class="diff-meta">{escaped}</span>\n'
        elif line.startswith("@@"):
            lines_html += f'<span class="diff-hunk">{escaped}</span>\n'
        elif line.startswith("+"):
            lines_html += f'<span class="diff-add">{escaped}</span>\n'
        elif line.startswith("-"):
            lines_html += f'<span class="diff-del">{escaped}</span>\n'
        else:
            lines_html += f'<span>{escaped}</span>\n'

    return f'<pre class="diff-block">{lines_html}</pre>'


def _build_file_section(file_result: dict, index: int) -> str:
    file_name = escape(file_result.get("file_name", "archivo"))
    language = escape(file_result.get("language", ""))
    suggestions = file_result.get("suggestions", [])
    diff = file_result.get("diff", "")
    improved_code = escape(file_result.get("improved_code", ""))

    high = sum(1 for s in suggestions if s.get("severity") == "high")
    medium = sum(1 for s in suggestions if s.get("severity") == "medium")
    low = sum(1 for s in suggestions if s.get("severity") == "low")

    return f"""
<section class="file-section">
  <div class="file-header" onclick="toggleSection('file-{index}')">
    <h2>
      <span class="toggle" id="toggle-file-{index}">&#9660;</span>
      <span class="file-icon">&#128196;</span> {file_name}
      <span class="lang-tag">{language}</span>
    </h2>
    <div class="file-badges">
      {f'<span class="badge" style="background:#e74c3c;">{high} Alta</span>' if high else ''}
      {f'<span class="badge" style="background:#f39c12;">{medium} Media</span>' if medium else ''}
      {f'<span class="badge" style="background:#3498db;">{low} Baja</span>' if low else ''}
      <span class="badge" style="background:#2c3e50;">{len(suggestions)} total</span>
    </div>
  </div>
  <div class="file-body" id="file-{index}">
    <h3>Sugerencias</h3>
    <table class="suggestions-table">
      <thead>
        <tr>
          <th width="80">Severidad</th>
          <th>Detalle</th>
          <th width="80">Lineas</th>
          <th>Original</th>
          <th>Sugerido</th>
        </tr>
      </thead>
      <tbody>
        {_build_suggestion_rows(suggestions)}
      </tbody>
    </table>

    <h3>Diff</h3>
    {_build_diff_html(diff)}

    <details class="improved-section">
      <summary>Ver codigo mejorado completo</summary>
      <pre class="improved-code">{improved_code}</pre>
    </details>
  </div>
</section>"""


def generate_html_report(suggestions_data: dict) -> str:
    """Genera un HTML autocontenido a partir de CodeSuggestionsResponse serializado."""
    files = suggestions_data.get("files", [])
    total = suggestions_data.get("total_suggestions", 0)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    total_high = sum(
        1 for f in files for s in f.get("suggestions", []) if s.get("severity") == "high"
    )
    total_medium = sum(
        1 for f in files for s in f.get("suggestions", []) if s.get("severity") == "medium"
    )
    total_low = sum(
        1 for f in files for s in f.get("suggestions", []) if s.get("severity") == "low"
    )

    file_sections = ""
    for i, f in enumerate(files):
        file_sections += _build_file_section(f, i)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reporte de Sugerencias - Gitzy</title>
<style>
  :root {{
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --yellow: #d29922;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}

  /* Header */
  .report-header {{
    text-align: center;
    padding: 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }}
  .report-header h1 {{
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }}
  .report-header h1 span {{ color: var(--accent); }}
  .report-header .meta {{ color: var(--text-muted); font-size: 0.9rem; }}

  /* Stats */
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    text-align: center;
  }}
  .stat-card .number {{
    font-size: 2rem;
    font-weight: 700;
    display: block;
  }}
  .stat-card .label {{
    color: var(--text-muted);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  /* File sections */
  .file-section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 1.5rem;
    overflow: hidden;
  }}
  .file-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    cursor: pointer;
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }}
  .file-header:hover {{ background: #1c2129; }}
  .file-header h2 {{
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}
  .toggle {{ font-size: 0.8rem; transition: transform 0.2s; }}
  .toggle.collapsed {{ transform: rotate(-90deg); }}
  .file-icon {{ font-size: 1.2rem; }}
  .lang-tag {{
    background: var(--border);
    color: var(--text-muted);
    font-size: 0.75rem;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 400;
  }}
  .file-badges {{ display: flex; gap: 0.5rem; }}
  .file-body {{ padding: 1.5rem; }}
  .file-body.hidden {{ display: none; }}
  .file-body h3 {{
    font-size: 1rem;
    margin: 1.5rem 0 0.75rem 0;
    color: var(--accent);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
  }}
  .file-body h3:first-child {{ margin-top: 0; }}

  /* Badge */
  .badge {{
    display: inline-block;
    color: #fff;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 12px;
    white-space: nowrap;
  }}

  /* Table */
  .suggestions-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }}
  .suggestions-table th {{
    background: var(--bg);
    color: var(--text-muted);
    text-align: left;
    padding: 0.6rem 0.8rem;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .suggestions-table td {{
    padding: 0.8rem;
    border-top: 1px solid var(--border);
    vertical-align: top;
  }}
  .suggestions-table tr:hover td {{ background: #1c2129; }}
  .line-ref {{
    font-family: 'SF Mono', SFMono-Regular, Consolas, monospace;
    color: var(--text-muted);
    font-size: 0.85rem;
    white-space: nowrap;
  }}

  /* Snippets */
  .snippet {{
    font-family: 'SF Mono', SFMono-Regular, Consolas, monospace;
    font-size: 0.8rem;
    padding: 0.5rem 0.7rem;
    border-radius: 6px;
    overflow-x: auto;
    white-space: pre;
    max-height: 150px;
    margin: 0;
  }}
  .snippet.original {{ background: #2d1215; border: 1px solid #5c2328; }}
  .snippet.suggested {{ background: #122117; border: 1px solid #245830; }}

  /* Diff */
  .diff-block {{
    font-family: 'SF Mono', SFMono-Regular, Consolas, monospace;
    font-size: 0.8rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    overflow-x: auto;
    line-height: 1.5;
  }}
  .diff-meta {{ color: var(--text-muted); font-weight: 600; }}
  .diff-hunk {{ color: #bc8cff; }}
  .diff-add {{ color: var(--green); background: rgba(63,185,80,0.1); display: inline-block; width: 100%; }}
  .diff-del {{ color: var(--red); background: rgba(248,81,73,0.1); display: inline-block; width: 100%; }}

  /* Improved code */
  .improved-section {{ margin-top: 1rem; }}
  .improved-section summary {{
    cursor: pointer;
    color: var(--accent);
    font-weight: 600;
    padding: 0.5rem 0;
  }}
  .improved-code {{
    font-family: 'SF Mono', SFMono-Regular, Consolas, monospace;
    font-size: 0.8rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    overflow-x: auto;
    margin-top: 0.5rem;
    max-height: 500px;
  }}

  .empty {{ color: var(--text-muted); font-style: italic; padding: 1rem 0; }}

  /* Footer */
  .report-footer {{
    text-align: center;
    padding: 2rem 0 1rem;
    color: var(--text-muted);
    font-size: 0.8rem;
    border-top: 1px solid var(--border);
    margin-top: 2rem;
  }}

  /* Print */
  @media print {{
    body {{ background: #fff; color: #000; padding: 1rem; }}
    .file-header {{ cursor: default; }}
    .file-body.hidden {{ display: block !important; }}
    .stat-card {{ border: 1px solid #ccc; }}
    .file-section {{ border: 1px solid #ccc; }}
    .diff-block, .improved-code, .snippet {{ background: #f5f5f5; border: 1px solid #ccc; }}
    .diff-add {{ color: #22863a; background: #e6ffec; }}
    .diff-del {{ color: #cb2431; background: #ffeef0; }}
    :root {{ --bg: #f5f5f5; --surface: #fff; --border: #ddd; --text: #000; --text-muted: #555; --accent: #0366d6; }}
  }}
</style>
</head>
<body>
<div class="container">

  <div class="report-header">
    <h1><span>Gitzy</span> - Reporte de Sugerencias IA</h1>
    <p class="meta">Generado el {generated_at}</p>
  </div>

  <div class="stats">
    <div class="stat-card">
      <span class="number">{len(files)}</span>
      <span class="label">Archivos analizados</span>
    </div>
    <div class="stat-card">
      <span class="number">{total}</span>
      <span class="label">Sugerencias totales</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#e74c3c;">{total_high}</span>
      <span class="label">Severidad alta</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#f39c12;">{total_medium}</span>
      <span class="label">Severidad media</span>
    </div>
    <div class="stat-card">
      <span class="number" style="color:#3498db;">{total_low}</span>
      <span class="label">Severidad baja</span>
    </div>
  </div>

  {file_sections}

  <div class="report-footer">
    <p>Reporte generado por <strong>Gitzy</strong> con analisis de IA (Claude) &bull; {generated_at}</p>
  </div>

</div>

<script>
function toggleSection(id) {{
  const body = document.getElementById(id);
  const toggle = document.getElementById('toggle-' + id);
  body.classList.toggle('hidden');
  toggle.classList.toggle('collapsed');
}}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# PDF report (fpdf2 - pure Python, no system dependencies)
# ---------------------------------------------------------------------------

_SEVERITY_RGB = {
    "high": (231, 76, 60),
    "medium": (243, 156, 18),
    "low": (52, 152, 219),
}


def _safe(text: str, max_len: int = 0) -> str:
    """Limpia texto para fpdf (reemplaza caracteres no soportados por latin-1)."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    if max_len and len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "..."
    return cleaned


class _ReportPDF:
    """Construye el PDF del reporte de sugerencias usando fpdf2."""

    def __init__(self, suggestions_data: dict):
        from fpdf import FPDF

        self.data = suggestions_data
        self.files = suggestions_data.get("files", [])
        self.total = suggestions_data.get("total_suggestions", 0)
        self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        self.pdf = FPDF(orientation="P", unit="mm", format="A4")
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.add_page()

    def _count_severity(self, level: str) -> int:
        return sum(
            1 for f in self.files for s in f.get("suggestions", [])
            if s.get("severity") == level
        )

    def _draw_header(self):
        pdf = self.pdf
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(3, 102, 214)
        pdf.cell(0, 10, "Gitzy", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(36, 41, 46)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, " - Reporte de Sugerencias IA", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"Generado el {self.generated_at}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(3, 102, 214)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(8)

    def _draw_stats(self):
        pdf = self.pdf
        stats = [
            (str(len(self.files)), "Archivos", (36, 41, 46)),
            (str(self.total), "Sugerencias", (36, 41, 46)),
            (str(self._count_severity("high")), "Alta", (231, 76, 60)),
            (str(self._count_severity("medium")), "Media", (243, 156, 18)),
            (str(self._count_severity("low")), "Baja", (52, 152, 219)),
        ]
        col_w = 37
        start_x = (210 - col_w * 5) / 2
        y = pdf.get_y()

        for i, (value, label, color) in enumerate(stats):
            x = start_x + i * col_w
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.3)
            pdf.rect(x, y, col_w - 2, 20)

            pdf.set_xy(x, y + 2)
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(*color)
            pdf.cell(col_w - 2, 8, value, align="C")

            pdf.set_xy(x, y + 11)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(col_w - 2, 5, label.upper(), align="C")

        pdf.set_y(y + 26)

    def _draw_severity_badge(self, severity: str):
        pdf = self.pdf
        r, g, b = _SEVERITY_RGB.get(severity, (150, 150, 150))
        label = _severity_label(severity)
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7)
        w = pdf.get_string_width(label) + 6
        pdf.cell(w, 5, label, fill=True, align="C")
        pdf.set_text_color(36, 41, 46)

    def _draw_file_header(self, file_result: dict):
        pdf = self.pdf
        file_name = file_result.get("file_name", "archivo")
        language = file_result.get("language", "")
        suggestions = file_result.get("suggestions", [])

        pdf.set_fill_color(246, 248, 250)
        pdf.set_draw_color(200, 200, 200)
        y = pdf.get_y()
        pdf.rect(10, y, 190, 9, style="DF")

        pdf.set_xy(12, y + 1.5)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(36, 41, 46)
        pdf.cell(0, 6, f"{file_name}  [{language}]", new_x="RIGHT", new_y="TOP")

        badge_x = 160
        for sev in ("high", "medium", "low"):
            count = sum(1 for s in suggestions if s.get("severity") == sev)
            if count:
                pdf.set_xy(badge_x, y + 2)
                r, g, b = _SEVERITY_RGB[sev]
                pdf.set_fill_color(r, g, b)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 6)
                txt = f"{count} {_severity_label(sev)}"
                w = pdf.get_string_width(txt) + 4
                pdf.cell(w, 4, txt, fill=True, align="C")
                badge_x += w + 2

        pdf.set_text_color(36, 41, 46)
        pdf.set_y(y + 11)

    def _draw_section_title(self, title: str):
        pdf = self.pdf
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(3, 102, 214)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(230, 230, 230)
        pdf.set_line_width(0.2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_text_color(36, 41, 46)

    def _draw_suggestions_table(self, suggestions: list):
        pdf = self.pdf
        if not suggestions:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Sin sugerencias", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(36, 41, 46)
            return

        col_widths = [18, 72, 50, 50]
        headers = ["Sev.", "Detalle", "Original", "Sugerido"]

        pdf.set_fill_color(246, 248, 250)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(100, 100, 100)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 5, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(36, 41, 46)

        for s in suggestions:
            severity = s.get("severity", "low")
            title = _safe(s.get("title", ""), 50)
            desc = _safe(s.get("description", ""), 80)
            lines = f"L{s.get('line_start', '?')}-L{s.get('line_end', '?')}"
            orig = _safe(s.get("original_snippet", ""), 120)
            sugg = _safe(s.get("suggested_snippet", ""), 120)

            detail_text = f"{title}\n{desc}\n{lines}"
            line_count = max(
                detail_text.count("\n") + 1,
                orig.count("\n") + 1,
                sugg.count("\n") + 1,
                1
            )
            row_h = max(line_count * 3.5, 7)

            if pdf.get_y() + row_h > 280:
                pdf.add_page()

            y_before = pdf.get_y()
            x = pdf.get_x()

            # Severity
            pdf.set_font("Helvetica", "B", 7)
            r, g, b = _SEVERITY_RGB.get(severity, (150, 150, 150))
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255, 255, 255)
            label = _severity_label(severity)
            pdf.rect(x, y_before, col_widths[0], row_h, style="D")
            pdf.set_xy(x + 1, y_before + 1)
            lw = pdf.get_string_width(label) + 4
            pdf.cell(lw, 4, label, fill=True, align="C")
            pdf.set_text_color(36, 41, 46)

            # Detail
            pdf.set_xy(x + col_widths[0], y_before)
            pdf.rect(x + col_widths[0], y_before, col_widths[1], row_h, style="D")
            pdf.set_xy(x + col_widths[0] + 1, y_before + 0.5)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(col_widths[1] - 2, 3.5, title)
            pdf.set_xy(x + col_widths[0] + 1, y_before + 3.5)
            pdf.set_font("Helvetica", "", 6)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(col_widths[1] - 2, 3, desc, new_x="RIGHT", new_y="TOP")
            pdf.set_text_color(36, 41, 46)

            # Original
            ox = x + col_widths[0] + col_widths[1]
            pdf.set_fill_color(255, 238, 240)
            pdf.rect(ox, y_before, col_widths[2], row_h, style="DF")
            pdf.set_xy(ox + 1, y_before + 0.5)
            pdf.set_font("Courier", "", 5.5)
            pdf.multi_cell(col_widths[2] - 2, 2.8, orig, new_x="RIGHT", new_y="TOP")

            # Suggested
            sx = ox + col_widths[2]
            pdf.set_fill_color(230, 255, 236)
            pdf.rect(sx, y_before, col_widths[3], row_h, style="DF")
            pdf.set_xy(sx + 1, y_before + 0.5)
            pdf.multi_cell(col_widths[3] - 2, 2.8, sugg, new_x="RIGHT", new_y="TOP")

            pdf.set_y(y_before + row_h)
            pdf.set_font("Helvetica", "", 8)

    def _draw_diff(self, diff: str):
        pdf = self.pdf
        if not diff:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Sin cambios", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(36, 41, 46)
            return

        pdf.set_font("Courier", "", 6)
        for line in diff.splitlines():
            if pdf.get_y() > 280:
                pdf.add_page()

            text = _safe(line, 150)
            if line.startswith("+") and not line.startswith("+++"):
                pdf.set_fill_color(230, 255, 236)
                pdf.set_text_color(34, 134, 58)
                pdf.cell(190, 3, text, new_x="LMARGIN", new_y="NEXT", fill=True)
            elif line.startswith("-") and not line.startswith("---"):
                pdf.set_fill_color(255, 238, 240)
                pdf.set_text_color(203, 36, 49)
                pdf.cell(190, 3, text, new_x="LMARGIN", new_y="NEXT", fill=True)
            elif line.startswith("@@"):
                pdf.set_text_color(111, 66, 193)
                pdf.cell(190, 3, text, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_text_color(100, 100, 100)
                pdf.cell(190, 3, text, new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(36, 41, 46)

    def _draw_improved_code(self, code: str):
        pdf = self.pdf
        pdf.set_font("Courier", "", 5.5)
        pdf.set_fill_color(246, 248, 250)

        for line in code.splitlines()[:80]:
            if pdf.get_y() > 280:
                pdf.add_page()
            pdf.cell(190, 2.8, _safe(line, 160), new_x="LMARGIN", new_y="NEXT", fill=True)

        if len(code.splitlines()) > 80:
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 4, f"... ({len(code.splitlines()) - 80} lineas mas)", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(36, 41, 46)

    def _draw_file_section(self, file_result: dict):
        pdf = self.pdf
        if pdf.get_y() > 240:
            pdf.add_page()

        self._draw_file_header(file_result)

        self._draw_section_title("Sugerencias")
        self._draw_suggestions_table(file_result.get("suggestions", []))

        pdf.ln(3)
        self._draw_section_title("Diff")
        self._draw_diff(file_result.get("diff", ""))

        pdf.ln(3)
        self._draw_section_title("Codigo mejorado")
        self._draw_improved_code(file_result.get("improved_code", ""))

        pdf.ln(6)

    def _draw_footer(self):
        pdf = self.pdf
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, f"Reporte generado por Gitzy con analisis de IA (Claude)  -  {self.generated_at}", align="C")

    def build(self) -> bytes:
        self._draw_header()
        self._draw_stats()
        for f in self.files:
            self._draw_file_section(f)
        self._draw_footer()
        return self.pdf.output()


def generate_pdf_report(suggestions_data: dict) -> bytes:
    """Genera un PDF a partir de los datos de sugerencias usando fpdf2."""
    return _ReportPDF(suggestions_data).build()
