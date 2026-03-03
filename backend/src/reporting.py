
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os
import numpy as np
import time

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Professional Header with Logo/Title
        self.set_fill_color(30, 41, 59)  # Slate 800
        self.rect(0, 0, 210, 25, 'F')
        
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'CardioAware - Clinical grade ECG Analysis', 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.cell(0, 4, 'Automated AI Signal Extraction & Environmental Correlation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 116, 139) 
        self.cell(0, 10, f'Generated on {time.strftime("%Y-%m-%d %H:%M")} | Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(data, output_path):
    pdf = PDFReport()
    pdf.add_page()
    
    # 1. Patient / File Info
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, f"Analysis Report for: {data.get('filename', 'Unknown')}", ln=True)
    pdf.ln(2)
    
    # 2. Key Findings Summary (The "Health Message")
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, pdf.get_y(), 190, 25, 'F')
    pdf.set_xy(10, pdf.get_y() + 5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Clinical Summary Assessment:", ln=True, align='L')
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, data.get('recommendation', "No specific recommendation generated."), align='L')
    pdf.ln(10)
    
    # 3. Physiological Parameters
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Physiological Metrics:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(90, 7, f"Heart Rate: {data.get('heart_rate', 'N/A')} BPM", ln=0)
    pdf.cell(90, 7, f"Rhythm Classification: {data.get('condition', 'N/A')}", ln=1)
    pdf.cell(90, 7, f"AI Confidence: {data.get('confidence', 'N/A')}%", ln=0)
    pdf.cell(90, 7, f"Pattern Risk Level: {data.get('pattern_alert', data.get('risk_level', 'N/A'))}", ln=1)
    pdf.ln(5)

    # 4. Environmental Context (AQI)
    if 'AQI' in data:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "Environmental Context (Air Quality):", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(90, 7, f"Current AQI: {data.get('AQI', 'N/A')} ({data.get('AQI_status', 'N/A')})", ln=0)
        pdf.cell(90, 7, f"Location: {data.get('location', 'Detected via IP')}", ln=1)
        pdf.multi_cell(0, 6, f"Advisory: {data.get('AQI_recommendation', 'N/A')}")
        pdf.ln(5)

    # 5. Signal Visualization
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Extracted Lead I Trace (Digital Reconstruction)", ln=True)
    
    try:
        signal = data.get('signal', [])
        if signal and len(signal) > 20:
            plt.figure(figsize=(10, 3))
            plt.plot(signal, color='#dc2626', linewidth=0.8) # Medical Red/Pink style
            plt.title("Filtered ECG Signal (0.5-40Hz Bandpass)", fontsize=8)
            plt.grid(True, which='both', linestyle=':', linewidth=0.5, color='#cbd5e1')
            plt.axis('off')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            import uuid
            temp_filename = f"temp_plot_{uuid.uuid4().hex}.png"
            with open(temp_filename, "wb") as f:
                f.write(buf.getvalue())
            
            pdf.image(temp_filename, x=10, w=190)
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        else:
             pdf.cell(0, 10, "[Signal data unavailable for visualization]", ln=True)
    except Exception as e:
        pdf.cell(0, 10, f"Error generating signal plot: {str(e)}", ln=True)
    
    pdf.ln(5)

    # 6. Hospital Recommendations (Conditional)
    hospitals = data.get('hospitals', [])
    if hospitals and len(hospitals) > 0:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Nearby Cardiac Care Facilities", ln=True)
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 6, "Based on your current location and detected condition severity:", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        for i, hosp in enumerate(hospitals[:5]):
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, f"{i+1}. {hosp.get('name', 'Unknown')}", ln=True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 5, f"   Distance: {hosp.get('distance', 'N/A')} | Contact: {hosp.get('phone', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"   Address: {hosp.get('address', 'N/A')}", ln=True)
            pdf.ln(3)

    # 7. Disclaimer
    pdf.set_y(-45)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 4, "CLINICAL DISCLAIMER:", ln=True)
    pdf.set_font("Arial", '', 8)
    disclaimer = (
        "This report is generated by an AI assistant for educational and demonstration purposes. "
        "The ECG signal is extracted from a static image and may contain artifacts. "
        "Heart rate and condition classifications are strictly algorithmic estimates and do not constitute a medical diagnosis. "
        "Always consult a qualified cardiologist for medical advice."
    )
    pdf.multi_cell(0, 4, disclaimer)
    
    pdf.output(output_path)
    return output_path
