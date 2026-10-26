import os
import csv
import json
import datetime
from typing import List, Dict, Any
from app.core.config import settings
from app.core.storage import get_storage

class ReportGenerator:
    def __init__(self):
        self.reports_dir = settings.REPORTS_DIR
        self.storage = get_storage()

    def generate_pdf_report(
        self,
        brand_name: str,
        kpi_data: Dict[str, Any],
        clusters: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
        executive_insights: Dict[str, Any],
        time_range: str = "7d"
    ) -> str:
        """
        Generates a sleek executive PDF report using ReportLab or FPDF.
        Returns the generated PDF file path.
        """
        report_id = f"report_{brand_name.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(self.reports_dir, report_id)

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#0f172a"),
                spaceAfter=6
            )
            
            subtitle_style = ParagraphStyle(
                'DocSubtitle',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#64748b"),
                spaceAfter=14
            )
            
            h2_style = ParagraphStyle(
                'SectionHeading',
                parent=styles['Heading2'],
                fontSize=13,
                leading=17,
                textColor=colors.HexColor("#1e293b"),
                spaceBefore=12,
                spaceAfter=6
            )
            
            body_style = ParagraphStyle(
                'BodyTextCustom',
                parent=styles['Normal'],
                fontSize=9.5,
                leading=13.5,
                textColor=colors.HexColor("#334155")
            )
            
            story = []
            
            # Header
            story.append(Paragraph(f"ADVANCED BRANDPULSE AI // EXECUTIVE INTELLIGENCE BRIEF", title_style))
            story.append(Paragraph(f"<b>Brand:</b> {brand_name} &nbsp;|&nbsp; <b>Time Window:</b> Past {time_range.upper()} &nbsp;|&nbsp; <b>Generated:</b> {datetime.datetime.now().strftime('%B %d, %Y - %H:%M UTC')}", subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=14))
            
            # Executive Summary Box
            story.append(Paragraph("1. Executive Summary & Health Status", h2_style))
            summary_text = executive_insights.get("executive_summary", "Brand sentiment remains stable across monitored channels.")
            story.append(Paragraph(f"<b>Current Health:</b> {executive_insights.get('health_status', 'Good')}<br/>{summary_text}", body_style))
            story.append(Spacer(1, 10))
            
            # KPI Metrics Table
            story.append(Paragraph("2. Key Performance Indicators (KPIs)", h2_style))
            kpi_table_data = [
                ["Metric", "Value", "Status / Trend"],
                ["Total Analyzed Mentions", f"{kpi_data.get('total_mentions', 0):,}", "Verified Feed"],
                ["Net Sentiment Score (NSS)", f"+{kpi_data.get('net_sentiment_score', 0)}%" if kpi_data.get('net_sentiment_score', 0) > 0 else f"{kpi_data.get('net_sentiment_score', 0)}%", "Calculated (Pos - Neg)"],
                ["Positive Mentions", f"{kpi_data.get('positive_count', 0):,}", f"{round(kpi_data.get('positive_count',0)/max(kpi_data.get('total_mentions',1),1)*100, 1)}% of total"],
                ["Negative Mentions", f"{kpi_data.get('negative_count', 0):,}", f"{round(kpi_data.get('negative_count',0)/max(kpi_data.get('total_mentions',1),1)*100, 1)}% of total"],
                ["Crisis Risk Index", f"{kpi_data.get('crisis_risk_index', 0)}%", "Low" if kpi_data.get('crisis_risk_index', 0) < 30 else ("Elevated" if kpi_data.get('crisis_risk_index', 0) < 60 else "Critical Alert")],
                ["Share of Voice (SOV)", f"{kpi_data.get('share_of_voice', 0)}%", "vs Top 3 Competitors"],
                ["Estimated Total Reach", f"{kpi_data.get('estimated_reach', 0):,}", "Audience Impressions"]
            ]
            
            kpi_table = Table(kpi_table_data, colWidths=[180, 150, 190])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 10))
            
            # Topic Clusters
            story.append(Paragraph("3. Unsupervised Topic Modeling & Theme Clusters", h2_style))
            cluster_rows = [["Cluster Theme", "Mentions", "Top Keywords", "Dominant Sentiment"]]
            for c in clusters[:4]:
                cluster_rows.append([
                    c.get("name", "Topic"),
                    str(c.get("mentions_count", 0)),
                    ", ".join(c.get("top_keywords", [])[:4]),
                    c.get("dominant_sentiment", "Neutral").title()
                ])
            
            if len(cluster_rows) > 1:
                c_table = Table(cluster_rows, colWidths=[140, 60, 220, 100])
                c_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                story.append(c_table)
            
            story.append(Spacer(1, 10))
            
            # Actionable Recommendations
            story.append(Paragraph("4. Strategic AI Recommendations & Risk Controls", h2_style))
            recs = executive_insights.get("recommended_actions", [
                "Amplify top-performing praise content across verified channels.",
                "Deploy proactive CS responses to fast-growing query threads."
            ])
            for i, rec in enumerate(recs, 1):
                story.append(Paragraph(f"• <b>Action {i}:</b> {rec}", body_style))
            
            doc.build(story)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    self.storage.save(report_id, f.read(), content_type="application/pdf")
            return report_id
            
        except Exception as e:
            # Fallback simple text-based PDF/HTML if reportlab encounters error
            html_content = f"""
            ADVANCED BRANDPULSE AI REPORT
            Brand: {brand_name}
            Time: {time_range}
            Total Mentions: {kpi_data.get('total_mentions', 0)}
            Net Sentiment: {kpi_data.get('net_sentiment_score', 0)}%
            """
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    self.storage.save(report_id, f.read(), content_type="application/pdf")
            return report_id

    def generate_csv_export(self, brand_name: str, mentions: List[Dict[str, Any]]) -> str:
        """
        Exports mentions dataset into a clean CSV file.
        """
        filename = f"mentions_{brand_name.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(self.reports_dir, filename)

        headers = [
            "id", "timestamp", "platform", "author", "author_handle", "followers",
            "content", "sentiment", "sentiment_score", "dominant_emotion", "intent",
            "reach", "engagement_score", "virality_score", "is_crisis_flag", "url"
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for m in mentions:
                writer.writerow([
                    m.get("id", ""),
                    m.get("timestamp", ""),
                    m.get("platform", ""),
                    m.get("author", ""),
                    m.get("author_handle", ""),
                    m.get("author_followers", 0),
                    m.get("content", "").replace("\n", " "),
                    m.get("sentiment", ""),
                    m.get("sentiment_score", 0),
                    m.get("dominant_emotion", ""),
                    m.get("intent", ""),
                    m.get("reach", 0),
                    m.get("engagement_score", 0),
                    m.get("virality_score", 0),
                    m.get("is_crisis_flag", False),
                    m.get("url", "")
                ])

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self.storage.save(filename, f.read(), content_type="text/csv")

        return filename

    def generate_json_export(self, brand_name: str, data: Dict[str, Any]) -> str:
        """
        Exports comprehensive brand intelligence payload into a structured JSON file.
        """
        filename = f"brandpulse_export_{brand_name.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(self.reports_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self.storage.save(filename, f.read(), content_type="application/json")

        return filename

report_generator = ReportGenerator()
