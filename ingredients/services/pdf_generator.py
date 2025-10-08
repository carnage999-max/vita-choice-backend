from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from django.utils import timezone


class SupplementFactsGenerator:
    """Generate Supplement Facts label PDF"""

    def __init__(self, formula):
        self.formula = formula
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom text styles"""
        self.styles.add(
            ParagraphStyle(
                name="SupplementTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.black,
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ServingSize",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=5,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Disclaimer",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
                spaceAfter=5,
                alignment=TA_LEFT,
            )
        )

    def generate(self):
        """Generate the PDF and return buffer"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        story = []

        # Title
        story.append(
            Paragraph(f"<b>{self.formula.name}</b>", self.styles["SupplementTitle"])
        )
        story.append(Spacer(1, 0.2 * inch))

        # Formula info
        info_text = f"""
        <b>Region:</b> {self.formula.region}<br/>
        <b>Created:</b> {self.formula.created_at.strftime('%Y-%m-%d')}<br/>
        <b>Formula ID:</b> {self.formula.id}
        """
        story.append(Paragraph(info_text, self.styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        # Description
        if self.formula.description:
            story.append(Paragraph(f"<b>Description:</b>", self.styles["Normal"]))
            story.append(Paragraph(self.formula.description, self.styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

        # Supplement Facts Panel
        story.append(self._create_supplement_facts_table())
        story.append(Spacer(1, 0.3 * inch))

        # Other Ingredients (if any have notes)
        other_ingredients = [item for item in self.formula.items.all() if item.notes]
        if other_ingredients:
            story.append(
                Paragraph("<b>Other Ingredients & Notes:</b>", self.styles["Normal"])
            )
            story.append(Spacer(1, 0.1 * inch))
            story.append(self._create_notes_section(other_ingredients))
            story.append(Spacer(1, 0.3 * inch))

        # Compliance warnings
        compliance = self.formula.check_compliance()
        if compliance["issues"]:
            story.append(
                Paragraph("<b>⚠️ Compliance Warnings:</b>", self.styles["Normal"])
            )
            story.append(Spacer(1, 0.1 * inch))
            story.append(self._create_warnings_section(compliance["issues"]))
            story.append(Spacer(1, 0.3 * inch))

        # Disclaimer
        disclaimer = """
        <b>DISCLAIMER:</b> This label is generated for informational purposes only. 
        It does not constitute regulatory approval. Consult with regulatory experts 
        before manufacturing or distributing this product. Verify all ingredient 
        compliance with local regulations.
        """
        story.append(Paragraph(disclaimer, self.styles["Disclaimer"]))

        # Footer
        footer = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Vita Choice App"
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(footer, self.styles["Disclaimer"]))

        # Build PDF
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer

    def _create_supplement_facts_table(self):
        """Create the main Supplement Facts table"""
        data = []

        # Header
        data.append(
            [Paragraph("<b>Supplement Facts</b>", self.styles["Normal"]), "", ""]
        )

        # Serving size placeholder
        total_weight = self.formula.total_weight_mg()
        if total_weight > 1000:
            serving = f"{total_weight/1000:.2f} g"
        else:
            serving = f"{total_weight:.2f} mg"

        data.append(
            [
                Paragraph(
                    f"<b>Serving Size:</b> {serving}", self.styles["ServingSize"]
                ),
                "",
                "",
            ]
        )

        # Column headers
        data.append(
            [
                Paragraph("<b>Ingredient</b>", self.styles["Normal"]),
                Paragraph("<b>Amount per Serving</b>", self.styles["Normal"]),
                Paragraph("<b>% Daily Value*</b>", self.styles["Normal"]),
            ]
        )

        # Ingredients
        for item in self.formula.items.select_related("ingredient").all():
            ingredient_name = item.ingredient.name
            amount = f"{item.dose_value} {item.dose_unit}"

            # Daily Value placeholder (would need DV database)
            dv = "†"  # † means DV not established

            data.append(
                [
                    Paragraph(ingredient_name, self.styles["Normal"]),
                    Paragraph(amount, self.styles["Normal"]),
                    Paragraph(dv, self.styles["Normal"]),
                ]
            )

        # Footer note
        data.append(
            [
                Paragraph(
                    "* Percent Daily Values are based on a 2,000 calorie diet.<br/>† Daily Value not established.",
                    self.styles["Disclaimer"],
                ),
                "",
                "",
            ]
        )

        # Create table
        table = Table(data, colWidths=[3 * inch, 1.5 * inch, 1 * inch])
        table.setStyle(
            TableStyle(
                [
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    # Serving size
                    ("SPAN", (0, 1), (-1, 1)),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey),
                    ("TOPPADDING", (0, 1), (-1, 1), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                    # Column headers
                    ("BACKGROUND", (0, 2), (-1, 2), colors.grey),
                    ("TEXTCOLOR", (0, 2), (-1, 2), colors.white),
                    ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 2), (-1, 2), 10),
                    ("TOPPADDING", (0, 2), (-1, 2), 6),
                    ("BOTTOMPADDING", (0, 2), (-1, 2), 6),
                    # All cells
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 3), (-1, -2), 4),
                    ("BOTTOMPADDING", (0, 3), (-1, -2), 4),
                    # Footer
                    ("SPAN", (0, -1), (-1, -1)),
                    ("FONTSIZE", (0, -1), (-1, -1), 7),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ]
            )
        )

        return table

    def _create_notes_section(self, items_with_notes):
        """Create notes section for ingredients"""
        data = [
            [
                Paragraph("<b>Ingredient</b>", self.styles["Normal"]),
                Paragraph("<b>Notes</b>", self.styles["Normal"]),
            ]
        ]

        for item in items_with_notes:
            data.append(
                [
                    Paragraph(item.ingredient.name, self.styles["Normal"]),
                    Paragraph(item.notes, self.styles["Normal"]),
                ]
            )

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        return table

    def _create_warnings_section(self, issues):
        """Create warnings section"""
        data = []

        for issue in issues:
            severity_icon = "🛑" if issue["severity"] == "RISK" else "⚠️"
            warning_text = f"""
            {severity_icon} <b>{issue['ingredient']}</b> ({issue['dose']})<br/>
            {issue['message']}<br/>
            <i>Action: {issue['action']}</i>
            """
            data.append([Paragraph(warning_text, self.styles["Normal"])])

        table = Table(data, colWidths=[6 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.Color(1, 0.95, 0.95)),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.red),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        return table


