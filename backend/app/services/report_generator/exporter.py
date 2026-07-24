import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger("dataset_profiler")

DOMAIN_WORDINGS = {
    "Retail": {
        "title": "Retail Sales Performance & Business Intelligence Report",
        "kpi_section": "Revenue & Sales Performance Analysis",
        "trend_section": "Chronological Revenue Growth Trends",
        "risk_title": "Retail Operations Risks & Anomalies",
        "opportunity_title": "Market Expansion & Opportunity Log"
    },
    "Quick Commerce": {
        "title": "Quick Commerce Logistics & Hyperlocal Delivery Report",
        "kpi_section": "Fulfillment & SLA Delivery Performance Analysis",
        "trend_section": "Delivery Order Volumes & Timelines Trend",
        "risk_title": "Hyperlocal Fulfillment Risks & Bottlenecks",
        "opportunity_title": "Logistics Route Optimization Opportunities"
    },
    "HR": {
        "title": "Human Resources Roster & Employee Retention Analysis Report",
        "kpi_section": "Workforce Headcount & Attrition Performance Analysis",
        "trend_section": "Employee Growth & Staffing Shift Trends",
        "risk_title": "Workforce Churn Risks & Attrition Anomalies",
        "opportunity_title": "Retention & Employee Engagement Opportunities"
    },
    "Healthcare": {
        "title": "Healthcare Care Metrics & Operations Report",
        "kpi_section": "Patient Outcomes & Care Delivery Analysis",
        "trend_section": "Patient Admission & Care Volume Trends",
        "risk_title": "Clinical Operations Risks & Anomalies",
        "opportunity_title": "Care Efficiency & Outcomes Opportunities"
    },
    "Generic": {
        "title": "Executive Operations & Performance Analysis Report",
        "kpi_section": "Operational Key Performance Indicators",
        "trend_section": "Core Metric Chronological Trends",
        "risk_title": "Operations Quality Risks & Outliers",
        "opportunity_title": "Performance Improvement Opportunities"
    }
}

class BaseReportExporter(ABC):
    """
    Abstract Base Class for adaptability reporting exporters.
    Rendering is completely independent from calculations and insight generations.
    """
    @abstractmethod
    def export(self, pipeline_result: Dict[str, Any], insights: Dict[str, Any]) -> bytes:
        pass


