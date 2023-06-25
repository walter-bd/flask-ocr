import io
import os
import numpy as np
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import img2pdf
from werkzeug.wsgi import wrap_file
from flask import Flask, request, redirect, url_for, render_template, send_file
from config import Config



# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)
# Initialize PaddleOCR with the desired language(s)
ocr = PaddleOCR(lang="es", use_gpu=True)     

from PyPDF2 import PaperSize
A4_w = PaperSize.A4.width
A4_h = PaperSize.A4.height

def reduce_size(pdf_bytes):
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    pdf_writer = PdfWriter()
    # We only have one page, so we directly access it
    for page in pdf.pages:
        h = float(page.mediabox.height)
        w = float(page.mediabox.width)
        scale_factor = min(A4_h/h, A4_w/w)
        page.scale_by(scale_factor)
        page.compress_content_streams()
        pdf_writer.add_page(page)
    pdf_writer.add_metadata(pdf.metadata)
    with io.BytesIO() as output_file:
        pdf_writer.write(output_file)
        output_file.seek(0)
        return output_file.getvalue()
    



def ocr_pdf(pdf_bytes):
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(pdf.pages)
    pdf_writer = PdfWriter()
    text_page = {}
    image_size = {}
    # Loop through each page of the PDF
    for i in range(num_pages):
        # Convert the current page to an image
        images = convert_from_bytes(pdf_bytes, first_page=i+1, last_page=i+1)
        box = pdf.pages[i].mediabox
        height = box.height
        width = box.width        
        # Since we're only converting one page at a time, there will only be one image in the list
        image = images[0]

        output = ocr.ocr(np.asarray(image))
        image_size[i] = image.size
        text_page[i] = []
        for item in output[0]:
            if item[1][1] > 0.85:
                text_page[i].append([item[0][3] , str(item[1][0]).lower(), item[0][0][1] - item[0][3][1]])
        
        # Save the image to a BytesIO object
        byteIO = io.BytesIO()
        image.save(byteIO, format='jpeg')

        # Convert the BytesIO object to a PDF
        with io.BytesIO() as f:
            f.write(img2pdf.convert([byteIO.getvalue()]))
            f.seek(0)
            pdf_reader = PdfReader(f)

            # We only have one page, so we directly access it
            page = pdf_reader.pages[0]
            packet = io.BytesIO()
            conversion_width = page.mediabox.width/image_size[i][0]
            conversion_height = page.mediabox.height/image_size[i][1]
            can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
            for text in text_page[i]:
                invisible_text = text[1]
                # Set the text color to white with 0 opacity (i.e. completely invisible)
                can.setFillColorRGB(1, 1, 1, 0)
                # Write the text to the canvas
                can.setFont("Helvetica", abs(int(float(text[2])*float(conversion_height)*0.75)))
                can.drawString(float(text[0][0])*float(conversion_width), float(page.mediabox.height) - float(text[0][1])*float(conversion_height), invisible_text)
            can.save()
            packet.seek(0)
            text_pdf = PdfReader(packet)
            page.merge_page(text_pdf.pages[0])
            page.scale_to(width=float(width),height=float(height))
            page.compress_content_streams()
            pdf_writer.add_page(page)
        print(f"Page number {i} of {num_pages}")
    pdf_writer.add_metadata(pdf.metadata)
    # Save the output PDF file
    with io.BytesIO() as output_file:
        pdf_writer.write(output_file)
        output_file.seek(0)
        return output_file.getvalue()


# # Define a function to perform OCR on a PDF and add the text to each page
# def ocr_pdf(pdf_bytes):
#     # Convert the PDF bytes to images and extract text from each page using PaddleOCR
#     images = convert_from_bytes(pdf_bytes)
#     bytes_images = []
#     metadata = {}
#     text_page = {}
#     pdf_writer = PdfWriter()
#     image_size = {}

#     for i, image in enumerate(images):
#         output = ocr.ocr(np.asarray(image))
#         image_size[i] = image.size
#         text_page[i] = []
#         for item in output[0]:
#             if item[1][1] > 0.85:
#                 text_page[i].append([item[0][3] , str(item[1][0]).lower(), item[0][0][1] - item[0][3][1]])
#         byteIO = io.BytesIO()
#         print("page " + i)
#         image.save(byteIO, format='PNG')
#         bytes_images.append(byteIO.getvalue())

#     # Convert the images to a PDF and add the extracted text to each page
#     with io.BytesIO() as f:
#         f.write(img2pdf.convert(bytes_images))
#         f.seek(0)
#         pdf_writer = PdfWriter()
#         pdf_reader = PdfReader(f)

#         for i in range(len(pdf_reader.pages)):
#             page = pdf_reader.pages[i]
#             packet = io.BytesIO()
#             conversion_width = page.mediabox.width/image_size[i][0]
#             conversion_height = page.mediabox.height/image_size[i][1]
#             can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
#             for text in text_page[i]:
#                 invisible_text = text[1]
#                 # Set the text color to white with 0 opacity (i.e. completely invisible)
#                 can.setFillColorRGB(1, 1, 1, 0)
#                 # Write the text to the canvas
#                 can.setFont("Helvetica", abs(int(text[2]*conversion_height*0.75)))
#                 can.drawString(text[0][0]*conversion_width, page.mediabox.height - text[0][1]*conversion_height, invisible_text)
#             can.save()
#             packet.seek(0)
#             text_pdf = PdfReader(packet)
#             page.merge_page(text_pdf.pages[0])
#             pdf_writer.add_page(page)

#         # Save the output PDF file
#         with io.BytesIO() as output_file:
#             pdf_writer.write(output_file)
#             output_file.seek(0)
#             return output_file.getvalue()

# Define a function to render the upload form
@app.route('/resizeA4', methods=['POST'])
def resizeA4():
    # Check if a file was uploaded
    if 'file' not in request.files:
        print('No file uploaded')
        return redirect(request.url)

    file = request.files['file']

    # Check if the file is a PDF
    if file.filename.split('.')[-1] != 'pdf':
        print('Only PDF files are allowed')
        return redirect(request.url)

    file_contents = file.read()
    reduced_pdf = reduce_size(file_contents)
    buffer = io.BytesIO(reduced_pdf)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='reduced.pdf', mimetype="application/pdf")
    
    

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    # Check if a file was uploaded
    if 'file' not in request.files:
        print('No file uploaded')
        return redirect(request.url)

    file = request.files['file']

    # Check if the file is a PDF
    if file.filename.split('.')[-1] != 'pdf':
        print('Only PDF files are allowed')
        return redirect(request.url)

    file_contents = file.read()
    print("OCR THE PDF")
    processed_pdf = ocr_pdf(file_contents)
    buffer = io.BytesIO(processed_pdf)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='processed.pdf', mimetype="application/pdf")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
