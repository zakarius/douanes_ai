from fastapi import APIRouter, UploadFile, File
import pdfplumber
import io

router = APIRouter()


@router.post("/extract-pdf-tables")
async def extract_pdf_tables(file: UploadFile = File(...)):
    pdf_data = await file.read()
    tables = []
    with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
        for page in pdf.pages:
            extracted_tables = page.extract_tables()
            for table in extracted_tables:
                for row in table:
                    cells = []
                    if row.count(None) <= 1:
                        for cell in row:
                            if cell is None:
                                cells.append("")
                            else:
                                cells.append(cell)
                        tables.append(cells)

    return tables