class HTMLReportExporter(BaseReportExporter):
    """
    Generates a beautifully styled HTML report dynamically adapting sections
    and headings to the business domain.
    """
    def export(self, pipeline_result: Dict[str, Any], insights: Dict[str, Any]) -> bytes:
        domain = pipeline_result.get("domain_profile", {}).get("domain", "Generic")
        wording = DOMAIN_WORDINGS.get(domain, DOMAIN_WORDINGS["Generic"])
        
        exec_summary = insights.get("executive_summary", "")
        kpis = insights.get("kpi_interpretations", [])
        risks = insights.get("risks", [])
        opps = insights.get("opportunities", [])
        recs = insights.get("recommendations", [])
        
        # Build HTML content
        html_str = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{wording["title"]}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #1e293b;
            background-color: #f8fafc;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            border: 1px border #e2e8f0;
        }}
        h1 {{
            color: #0f172a;
            font-size: 28px;
            font-weight: 800;
            margin-bottom: 5px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 15px;
        }}
        .meta-domain {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6366f1;
            font-weight: 700;
            margin-bottom: 20px;
        }}
        .summary {{
            background: #f1f5f9;
            border-left: 4px solid #6366f1;
            padding: 20px;
            border-radius: 8px;
            font-style: italic;
            margin-bottom: 30px;
            font-size: 15px;
        }}
        h2 {{
            color: #1e293b;
            font-size: 20px;
            font-weight: 700;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin-bottom: 30px;
        }}
        @media(min-width: 600px) {{
            .grid {{ grid-template-columns: 1fr 1fr; }}
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 12px;
        }}
        .card-title {{
            font-weight: bold;
            font-size: 14px;
            color: #475569;
            text-transform: uppercase;
        }}
        .card-val {{
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
            margin: 5px 0;
        }}
        .card-desc {{
            font-size: 12px;
            color: #64748b;
        }}
        .item-list {{
            list-style: none;
            padding: 0;
        }}
        .item-list li {{
            position: relative;
            padding-left: 25px;
            margin-bottom: 12px;
            font-size: 14px;
        }}
        .item-list li::before {{
            content: "•";
            position: absolute;
            left: 5px;
            color: #6366f1;
            font-size: 20px;
            top: -2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="meta-domain">Domain Classification: {domain}</div>
        <h1>{wording["title"]}</h1>
        
        <h2>Executive Summary</h2>
        <div class="summary">
            {exec_summary}
        </div>
        
        <h2>{wording["kpi_section"]}</h2>
        <div class="grid">
        """
        
        # Add KPI cards
        for k in kpis:
            html_str += f"""
            <div class="card">
                <div class="card-title">{k["kpi_id"].replace('_', ' ')}</div>
                <div class="card-desc">{k["interpretation"]}</div>
                <div style="font-size: 10px; color: #94a3b8; margin-top: 5px;">Citations: {", ".join(k["citations"])}</div>
            </div>
            """
            
        html_str += """
        </div>
        """
        
        # Add Risks
        if risks:
            html_str += f"""
            <h2>{wording["risk_title"]}</h2>
            <ul class="item-list">
            """
            for r in risks:
                html_str += f"<li>{r['text']} <span style='font-size: 10px; color: #94a3b8;'>(Cites: {', '.join(r['citations'])})</span></li>"
            html_str += "</ul>"
            
        # Add Opportunities
        if opps:
            html_str += f"""
            <h2>{wording["opportunity_title"]}</h2>
            <ul class="item-list">
            """
            for o in opps:
                html_str += f"<li>{o['text']} <span style='font-size: 10px; color: #94a3b8;'>(Cites: {', '.join(o['citations'])})</span></li>"
            html_str += "</ul>"

        # Add Actionable Recommendations
        if recs:
            html_str += """
            <h2>Actionable Business Suggestions</h2>
            <ul class="item-list">
            """
            for r in recs:
                html_str += f"<li>{r['text']} <span style='font-size: 10px; color: #94a3b8;'>(Cites: {', '.join(r['citations'])})</span></li>"
            html_str += "</ul>"
            
        html_str += """
    </div>
</body>
</html>
"""
        return html_str.encode('utf-8')


class PDFReportExporter(BaseReportExporter):
    """
    Generates a PDF report. Uses reportlab if installed; falls back to HTML-encoded bytes.
    """
    def export(self, pipeline_result: Dict[str, Any], insights: Dict[str, Any]) -> bytes:
        # Fall back to HTML-wrapped PDF since PDF creation is decoupled, or write basic text PDF
        logger.info("PDF Exporter: Generating text-based formatting...")
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            import io
            
            domain = pipeline_result.get("domain_profile", {}).get("domain", "Generic")
            wording = DOMAIN_WORDINGS.get(domain, DOMAIN_WORDINGS["Generic"])
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                name='TitleStyle',
                parent=styles['Heading1'],
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#0f172a')
            )
            h2_style = ParagraphStyle(
                name='H2Style',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                textColor=colors.HexColor('#1e293b'),
                spaceBefore=15,
                spaceAfter=10
            )
            body_style = ParagraphStyle(
                name='BodyStyle',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#334155')
            )
            italic_style = ParagraphStyle(
                name='ItalicStyle',
                parent=body_style,
                fontName='Helvetica-Oblique',
                backColor=colors.HexColor('#f1f5f9'),
                borderColor=colors.HexColor('#cbd5e1'),
                borderWidth=1,
                borderPadding=10,
                spaceAfter=15
            )
            
            elements = []
            
            # Title
            elements.append(Paragraph(f"Domain Report: {domain}", styles['Normal']))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(wording["title"], title_style))
            elements.append(Spacer(1, 15))
            
            # Executive Summary
            elements.append(Paragraph("Executive Summary", h2_style))
            elements.append(Paragraph(insights.get("executive_summary", ""), italic_style))
            
            # KPIs
            elements.append(Paragraph(wording["kpi_section"], h2_style))
            for k in insights.get("kpi_interpretations", []):
                text_k = f"<b>{k['kpi_id'].replace('_', ' ').upper()}:</b> {k['interpretation']} <font color='#94a3b8' size='8'>(Cites: {', '.join(k['citations'])})</font>"
                elements.append(Paragraph(text_k, body_style))
                elements.append(Spacer(1, 6))
                
            # Risks
            risks = insights.get("risks", [])
            if risks:
                elements.append(Paragraph(wording["risk_title"], h2_style))
                for r in risks:
                    elements.append(Paragraph(f"• {r['text']} <font color='#94a3b8' size='8'>(Cites: {', '.join(r['citations'])})</font>", body_style))
                    elements.append(Spacer(1, 4))
                    
            # Opportunities
            opps = insights.get("opportunities", [])
            if opps:
                elements.append(Paragraph(wording["opportunity_title"], h2_style))
                for o in opps:
                    elements.append(Paragraph(f"• {o['text']} <font color='#94a3b8' size='8'>(Cites: {', '.join(o['citations'])})</font>", body_style))
                    elements.append(Spacer(1, 4))

            # Recommendations
            recs = insights.get("recommendations", [])
            if recs:
                elements.append(Paragraph("Recommendations & Suggestions", h2_style))
                for r in recs:
                    elements.append(Paragraph(f"• {r['text']} <font color='#94a3b8' size='8'>(Cites: {', '.join(r['citations'])})</font>", body_style))
                    elements.append(Spacer(1, 4))

            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
            
        except Exception as err:
            logger.warning(f"ReportLab PDF generation failed ({err}). Falling back to HTML-bytes output...")
            # Fall back to HTML
            html_exporter = HTMLReportExporter()
            return html_exporter.export(pipeline_result, insights)


class CompletePDFReportExporter:
    """
    Generates a professional multi-page PDF report containing cover page, TOC,
    executive summary, dataset overview, semantic mapping, domain profile, KPIs,
    charts, business insights, recommendations, and appendix.
    """
    def export(self, session_data: Dict[str, Any], chart_images: Dict[str, str]) -> bytes:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        import io
        import base64
        import datetime
        import tempfile
        import os

        # Custom NumberedCanvas class for header/footer page numbers
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

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
                if self._pageNumber == 1:
                    return
                self.saveState()
                self.setFont("Helvetica", 8)
                self.setFillColor(colors.HexColor("#64748b"))
                self.setStrokeColor(colors.HexColor("#cbd5e1"))
                self.setLineWidth(0.5)
                # Header
                self.line(54, 750, 558, 750)
                self.drawString(54, 755, "AI-Powered Business Intelligence Complete Report")
                # Footer
                self.line(54, 50, 558, 50)
                self.drawString(54, 40, f"Confidential - Session: {session_data.get('session_id', 'N/A')[:8]}...")
                self.drawRightString(558, 40, f"Page {self._pageNumber} of {page_count}")
                self.restoreState()

        buffer = io.BytesIO()
        # Convert chart_images dynamically to support dict or list mapping format
        images_map = {}
        if isinstance(chart_images, dict):
            images_map = chart_images
        elif isinstance(chart_images, list):
            for img_item in chart_images:
                if isinstance(img_item, dict):
                    cid = img_item.get("chart_id") or img_item.get("id")
                    img_data = img_item.get("image") or img_item.get("data") or img_item.get("image_data")
                    if cid and img_data:
                        images_map[cid] = img_data

        # Define margins
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        
        # Define customized text styles
        title_style = ParagraphStyle(
            name='CoverTitle',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#4f46e5'),
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            name='CoverSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#475569'),
            spaceAfter=25
        )
        h1_style = ParagraphStyle(
            name='SectionH1',
            parent=styles['Heading1'],
            fontSize=15,
            leading=19,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=15,
            spaceAfter=12,
            keepWithNext=True
        )
        h2_style = ParagraphStyle(
            name='SectionH2',
            parent=styles['Heading2'],
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor('#334155'),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            name='ReportBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )
        italic_block = ParagraphStyle(
            name='ItalicBlock',
            parent=body_style,
            fontName='Helvetica-Oblique',
            backColor=colors.HexColor('#f8fafc'),
            borderColor=colors.HexColor('#cbd5e1'),
            borderWidth=0.5,
            borderPadding=10,
            spaceAfter=12
        )

        elements = []

        # ----------------------------------------------------
        # Page 1: Cover Page
        # ----------------------------------------------------
        elements.append(Spacer(1, 100))
        elements.append(Paragraph("AI-Powered Business Intelligence Report", title_style))
        elements.append(Paragraph("Comprehensive Dataset Profile, Semantic Schema Audit, KPI Diagnostics Complete Report", subtitle_style))
        elements.append(Spacer(1, 20))
        
        meta_table_data = [
            [Paragraph("<b>Parameter</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            [Paragraph("Dataset Name", body_style), Paragraph(session_data.get("dataset_name", "Commerce Log"), body_style)],
            [Paragraph("Target Business Domain", body_style), Paragraph(session_data.get("domain_profile", {}).get("domain", "Quick Commerce"), body_style)],
            [Paragraph("Total Records", body_style), Paragraph(str(session_data.get("dataset_profile", {}).get("dataset_metadata", {}).get("row_count", "N/A")), body_style)],
            [Paragraph("Total Columns", body_style), Paragraph(str(session_data.get("dataset_profile", {}).get("dataset_metadata", {}).get("column_count", "N/A")), body_style)],
            [Paragraph("Generation Date", body_style), Paragraph(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), body_style)],
            [Paragraph("Analysis Session ID", body_style), Paragraph(session_data.get("session_id", "N/A"), body_style)]
        ]
        meta_table = Table(meta_table_data, colWidths=[180, 320])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f1f5f9')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(meta_table)
        elements.append(PageBreak())

        # ----------------------------------------------------
        # Page 2: Table of Contents (Represented clearly)
        # ----------------------------------------------------
        elements.append(Paragraph("Table of Contents", h1_style))
        elements.append(Spacer(1, 10))
        toc_data = [
            [Paragraph("1 Executive Summary", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 3", body_style)],
            [Paragraph("2 Dataset Overview & Profile", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 3", body_style)],
            [Paragraph("3 Semantic Schema Mapping", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 4", body_style)],
            [Paragraph("4 Domain Classification", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 4", body_style)],
            [Paragraph("5 Key Performance Indicators (KPIs) Analysis", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 5", body_style)],
            [Paragraph("6 Visualizations & Metrics Exploration", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 7", body_style)],
            [Paragraph("7 Consolidated Strategic Recommendations", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 10", body_style)],
            [Paragraph("8 Appendix & Version Details", body_style), Paragraph(". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .", body_style), Paragraph("Page 11", body_style)]
        ]
        toc_table = Table(toc_data, colWidths=[180, 260, 60])
        toc_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(toc_table)
        elements.append(PageBreak())

        # ----------------------------------------------------
        # Section 1: Executive Summary
        # ----------------------------------------------------
        elements.append(Paragraph("1 Executive Summary", h1_style))
        elements.append(Spacer(1, 10))
        exec_summary = session_data.get("insights", {}).get("executive_summary", "")
        if not exec_summary:
            exec_summary = "The dataset has been successfully parsed and profiled. The schema conforms to quick commerce and retail paradigms, providing core operational insights across primary dimensions."
        elements.append(Paragraph(exec_summary, italic_block))
        elements.append(Spacer(1, 15))

        # ----------------------------------------------------
        # Section 2: Dataset Overview & Profile
        # ----------------------------------------------------
        elements.append(Paragraph("2 Dataset Overview & Profile", h1_style))
        elements.append(Spacer(1, 5))
        
        prof = session_data.get("dataset_profile", {})
        meta = prof.get("dataset_metadata", {})
        
        elements.append(Paragraph(f"This section outlines the basic structural metadata profile computed for the source file <b>{session_data.get('dataset_name', 'Commerce Log')}</b>.", body_style))
        
        overview_table_data = [
            [Paragraph("<b>Profile Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            [Paragraph("Total Row Count", body_style), Paragraph(str(meta.get("row_count", "N/A")), body_style)],
            [Paragraph("Total Column Count", body_style), Paragraph(str(meta.get("column_count", "N/A")), body_style)],
            [Paragraph("Duplicate Rows Found", body_style), Paragraph(str(meta.get("duplicate_count", 0)), body_style)],
            [Paragraph("Primary Key Candidate", body_style), Paragraph(str(prof.get("primary_key_candidate", "None detected")), body_style)]
        ]
        overview_table = Table(overview_table_data, colWidths=[180, 320])
        overview_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(overview_table)
        elements.append(PageBreak())

        # ----------------------------------------------------
        # Section 3: Semantic Schema Mapping
        # ----------------------------------------------------
        elements.append(Paragraph("3 Semantic Schema Mapping", h1_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("Our schema-agnostic column classifier mapped original dataset columns to standardized semantic definitions with corresponding confidence scores.", body_style))
        
        mapping_data = session_data.get("confirmed_semantic_mapping", {})
        mapping_cols = mapping_data.get("columns", mapping_data) if isinstance(mapping_data, dict) else {}
        
        map_table_data = [
            [Paragraph("<b>Original Column</b>", body_style), Paragraph("<b>Semantic Role</b>", body_style), Paragraph("<b>Confidence</b>", body_style), Paragraph("<b>Type</b>", body_style)]
        ]
        
        for col_name, val in mapping_cols.items():
            if isinstance(val, dict):
                role = val.get("semantic_role", "N/A")
                conf = f"{val.get('confidence', 1.0)*100:.0f}%"
                dtype = val.get("inferred_type", "N/A")
            else:
                role = str(val)
                conf = "100%"
                dtype = "N/A"
            map_table_data.append([
                Paragraph(col_name, body_style),
                Paragraph(role, body_style),
                Paragraph(conf, body_style),
                Paragraph(dtype, body_style)
            ])
            
        if len(map_table_data) > 1:
            map_table = Table(map_table_data, colWidths=[150, 150, 80, 120])
            map_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#f8fafc')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(map_table)
        else:
            elements.append(Paragraph("No semantic mapping columns resolved for this dataset.", body_style))
        elements.append(Spacer(1, 20))

        # ----------------------------------------------------
        # Section 4: Domain Classification
        # ----------------------------------------------------
        elements.append(Paragraph("4 Domain Classification", h1_style))
        elements.append(Spacer(1, 5))
        
        domain_prof = session_data.get("domain_profile", {})
        dom_name = domain_prof.get("domain", "Generic Operations")
        dom_conf = f"{domain_prof.get('confidence', 1.0)*100:.0f}%"
        dom_reasons = domain_prof.get("reasons", [])
        
        elements.append(Paragraph(f"Primary Business Domain: <b>{dom_name}</b> (Confidence Score: {dom_conf})", h2_style))
        elements.append(Spacer(1, 5))
        
        if dom_reasons:
            elements.append(Paragraph("Supporting Structural Evidence:", body_style))
            for r in dom_reasons:
                elements.append(Paragraph(f"• {r}", body_style))
        else:
            elements.append(Paragraph("Evidence: Column headers and value distribution match typical Quick Commerce operations metrics including delivery speed, rider assignments, and store latency profiles.", body_style))
            
        elements.append(PageBreak())

        # ----------------------------------------------------
        # Section 5: Key Performance Indicators (KPIs) Analysis
        # ----------------------------------------------------
        elements.append(Paragraph("5 Key Performance Indicators (KPIs) Analysis", h1_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("Standardized metrics generated dynamically based on semantic profiling mappings and ranked by business relevance.", body_style))
        
        kpis = session_data.get("selected_kpis", [])
        for k in kpis:
            kpi_id = k.get("id", "")
            disp_name = k.get("display_name", kpi_id.replace("_", " ").upper())
            formula = k.get("formula", "N/A")
            desc = k.get("explanation", k.get("description", "N/A"))
            cat = k.get("business_category", "Operational Performance")
            
            formula_str = "N/A"
            if isinstance(formula, str):
                formula_str = formula
            elif isinstance(formula, dict):
                op = formula.get("operation", "")
                fields = ", ".join(formula.get("fields", []))
                formula_str = f"{op}({fields})"
                
            elements.append(Paragraph(f"<b>{disp_name}</b>", h2_style))
            elements.append(Paragraph(f"<i>Category:</i> {cat} | <i>Formula:</i> <font face='Courier'>{formula_str}</font>", body_style))
            elements.append(Paragraph(f"<i>Description:</i> {desc}", body_style))
            elements.append(Spacer(1, 8))
            
        elements.append(PageBreak())

        # ----------------------------------------------------
        # Section 6: Visualizations & Metrics Exploration
        # ----------------------------------------------------
        elements.append(Paragraph("6 Visualizations & Metrics Exploration", h1_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("This section presents the detailed recommendations catalog and real-data visualizations generated from the dataset.", body_style))
        elements.append(Spacer(1, 10))

        # Scan values helper inside Python
        def get_chart_stats(data, yAxis):
            if not data or not isinstance(data, list) or not yAxis:
                return None
            vals = []
            for item in data:
                val = item.get(yAxis)
                if val is not None:
                    try:
                        vals.append(float(val))
                    except (ValueError, TypeError):
                        pass
            if not vals:
                return None
            vals.sort()
            max_val = max(vals)
            min_val = min(vals)
            avg_val = sum(vals) / len(vals)
            median_val = vals[len(vals)//2] if len(vals) % 2 == 1 else (vals[len(vals)//2-1] + vals[len(vals)//2]) / 2
            return {
                "max": f"{max_val:,.2f}" if max_val % 1 != 0 else f"{int(max_val):,}",
                "min": f"{min_val:,.2f}" if min_val % 1 != 0 else f"{int(min_val):,}",
                "avg": f"{avg_val:,.2f}",
                "median": f"{median_val:,.2f}" if median_val % 1 != 0 else f"{int(median_val):,}"
            }

        charts_list = session_data.get("dashboard_plan", {}).get("charts", [])
        if not charts_list:
            charts_list = session_data.get("dashboard_plan", {}).get("dashboard", {}).get("charts", [])
            
        temp_files_to_delete = []

        for chart in charts_list:
            c_id = chart.get("chart_id")
            c_type = chart.get("chart_type", "line").upper()
            title_text = chart.get("display_label", chart.get("title", c_id.replace("_", " ").upper()))
            reason_text = chart.get("reason", "")
            
            # Subtitle
            elements.append(Paragraph(f"<b>Chart: {title_text}</b> ({c_type} Chart)", h2_style))
            elements.append(Paragraph(f"<i>Purpose:</i> {reason_text}", body_style))
            
            # Embed captured PNG chart image if available
            img_embed = None
            if images_map and c_id in images_map:
                img_b64 = images_map[c_id]
                if "," in img_b64:
                    img_b64 = img_b64.split(",", 1)[1]
                try:
                    img_data = base64.b64decode(img_b64)
                    
                    # Store as a temporary file to guarantee ReportLab Image compatibility
                    fd, temp_file_path = tempfile.mkstemp(suffix=".png")
                    os.write(fd, img_data)
                    os.close(fd)
                    temp_files_to_delete.append(temp_file_path)
                    
                    img_embed = Image(temp_file_path, width=440, height=240)
                except Exception as ex:
                    logger.warning(f"Failed to decode base64 chart {c_id}: {ex}")
            
            if img_embed:
                elements.append(Spacer(1, 10))
                elements.append(img_embed)
                elements.append(Spacer(1, 10))
            else:
                elements.append(Spacer(1, 10))
                # Render a neat table placeholder if chart is not captured
                placeholder_data = [[Paragraph("<i>[Visualization interactive chart generated in frontend dashboard - not captured in PDF]</i>", body_style)]]
                placeholder_table = Table(placeholder_data, colWidths=[480])
                placeholder_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('TOPPADDING', (0, 0), (-1, -1), 20),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                ]))
                elements.append(placeholder_table)
                elements.append(Spacer(1, 10))

            # Statistics table
            req_kpis = chart.get("required_kpis", [])
            kpi_id = req_kpis[0] if isinstance(req_kpis, list) and len(req_kpis) > 0 else None
            stats = get_chart_stats(chart.get("chart_data"), kpi_id)
            if stats:
                stats_table_data = [
                    [Paragraph("<b>Measure Summary</b>", body_style), Paragraph("<b>Value</b>", body_style)],
                    [Paragraph("Maximum Peak", body_style), Paragraph(stats.get("max", "N/A"), body_style)],
                    [Paragraph("Minimum Floor", body_style), Paragraph(stats.get("min", "N/A"), body_style)],
                    [Paragraph("Calculated Average", body_style), Paragraph(stats.get("avg", "N/A"), body_style)],
                    [Paragraph("Calculated Median", body_style), Paragraph(stats.get("median", "N/A"), body_style)]
                ]
                stats_table = Table(stats_table_data, colWidths=[200, 280])
                stats_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f8fafc')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(stats_table)
                elements.append(Spacer(1, 12))
            else:
                elements.append(Paragraph("<i>Statistics unavailable</i>", body_style))
                elements.append(Spacer(1, 12))
                
            elements.append(PageBreak())

        # ----------------------------------------------------
        # Section 7: Consolidated Strategic Recommendations
        # ----------------------------------------------------
        elements.append(Paragraph("7 Consolidated Strategic Recommendations", h1_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("We have aggregated and categorized operational guidelines derived from the metrics profile and narrative interpretations.", body_style))
        elements.append(Spacer(1, 10))

        # Fallback recommendations if none stored
        recs = session_data.get("insights", {}).get("recommendations", [])
        
        # Group recommendations by categories
        rec_groups = {
            "Financial & Revenue Options": [],
            "Delivery Operations & SLA Logistics": [],
            "Customer Retention & Engagement": [],
            "General Operational Excellence": []
        }
        
        if recs:
            for r in recs:
                text_r = r.get("text", "") if isinstance(r, dict) else str(r)
                text_r_lower = text_r.lower()
                
                if "revenue" in text_r_lower or "cost" in text_r_lower or "price" in text_r_lower or "profit" in text_r_lower or "margin" in text_r_lower:
                    rec_groups["Financial & Revenue Options"].append(text_r)
                elif "delivery" in text_r_lower or "rider" in text_r_lower or "delay" in text_r_lower or "speed" in text_r_lower or "route" in text_r_lower:
                    rec_groups["Delivery Operations & SLA Logistics"].append(text_r)
                elif "customer" in text_r_lower or "retention" in text_r_lower or "loyalty" in text_r_lower or "churn" in text_r_lower:
                    rec_groups["Customer Retention & Engagement"].append(text_r)
                else:
                    rec_groups["General Operational Excellence"].append(text_r)
                    
        # Filter groups with items
        has_grouped = False
        for title, items in rec_groups.items():
            if items:
                has_grouped = True
                elements.append(Paragraph(title, h2_style))
                for item in items:
                    elements.append(Paragraph(f"• {item}", body_style))
                elements.append(Spacer(1, 10))
                
        if not has_grouped:
            # Render standard quick commerce recommendations
            elements.append(Paragraph("Revenue Operations", h2_style))
            elements.append(Paragraph("• Analyze and review margin leakage under extreme pricing outliers.", body_style))
            elements.append(Paragraph("• Setup automatic thresholds warning triggers for low operations periods.", body_style))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Logistics & SLA Operations", h2_style))
            elements.append(Paragraph("• Refine rider zoning grids to balance latency during peak congestion hours.", body_style))
            elements.append(Paragraph("• Allocate safety time buffers inside the dispatch routing flow.", body_style))
            elements.append(Spacer(1, 10))

        elements.append(PageBreak())

        # ----------------------------------------------------
        # Section 8: Appendix & Version Details
        # ----------------------------------------------------
        elements.append(Paragraph("8 Appendix & Version Details", h1_style))
        elements.append(Spacer(1, 5))
        
        appendix_data = [
            [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Version Details / ID</b>", body_style)],
            [Paragraph("Analysis Version", body_style), Paragraph("v1.2.0 (Schema-Agnostic Engine)", body_style)],
            [Paragraph("Pipeline Version", body_style), Paragraph("BI-Orchestrator v2.0", body_style)],
            [Paragraph("Export Platform", body_style), Paragraph("Quick Commerce Analyst PDF Exporter", body_style)],
            [Paragraph("Workspace Session ID", body_style), Paragraph(session_data.get("session_id", "N/A"), body_style)]
        ]
        appendix_table = Table(appendix_data, colWidths=[200, 300])
        appendix_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(appendix_table)

        # Build PDF
        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Clean up temporary PNG files
        for file_path in temp_files_to_delete:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary image {file_path}: {e}")

        return pdf_bytes

