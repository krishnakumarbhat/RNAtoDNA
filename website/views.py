from flask import Blueprint, render_template, request, flash, send_file
from werkzeug.utils import secure_filename
import os
import uuid

from .utils.pdb_converter import ConversionOptions, convert_pdb_text_to_dna

views = Blueprint('views', __name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Basic abuse protection (no DB): limit upload sizes
MAX_UPLOAD_BYTES = 4 * 1024 * 1024  # 4 MB


def _safe_job_name(original: str) -> str:
    base = secure_filename(original) or "input.pdb"
    stem, ext = os.path.splitext(base)
    if ext.lower() != ".pdb":
        ext = ".pdb"
    return f"{stem}_{uuid.uuid4().hex}{ext}"


@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', category='error')
            return render_template("home.html")

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', category='error')
            return render_template("home.html")

        if file.filename.split('.')[-1].lower() != 'pdb':
            flash('Invalid file format. Only PDB files are allowed.', category='error')
            return render_template("home.html")

        # Options
        remove_o2prime = request.form.get('remove_o2prime') == 'on'
        h5_to_c7 = request.form.get('h5_to_c7') == 'on'
        options = ConversionOptions(remove_o2_prime=remove_o2prime, h5_to_c7=h5_to_c7)

        # Read file bytes with basic size guard
        file_bytes = file.read()
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            flash(f'File too large. Max size is {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.', category='error')
            return render_template("home.html")

        try:
            pdb_text = file_bytes.decode('utf-8', errors='replace')
        except Exception:
            flash('Could not read file as text.', category='error')
            return render_template("home.html")

        converted_text, stats = convert_pdb_text_to_dna(pdb_text, options=options)

        original_name = secure_filename(file.filename)
        out_name = f"converted_DNA_from_{os.path.splitext(original_name)[0]}.pdb"
        job_name = _safe_job_name(out_name)
        out_path = os.path.join(UPLOAD_FOLDER, job_name)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(converted_text)

        flash('Conversion successful! Your file is ready to download.', category='success')
        return render_template(
            "home.html",
            download_ready=True,
            download_filename=job_name,
            stats=stats,
            options={"remove_o2prime": remove_o2prime, "h5_to_c7": h5_to_c7},
        )

    return render_template("home.html")


@views.route('/preview/<filename>')
def preview_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if not os.path.exists(file_path):
        flash('File not found', category='error')
        return render_template("home.html")

    # Show only first N lines to keep response small
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    preview_lines = lines[:200]
    return render_template('preview.html', filename=filename, preview_lines=preview_lines, total_lines=len(lines))


@views.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    flash('File not found', category='error')
    return render_template("home.html")
