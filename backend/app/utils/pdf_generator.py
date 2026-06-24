import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# Define custom color themes
THEMES = {
    "navy": {
        "primary": colors.HexColor("#1e3a8a"),    # Dark Blue
        "secondary": colors.HexColor("#3b82f6"),  # Light Blue
        "accent": colors.HexColor("#eff6ff"),     # Light Background
        "text": colors.HexColor("#1e293b"),
        "white": colors.HexColor("#ffffff"),
        "border": colors.HexColor("#cbd5e1"),
    },
    "teal": {
        "primary": colors.HexColor("#0f766e"),    # Dark Teal
        "secondary": colors.HexColor("#0d9488"),  # Teal
        "accent": colors.HexColor("#f0fdfa"),     # Light Teal
        "text": colors.HexColor("#1f2937"),
        "white": colors.HexColor("#ffffff"),
        "border": colors.HexColor("#ccfbf1"),
    },
    "emerald": {
        "primary": colors.HexColor("#065f46"),    # Dark Green
        "secondary": colors.HexColor("#10b981"),  # Emerald
        "accent": colors.HexColor("#ecfdf5"),     # Light Green
        "text": colors.HexColor("#1f2937"),
        "white": colors.HexColor("#ffffff"),
        "border": colors.HexColor("#d1fae5"),
    },
    "charcoal": {
        "primary": colors.HexColor("#374151"),    # Dark Grey
        "secondary": colors.HexColor("#4b5563"),  # Grey
        "accent": colors.HexColor("#f9fafb"),     # Light Grey
        "text": colors.HexColor("#111827"),
        "white": colors.HexColor("#ffffff"),
        "border": colors.HexColor("#e5e7eb"),
    },
    "ruby": {
        "primary": colors.HexColor("#9f1239"),    # Dark Red
        "secondary": colors.HexColor("#f43f5e"),  # Rose/Ruby
        "accent": colors.HexColor("#fff1f2"),     # Light Rose
        "text": colors.HexColor("#1f2937"),
        "white": colors.HexColor("#ffffff"),
        "border": colors.HexColor("#ffe4e6"),
    },
    "dark": {
        "primary": colors.HexColor("#818cf8"),    # Indigo
        "secondary": colors.HexColor("#a78bfa"),  # Light Indigo
        "accent": colors.HexColor("#1e1b4b"),     # Dark Indigo card background
        "text": colors.HexColor("#cbd5e1"),       # Light Slate text
        "white": colors.HexColor("#ffffff"),      # Table header / metrics values
        "border": colors.HexColor("#312e81"),     # Indigo borders
    }
}

class NumberedCanvas(canvas.Canvas):
    theme_name_val = "navy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self._draw_background()

    def _draw_background(self):
        theme = getattr(self, "theme_name_val", "navy")
        if theme == "dark":
            self.saveState()
            self.setFillColor(colors.HexColor("#0f172a")) # Dark Slate background
            self.rect(0, 0, 612, 792, fill=True, stroke=False)
            self.restoreState()

    def _startPage(self):
        super()._startPage()
        self._draw_background()

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        
        # Text/Line Colors based on theme
        if getattr(self, "theme_name_val", "navy") == "dark":
            self.setFillColor(colors.HexColor("#94a3b8")) # Gray 400
            self.setStrokeColor(colors.HexColor("#312e81"))
        else:
            self.setFillColor(colors.HexColor("#64748b"))
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            
        self.setLineWidth(0.5)
        self.line(36, 45, 576, 45)
        
        # Footer text
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 32, footer_text)
        
        doc_info = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Vixx Personal Assistant"
        self.drawString(36, 32, doc_info)
        self.restoreState()


def get_numbered_canvas(theme_name: str):
    """Factory helper to bake theme name into NumberedCanvas class."""
    class CustomNumberedCanvas(NumberedCanvas):
        theme_name_val = theme_name
    return CustomNumberedCanvas


