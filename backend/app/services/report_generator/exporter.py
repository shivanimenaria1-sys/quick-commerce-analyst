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