class FormulaSummaryGenerator:
    """Generate simple formula summary PDF"""

    def __init__(self, formula):
        self.formula = formula
        self.buffer = BytesIO()

    def generate(self):
        """Generate simple formula list PDF"""
        doc = SimpleDocTemplate(self.buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1976d2"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(self.formula.name, title_style))

        # Metadata
        metadata = f"""
        <b>Region:</b> {self.formula.region}<br/>
        <b>Created:</b> {self.formula.created_at.strftime('%Y-%m-%d %H:%M')}<br/>
        <b>Last Updated:</b> {self.formula.updated_at.strftime('%Y-%m-%d %H:%M')}<br/>
        <b>Total Weight:</b> {self.formula.total_weight_mg()} mg<br/>
        <b>Number of Ingredients:</b> {self.formula.items.count()}
        """
        story.append(Paragraph(metadata, styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        if self.formula.description:
            story.append(Paragraph(f"<b>Description:</b>", styles["Heading2"]))
            story.append(Paragraph(self.formula.description, styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

        # Ingredients table
        story.append(Paragraph("<b>Ingredients:</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))

        table_data = [
            [
                Paragraph("<b>Ingredient</b>", styles["Normal"]),
                Paragraph("<b>Category</b>", styles["Normal"]),
                Paragraph("<b>Amount</b>", styles["Normal"]),
                Paragraph("<b>Safety</b>", styles["Normal"]),
            ]
        ]

        for item in self.formula.items.select_related("ingredient").all():
            table_data.append(
                [
                    Paragraph(item.ingredient.name, styles["Normal"]),
                    Paragraph(item.ingredient.category or "-", styles["Normal"]),
                    Paragraph(f"{item.dose_value} {item.dose_unit}", styles["Normal"]),
                    Paragraph(item.ingredient.safety_level, styles["Normal"]),
                ]
            )

        table = Table(
            table_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1 * inch]
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(table)

        doc.build(story)
        self.buffer.seek(0)
        return self.buffer