def generate_payments_report_pdf(payments_list: list, filename: str, config: dict = None) -> str:
    """
    Generates a beautifully formatted PDF report for payments.
    
    Parameters:
    - payments_list: List of dicts representing payment records
    - filename: The target path to save the PDF (inside uploads/ directory)
    - config: Dict containing customization options:
      - title: Custom main header title
      - subtitle: Custom subtitle
      - theme: 'navy', 'teal', 'emerald', 'charcoal', 'ruby'
      - exclude_notes: boolean (whether to hide notes column)
    """
    if config is None:
        config = {}
        
    theme_name = config.get("theme", "navy").lower()
    if theme_name not in THEMES:
        theme_name = "navy"
    theme = THEMES[theme_name]
    
    title_text = config.get("title") or "Payments & Cashflow Report"
    subtitle_text = config.get("subtitle") or f"Financial details and logged cashflow records"
    exclude_notes = config.get("exclude_notes", False)
    
    # Initialize Document
    # Letter size: 612 x 792 pt. 0.5 inch margin (36pt) leaves 540pt printable width.
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom Paragraph styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=theme["primary"]
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b")
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=theme["primary"]
    )
    
    metric_label_style = ParagraphStyle(
        'MetricLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=1 # Center
    )
    
    metric_val_style = ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=theme["primary"],
        alignment=1 # Center
    )
    
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=theme["white"]
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=theme["text"]
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=theme["text"]
    )

    story = []
    
    # Header Section
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(subtitle_text, subtitle_style))
    story.append(Spacer(1, 15))
    
    # Calculate Summary Metrics
    total_received = 0.0
    total_pending = 0.0
    total_overdue = 0.0
    currency_str = "INR" # Default
    
    for pay in payments_list:
        amt = float(pay.get("amount") or 0)
        curr = pay.get("currency") or "INR"
        currency_str = curr # Capture currency
        status = str(pay.get("status") or "").lower()
        
        if status == "received":
            total_received += amt
        elif status == "pending":
            total_pending += amt
        elif status == "overdue":
            total_overdue += amt
            
    # Metrics Cards Table
    total_amount = config.get("total_amount")
    if total_amount is not None:
        total_amount = float(total_amount)
        remaining_payment = total_amount - total_received
        total_outstanding = total_pending + total_overdue
        
        metric_data = [
            [
                Paragraph("TOTAL AMOUNT", metric_label_style),
                Paragraph("TOTAL RECEIVED", metric_label_style),
                Paragraph("REMAINING PAYMENT", metric_label_style),
                Paragraph("TOTAL OUTSTANDING", metric_label_style)
            ],
            [
                Paragraph(f"{total_amount:,.2f} {currency_str}", metric_val_style),
                Paragraph(f"{total_received:,.2f} {currency_str}", metric_val_style),
                Paragraph(f"{remaining_payment:,.2f} {currency_str}", metric_val_style),
                Paragraph(f"{total_outstanding:,.2f} {currency_str}", metric_val_style)
            ]
        ]
        metrics_table = Table(metric_data, colWidths=[135, 135, 135, 135])
    else:
        metric_data = [
            [
                Paragraph("TOTAL RECEIVED", metric_label_style),
                Paragraph("TOTAL PENDING", metric_label_style),
                Paragraph("TOTAL OVERDUE", metric_label_style)
            ],
            [
                Paragraph(f"{total_received:,.2f} {currency_str}", metric_val_style),
                Paragraph(f"{total_pending:,.2f} {currency_str}", metric_val_style),
                Paragraph(f"{total_overdue:,.2f} {currency_str}", metric_val_style)
            ]
        ]
        metrics_table = Table(metric_data, colWidths=[180, 180, 180])
    
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme["accent"]),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 1.5, theme["white"]),
        ('BOX', (0,0), (-1,-1), 1.5, theme["white"]),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Payments List Table
    story.append(Paragraph("Transactions Ledger", section_heading))
    story.append(Spacer(1, 8))
    
    # Table Header Definition
    if exclude_notes:
        headers = ["Project Title", "Date", "Type", "Status", "Amount"]
        widths = [190, 85, 85, 80, 100]
    else:
        headers = ["Project Title", "Date", "Type", "Status", "Amount", "Notes"]
        widths = [130, 75, 75, 70, 80, 110]
        
    table_data = [[Paragraph(h, table_hdr_style) for h in headers]]
    
    for pay in payments_list:
        proj = pay.get("project_title") or "General"
        date_raw = pay.get("received_date") or pay.get("due_date") or ""
        if date_raw:
            try:
                date_str = datetime.fromisoformat(str(date_raw)).strftime("%Y-%m-%d")
            except:
                date_str = str(date_raw).split("T")[0]
        else:
            date_str = "-"
            
        ptype = pay.get("payment_type") or "Advance"
        pstatus = str(pay.get("status") or "").upper()
        pamt = f"{float(pay.get('amount') or 0):,.2f} {pay.get('currency') or 'INR'}"
        notes = pay.get("notes") or ""
        
        status_color = "#047857" # Green for received
        if pstatus == "PENDING":
            status_color = "#b45309" # Orange
        elif pstatus == "OVERDUE":
            status_color = "#be123c" # Red
            
        status_html = f"<font color='{status_color}'><b>{pstatus}</b></font>"
        
        row = [
            Paragraph(proj, table_cell_bold),
            Paragraph(date_str, table_cell_style),
            Paragraph(ptype, table_cell_style),
            Paragraph(status_html, table_cell_style),
            Paragraph(pamt, table_cell_bold),
        ]
        if not exclude_notes:
            row.append(Paragraph(notes, table_cell_style))
            
        table_data.append(row)
        
    ledger_table = Table(table_data, colWidths=widths, repeatRows=1)
    
    # Table Styling
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), theme["primary"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('INNERGRID', (0,0), (-1,-1), 0.5, theme["border"]),
        ('BOX', (0,0), (-1,-1), 0.5, theme["primary"]),
    ])
    
    # Zebra striping
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.add('BACKGROUND', (0,i), (-1,i), theme["accent"])
            
    ledger_table.setStyle(t_style)
    story.append(ledger_table)
    
    # Build Document using NumberedCanvas with baked theme_name
    doc.build(story, canvasmaker=get_numbered_canvas(theme_name))
    return filename


