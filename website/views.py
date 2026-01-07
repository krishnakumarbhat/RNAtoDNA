from flask import Blueprint, render_template, request, flash, send_file
from werkzeug.utils import secure_filename
import os
import tempfile

views = Blueprint('views', __name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', category='error')
            return render_template("home.html")

        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', category='error')
            return render_template("home.html")

        # Check if the file is a pdb file
        if file.filename.split('.')[-1].lower() != 'pdb':
            flash('Invalid file format. Only PDB files are allowed.', category='error')
            return render_template("home.html")

        # Generate a unique filename and save the file to the server
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = 'converted_DNA_from_' + filename
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        file.save(input_path)

        # Perform RNA to DNA conversion and remove O2 lines
        with open(input_path, 'r') as f:
            file_contents = f.readlines()

        new_file_contents = ''
        for line in file_contents:
            if line.startswith('ATOM'):
                residue_name = line[17:20].strip()
                if residue_name == 'A':
                    line = line[:17] + ' DA ' + line[21:]
                elif residue_name == 'C':
                    line = line[:17] + ' DC ' + line[21:]
                elif residue_name == 'G':
                    line = line[:17] + ' DG ' + line[21:]
                elif residue_name == 'U':
                    line = line[:17] + ' DT ' + line[21:]

                # Remove O2' lines
                if line[13:16].strip() == "O2'":
                    continue

                # Replace H5 with C7
                if line[13:16].strip() == 'H5':
                    line = line[:13] + 'C7 ' + line[16:]

            new_file_contents += line

        # Save the converted DNA file
        with open(output_path, 'w') as f:
            f.writelines(new_file_contents)

        # Clean up input file
        os.remove(input_path)

        flash('Conversion successful! Your file is ready to download.', category='success')
        return render_template("home.html", download_ready=True, download_filename=output_filename)

    return render_template("home.html")


@views.route('/download/<filename>')
def download_file(filename):
    """Download the converted file"""
    file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash('File not found', category='error')
    return render_template("home.html")
