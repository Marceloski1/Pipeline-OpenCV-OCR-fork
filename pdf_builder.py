from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from datetime import datetime
import os

def filter_and_renumber_actors(actors_list):
    """
    Filtra actores sin nombre y reenumera los que sí tienen
    
    Args:
        actors_list: Lista de tuplas (actor_id, actor_name)
        
    Returns:
        Tuple: (filtered_list, stats_dict)
        filtered_list: Lista filtrada y reenumerada
        stats_dict: Diccionario con estadísticas del filtrado
    """
    # Filtrar actores que tienen nombre (no vacío y no solo espacios)
    filtered = [(actor_id, name.strip()) for actor_id, name in actors_list if name and name.strip()]
    
    # Reenumerar del 1 en adelante
    renumbered = []
    for new_id, (old_id, name) in enumerate(filtered, start=1):
        renumbered.append((new_id, name))
    
    # Estadísticas
    stats = {
        'total_detected': len(actors_list),
        'with_names': len(filtered),
        'without_names': len(actors_list) - len(filtered),
        'filtered_list': renumbered
    }
    
    return renumbered, stats

def create_actors_pdf(actors_list, detection_date=None, image_path=None):
    """
    Create a PDF with actors information (filtrado y reenumerado)
    
    Args:
        actors_list: List of tuples (actor_id, actor_name)
        detection_date: Date of detection (optional)
        image_path: Path to processed image (optional)
    
    Returns:
        BytesIO buffer with PDF content
    """
    # Filtrar y reenumerar actores
    filtered_actors, stats = filter_and_renumber_actors(actors_list)
    
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    stats_style = ParagraphStyle(
        'StatsStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        textColor=colors.HexColor('#34495e')
    )
    
    warning_style = ParagraphStyle(
        'WarningStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5,
        textColor=colors.HexColor('#e74c3c'),
        backColor=colors.HexColor('#fdf2e9'),
        borderPadding=5,
        borderColor=colors.HexColor('#f5b7b1'),
        borderWidth=1
    )
    
    # Story elements
    story = []
    
    # Title
    story.append(Paragraph("Reporte de Actores Detectados", title_style))
    
    # Date
    if detection_date is None:
        detection_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    story.append(Paragraph(f"Fecha de detección: {detection_date}", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Estadísticas de filtrado
    story.append(Paragraph("<b>Resumen de Detección:</b>", stats_style))
    
    stats_text = f"""
    • Total de actores detectados: {stats['with_names']}
    """
    
    for line in stats_text.strip().split('\n'):
        story.append(Paragraph(line, stats_style))
    
    story.append(Spacer(1, 10))
    
    # Actors table
    if filtered_actors:
        # Create table data
        table_data = [["ID Actor", "Nombre del Actor"]]
        
        # Mapear IDs originales para referencia
        original_ids_map = {}
        for new_id, (old_id, name) in enumerate(filtered_actors, start=1):
            old_original_id = actors_list[old_id-1][0] if old_id <= len(actors_list) else old_id
            table_data.append([f"Actor {new_id}", name])
        
        # Create table
        actor_table = Table(table_data, colWidths=[80, 250, 80])
        actor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        story.append(actor_table)
        story.append(Spacer(1, 40))
    
    # Add processed image if available
    if image_path and os.path.exists(image_path):
        try:
            story.append(Paragraph("Imagen Procesada:", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Add image to PDF (resize if necessary)
            img = Image(image_path, width=400, height=300)
            story.append(img)
            story.append(Spacer(1, 20))
        except Exception as e:
            story.append(Paragraph(f"Error al cargar la imagen: {str(e)}", styles['Normal']))
    
    # Footer information
    story.append(Spacer(1, 30))
    story.append(Paragraph("Smart Task", 
                          ParagraphStyle('Footer', 
                                        parent=styles['Normal'],
                                        fontSize=10,
                                        alignment=TA_CENTER,
                                        textColor=colors.gray)))
    
    # Build PDF
    doc.build(story)
    
    # Move buffer position to beginning
    buffer.seek(0)
    return buffer

def create_simple_actors_pdf(actors_list):
    """
    Create a simple PDF with just the actors list (filtrado y reenumerado)
    
    Args:
        actors_list: List of tuples (actor_id, actor_name)
    
    Returns:
        BytesIO buffer with PDF content
    """
    # Filtrar y reenumerar actores
    filtered_actors, stats = filter_and_renumber_actors(actors_list)
    
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Story elements
    story = []
    
    # Title
    story.append(Paragraph("Actores Detectados", styles['Heading1']))
    story.append(Spacer(1, 10))
    
    # Estadísticas
    if stats['without_names'] > 0:
        stats_msg = f"Detectados: {stats['with_names']}"
        story.append(Paragraph(stats_msg, styles['Normal']))
        story.append(Spacer(1, 10))
    
    # Actors list
    if filtered_actors:
        for new_id, name in filtered_actors:
            actor_text = f"Actor {new_id} - {name}"
            story.append(Paragraph(actor_text, styles['Normal']))
            story.append(Spacer(1, 5))
    else:
        story.append(Paragraph("No se detectaron actores", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    # Move buffer position to beginning
    buffer.seek(0)
    return buffer

def create_compact_actors_pdf(actors_list):
    """
    Create a very compact PDF with only the filtered and renumbered actors
    
    Args:
        actors_list: List of tuples (actor_id, actor_name)
    
    Returns:
        BytesIO buffer with PDF content
    """
    # Filtrar y reenumerar actores
    filtered_actors, _ = filter_and_renumber_actors(actors_list)
    
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom style for compact list
    compact_style = ParagraphStyle(
        'CompactStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        leftIndent=20
    )
    
    # Story elements
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CompactTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Actores Identificados", title_style))
    
    # Actors list
    if filtered_actors:
        for new_id, name in filtered_actors:
            actor_text = f"<b>Actor {new_id}:</b> {name}"
            story.append(Paragraph(actor_text, compact_style))
    else:
        story.append(Paragraph("No se identificaron actores", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    
    # Move buffer position to beginning
    buffer.seek(0)
    return buffer