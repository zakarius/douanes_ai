from fastapi import APIRouter, UploadFile, File
import pdfplumber
import io

router = APIRouter()


@router.post("/extract-pdf-tables")
async def extract_pdf_tables(file: UploadFile = File(...)):
    # Read the uploaded PDF file
    pdf_data = await file.read()
    tables = []

    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        # Extract tables from the PDF
        for page in pdf.pages:
            extracted_tables = page.extract_tables()
            for table in extracted_tables:
                for row in table:
                    tables.append(row)

    return tables
