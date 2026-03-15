import shutil
from pathlib import Path

def zip_pdf_directory(directory:Path, file_name:str)->Path:
    if not directory.exists() or not directory.is_dir:
        raise FileNotFoundError(f"The directory {directory} does not exist.")
    zip_path = shutil.make_archive(base_name=str(directory), format="zip", root_dir=directory)
    return Path(zip_path)

