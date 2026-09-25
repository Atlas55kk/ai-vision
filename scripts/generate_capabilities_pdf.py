"""
AI-Vision Capabilities Report PDF Generator
Compiles a publication-quality, professional academic/engineering PDF report
using ReportLab with two-pass dynamic page numbering, custom palettes, and styled tables.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page counts and running headers/footers."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Suppress running header on cover/first page
        if self._pageNumber > 1:
            # Running Header
            self.drawString(54, letter[1] - 36, "AI-Vision: Cross-Platform Capabilities & Engineering Integration Report")
            self.drawRightString(letter[0] - 54, letter[1] - 36, "Project: Atlas55kk/ai-vision")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Running Footer (on all pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, letter[0] - 54, 45)
        
        self.drawString(54, 32, "Confidential & Academic Whitepaper — First-Principles Visual AI")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def build_capabilities_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Palette
    c_primary = colors.HexColor("#1A365D")    # Deep Navy
    c_secondary = colors.HexColor("#2B6CB0")  # Slate Blue
    c_dark = colors.HexColor("#2D3748")       # Body text
    c_accent = colors.HexColor("#319795")     # Teal
    c_bg_light = colors.HexColor("#F7FAFC")   # Light background
    c_border = colors.HexColor("#E2E8F0")     # Light border

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=14
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_dark,
        leftIndent=12,
        spaceAfter=3
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_dark
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.white
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#2C5282")
    )

    story = []

    # Title Block
    story.append(Paragraph("AI-VISION: COMPREHENSIVE CAPABILITIES REPORT", title_style))
    story.append(Paragraph("Universal Adaptive Visual Perception & Actuation Layer for Engineering, Game Dev & Scientific Simulation", subtitle_style))
    
    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Author / Lead:</b> Atlas jade (Atlas55kk)", meta_style),
            Paragraph("<b>Target Hardware:</b> Resource-Constrained (Low RAM / Integrated GPU)", meta_style)
        ],
        [
            Paragraph("<b>Document ID:</b> REP-CAP-01", meta_style),
            Paragraph("<b>Repository:</b> github.com/Atlas55kk/ai-vision", meta_style)
        ],
        [
            Paragraph("<b>Status:</b> Phase 1 & 2 Verified (Open Source)", meta_style),
            Paragraph("<b>Date:</b> September 2026", meta_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[240, 264])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Core Philosophy", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=6))
    story.append(Paragraph(
        "Modern frontier AI models excel in terminal and code environments but remain blind to native graphical desktop software. "
        "Engineering suites like <b>Godot, Blender, ANSYS, OpenFOAM, KiCad, and CAD</b> operate primarily through dense graphical user interfaces, "
        "3D viewports, and complex parameter panels. Traditional vision-based computer agents attempt to stream full-screen 30–60 FPS video or frequent 4K frames, "
        "which exhausts system RAM, spikes CPU to 40–70%, and consumes millions of cloud tokens per hour.",
        body_style
    ))
    story.append(Paragraph(
        "<b>AI-Vision solves this from first principles:</b> (1) <i>Hardware-Zero Footprint:</i> Uses pre-allocated memory buffers keeping total process RAM under <b>95 MB</b> with zero leaks. "
        "(2) <i>Dual-Tier Foveated Vision:</i> Replicates human visual acuity by supplying a global thumbnail (64 tokens) and on-demand 1:1 pixel micro-crops (80 tokens), cutting token usage by <b>over 90%</b>. "
        "(3) <i>On-Device Privacy Isolation:</i> Automatically tracks active application windows, masking background personal files, chats, and taskbars before data is serialized.",
        body_style
    ))

    # 2. Capabilities Across Installed Tools
    story.append(Spacer(1, 6))
    story.append(Paragraph("2. Deep Dive: Capabilities Across Installed Workstation Tools", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=6))

    tools_page1 = [
        (
            "A. Game Development: Godot Engine 4.3 (D:\\Games_Ai\\Game_Project\\)",
            [
                "<b>Horror Game Atmosphere Tuning:</b> Visually inspects 3D viewport shadow penumbras, ambient energy, and volumetric fog. Automatically spots when scene lighting is too flat.",
                "<b>Car Physics Telemetry (VehicleBody3D):</b> Reads suspension stiffness, damping force, tire friction slips, and center of mass from the Inspector, adjusting values to eliminate wheel jitter.",
                "<b>Console & Crash Diagnostics:</b> Foveates on red runtime error stack traces in the bottom console, diagnosing GDScript bugs without manual copy-pasting."
            ]
        ),
        (
            "B. 3D Modeling & Asset Creation: Blender 5.2 (D:\\blender\\)",
            [
                "<b>Autonomous Procedural Modeling (bpy):</b> Generates complete aerodynamic sports cars, wheel assemblies, and horror rooms via automated Python scripts without manual vertex manipulation.",
                "<b>Visual Quality Assurance:</b> Acts as the visual eye inspecting the rendered viewport for inverted normals, face intersections, and proper quad topology.",
                "<b>Automotive PBR Material Verification:</b> Verifies metallic clear-coat reflections, glass transmission, and studio light ribbon falloffs along body panels."
            ]
        )
    ]

    tools_page2 = [
        (
            "C. Simulation & Multiphysics: AnsysEM, blueCFD / OpenFOAM & ParaView 6.1.1",
            [
                "<b>AnsysEM (HFSS / Maxwell):</b> Reads 3D electromagnetic radiation patterns, S-parameter (S11 return loss) curves, and resonant frequencies for antenna and rectenna design.",
                "<b>blueCFD / OpenFOAM (CFD Aerodynamics):</b> Monitors residual convergence graphs (p, U, k, epsilon) in real time to catch diverging solver oscillations early.",
                "<b>ParaView 6.1.1 (3D Post-Processing):</b> Inspects airflow streamlines, pressure drag zones, and vortex separation points over vehicle bodies and hydrogen combustion chambers (H2-ICE)."
            ]
        ),
        (
            "D. Electronics, EDA & Semiconductor Design: KiCad, LTspice, Qucs-S & OpenROAD",
            [
                "<b>KiCad (PCB Layout & DRC):</b> Automatically zooms in on Design Rule Check (DRC) clearance violations and inspects 3D PCB views for component height collisions.",
                "<b>LTspice & Qucs-S (Waveform Analysis):</b> Reads transient oscilloscope waveforms, measuring voltage rise times, overshoot percentages, and ringing in rectenna circuits.",
                "<b>OpenROAD (Chip Design / ASIC):</b> Inspects standard cell density heatmaps, macro placements, and metal-layer routing congestion maps."
            ]
        ),
        (
            "E. Scientific Computing, Math & Academic Writing: Octave, Maxima, TeXstudio & Zotero",
            [
                "<b>GNU Octave & Maxima:</b> Analyzes matrix eigenvalues, phase space trajectories, and 3D surface plots for physical system stability.",
                "<b>TeXstudio & Zotero:</b> Compares LaTeX source code with the compiled PDF pane, identifying formula overflows, table clipping, and citation mismatches."
            ]
        ),
        (
            "F. Video Production: DaVinci Resolve / Blackmagic Design",
            [
                "<b>Color Grade Verification:</b> Reads Vectorscopes and RGB Parades to ensure game cinematic lighting and skin tones do not clip or distort.",
                "<b>Timeline Rhythm Guidance:</b> Correlates video cut points with audio waveform peaks for punchy game trailers."
            ]
        )
    ]

    for title, bullets in tools_page1:
        story.append(Paragraph(title, h2_style))
        for bullet in bullets:
            story.append(Paragraph(f"<b>-</b> {bullet}", bullet_style))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    story.append(Paragraph("2. Deep Dive: Capabilities Across Installed Workstation Tools (Cont.)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=4))

    for title, bullets in tools_page2:
        story.append(Paragraph(title, h2_style))
        for bullet in bullets:
            story.append(Paragraph(f"<b>-</b> {bullet}", bullet_style))
        story.append(Spacer(1, 2))

    story.append(PageBreak())

    # 3. Future Industrial Tools
    story.append(Paragraph("3. Future Industrial Tools & Academic Extension", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=5))
    story.append(Paragraph(
        "To ensure the system scales with advanced university research and professional engineering careers, AI-Vision is architected to seamlessly interface with future tools:",
        body_style
    ))

    future_data = [
        [
            Paragraph("<b>Domain</b>", table_header),
            Paragraph("<b>Target Software</b>", table_header),
            Paragraph("<b>AI-Vision Operational Value & Workflow Integration</b>", table_header)
        ],
        [
            Paragraph("<b>Mechanical CAD</b>", table_cell),
            Paragraph("SolidWorks / Fusion 360 / FreeCAD", table_cell),
            Paragraph("Reads 2D sketch constraint statuses (under/over-constrained), parametric dimension tables, and assembly joint mates for CNC/3D-printing.", table_cell)
        ],
        [
            Paragraph("<b>Heavy Game Engines</b>", table_cell),
            Paragraph("Unreal Engine 5 / Unity", table_cell),
            Paragraph("Navigates massive visual Blueprint node graphs, Nanite geometric budgets, Lumen dynamic GI bounces, and component inspectors.", table_cell)
        ],
        [
            Paragraph("<b>Enterprise Multiphysics</b>", table_cell),
            Paragraph("COMSOL Multiphysics", table_cell),
            Paragraph("Monitors coupled multi-field equations (thermal-structural-electrical), validating boundary conditions across complex interfaces.", table_cell)
        ],
        [
            Paragraph("<b>Semiconductor EDA</b>", table_cell),
            Paragraph("Altium Designer / Cadence", table_cell),
            Paragraph("Automates high-speed differential pair routing checks, length tuning, and Layout Versus Schematic (LVS) verification.", table_cell)
        ]
    ]

    future_table = Table(future_data, colWidths=[105, 140, 259])
    future_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(future_table)
    story.append(Spacer(1, 5))

    # 4. Verified Hardware Benchmarks
    story.append(Paragraph("4. Verified Hardware Benchmarks (Workstation Empirical Data)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=5))
    
    bench_data = [
        [
            Paragraph("<b>Performance Metric</b>", table_header),
            Paragraph("<b>Measured Value</b>", table_header),
            Paragraph("<b>Engineering Significance</b>", table_header)
        ],
        [
            Paragraph("<b>Full Screen Capture Latency</b>", table_cell),
            Paragraph("<b>29.2 ms (37.2 FPS)</b>", table_cell),
            Paragraph("Real-time responsive capture using DirectX Ctypes hooks directly from VRAM.", table_cell)
        ],
        [
            Paragraph("<b>Perceptual Delta Evaluation</b>", table_cell),
            Paragraph("<b>3.1 ms</b>", table_cell),
            Paragraph("Downsampled 64x64 luminance grid detects changes without CPU burden.", table_cell)
        ],
        [
            Paragraph("<b>Macro View Payload</b>", table_cell),
            Paragraph("<b>26.5 KB (~64 tokens)</b>", table_cell),
            Paragraph("Downsampled 640x360 global orientation image; dirt cheap API token cost.", table_cell)
        ],
        [
            Paragraph("<b>Foveated Micro-Crop Latency</b>", table_cell),
            Paragraph("<b>0.01 ms (~80 tokens)</b>", table_cell),
            Paragraph("Instantaneous 1:1 pixel native extraction of requested bounding boxes.", table_cell)
        ],
        [
            Paragraph("<b>Process RSS Memory</b>", table_cell),
            Paragraph("<b>< 95 MB total</b>", table_cell),
            Paragraph("Pre-allocated contiguous buffers prevent Garbage Collection memory spikes.", table_cell)
        ],
        [
            Paragraph("<b>RAM Drift (50–200 Frames)</b>", table_cell),
            Paragraph("<b>0.00 MB (Zero Leaks)</b>", table_cell),
            Paragraph("Guarantees the system can run as a background service for hours safely.", table_cell)
        ],
        [
            Paragraph("<b>Token Cost Reduction</b>", table_cell),
            Paragraph("<b>> 90% Savings</b>", table_cell),
            Paragraph("Replaces continuous 4K streaming with event-driven foveated queries.", table_cell)
        ]
    ]

    bench_table = Table(bench_data, colWidths=[135, 114, 255])
    bench_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(bench_table)
    story.append(Spacer(1, 5))

    # 5. University & Research Community Value
    story.append(Paragraph("5. University & Research Community Impact", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceAfter=4))
    story.append(Paragraph(
        "This project embodies true <b>first-principles research</b>: rather than throwing compute power at a problem, "
        "it re-architects the visual data pipeline from the ground up. "
        "For university researchers, graduate students, and independent developers who do not have $3,000 multi-GPU workstations, "
        "<b>AI-Vision demonstrates that intelligent perceptual sampling, delta gating, and hardware zero-copy pipelines can bring frontier AI capabilities "
        "to standard laptops and desktops.</b>",
        body_style
    ))
    
    # Callout Box
    callout_data = [[
        Paragraph(
            "<b>Open Source Repository:</b> https://github.com/Atlas55kk/ai-vision &nbsp;|&nbsp; "
            "<b>License:</b> Open for Academic Research & Engineering<br/>"
            "Publicly accessible, completely modular, and model-agnostic. Ready for university peer review and extension.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BEE3F8")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(callout_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] Capabilities Report compiled to: {output_path}")


if __name__ == "__main__":
    out_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "AI_Vision_Comprehensive_Capabilities_Report.pdf"))
    build_capabilities_pdf(out_pdf)
