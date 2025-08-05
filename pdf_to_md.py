# from reducto.reducto import Reducto
from pathlib import Path
from docling.document_converter import DocumentConverter
import os

# need API key
# def reducto_to_md():
#     client = Reducto()
#     upload = client.upload(file=Path("pdf_out/1.pdf"))
#     result = client.parse.run(
#         document_url=str(upload),
#         options={
#             "chunking": {
#                 "chunk_mode": "disabled",
#             }
#         },
#     )
#     return result

def docling_to_md(pdf_path):
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()

def process_all_pdfs():
    # Create docling_md directory if it doesn't exist
    os.makedirs("docling_md", exist_ok=True)
    
    # Get all PDF files from pdf_out directory
    pdf_dir = Path("pdf_out")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in pdf_out directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        
        # Convert PDF to markdown
        markdown_content = docling_to_md(str(pdf_file))
        
        # Create output filename (change .pdf to .md)
        output_filename = pdf_file.stem + ".md"
        output_path = Path("docling_md") / output_filename
        
        # Write markdown to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"Saved {output_filename}")
    
    print(f"All done! Processed {len(pdf_files)} files.")

# Run the batch processing
process_all_pdfs()