def generate_todos_report_pdf(todos_list: list, filename: str, config: dict = None) -> str:
    """
    Generates a beautifully formatted PDF report for tasks/todos.
    """
    if config is None:
        config = {}
        
    theme_name = config.get("theme", "navy").lower()
    if theme_name not in THEMES:
        theme_name = "navy"
    theme = THEMES[theme_name]
    
    title_text = config.get("title") or "Tasks & Todos Report"
    subtitle_text = config.get("subtitle") or f"Task execution and backlog details"
    
    # Initialize Document
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom Paragraph styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=theme["primary"]
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b")
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=theme["primary"]
    )
    
    metric_label_style = ParagraphStyle(
        'MetricLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=1 # Center
    )
    
    metric_val_style = ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=theme["primary"],
        alignment=1 # Center
    )
    
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=theme["white"]
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=theme["text"]
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=theme["text"]
    )

    story = []
    
    # Header Section
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(subtitle_text, subtitle_style))
    story.append(Spacer(1, 15))
    
    # Calculate Summary Metrics
    total_tasks = len(todos_list)
    completed_tasks = 0
    pending_tasks = 0
    
    for todo in todos_list:
        status = str(todo.get("status") or "").lower()
        if status in ["done", "completed"]:
            completed_tasks += 1
        else:
            pending_tasks += 1
            
    # Metrics Cards Table
    metric_data = [
        [
            Paragraph("TOTAL TASKS", metric_label_style),
            Paragraph("COMPLETED TASKS", metric_label_style),
            Paragraph("PENDING TASKS", metric_label_style)
        ],
        [
            Paragraph(str(total_tasks), metric_val_style),
            Paragraph(str(completed_tasks), metric_val_style),
            Paragraph(str(pending_tasks), metric_val_style)
        ]
    ]
    
    metrics_table = Table(metric_data, colWidths=[180, 180, 180])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme["accent"]),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 1.5, theme["white"]),
        ('BOX', (0,0), (-1,-1), 1.5, theme["white"]),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Todos List Table
    story.append(Paragraph("Tasks Backlog", section_heading))
    story.append(Spacer(1, 8))
    
    # Table Header Definition
    headers = ["Task Title", "Project", "Priority", "Status", "Due Date"]
    widths = [160, 110, 80, 80, 110]
        
    table_data = [[Paragraph(h, table_hdr_style) for h in headers]]
    
    for todo in todos_list:
        title = todo.get("title") or "Untitled Task"
        proj = todo.get("project_title") or "General"
        priority = str(todo.get("priority") or "medium").upper()
        status = str(todo.get("status") or "todo").upper()
        
        date_raw = todo.get("due_date") or ""
        if date_raw:
            try:
                date_str = datetime.fromisoformat(str(date_raw)).strftime("%Y-%m-%d")
            except:
                date_str = str(date_raw).split("T")[0]
        else:
            date_str = "-"
            
        status_color = "#047857" if status in ["DONE", "COMPLETED"] else "#b45309" if status == "IN_PROGRESS" else "#64748b"
        status_html = f"<font color='{status_color}'><b>{status}</b></font>"
        
        row = [
            Paragraph(title, table_cell_bold),
            Paragraph(proj, table_cell_style),
            Paragraph(priority, table_cell_style),
            Paragraph(status_html, table_cell_style),
            Paragraph(date_str, table_cell_style),
        ]
        table_data.append(row)
        
    backlog_table = Table(table_data, colWidths=widths, repeatRows=1)
    
    # Table Styling
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), theme["primary"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('INNERGRID', (0,0), (-1,-1), 0.5, theme["border"]),
        ('BOX', (0,0), (-1,-1), 0.5, theme["primary"]),
    ])
    
    # Zebra striping
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.add('BACKGROUND', (0,i), (-1,i), theme["accent"])
            
    backlog_table.setStyle(t_style)
    story.append(backlog_table)
    
    # Build Document using NumberedCanvas with baked theme_name
    doc.build(story, canvasmaker=get_numbered_canvas(theme_name))
    return filename
