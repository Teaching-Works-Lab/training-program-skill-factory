import fitz
from curriculum import main

def test_extract_matrix_rejects_page_zero_before_open(tmp_path):
    source = tmp_path / "source.pdf"
    document = fitz.open()
    document.new_page()
    document.save(source)
    document.close()
    assert main(["extract-matrix", str(source), str(tmp_path / "out.json"), "--indicators", "1.1", "--page", "0"]) == 2
