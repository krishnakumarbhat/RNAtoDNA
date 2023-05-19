from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', category='error')
            return render_template("home.html", user=current_user)

        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', category='error')
            return render_template("home.html", user=current_user)

        # Check if the file is a pdb file
        if file.filename.split('.')[-1].lower() != 'pdb':
            flash('Invalid file format. Only PDB files are allowed.', category='error')
            return render_template("home.html", user=current_user)

        # Generate a unique filename and save the file to the server
        filename = secure_filename(file.filename)
        new_file_name = 'converted_DNA_from' + filename
        file.save(new_file_name)

        # Perform RNA to DNA conversion and remove O2 lines
        with open(new_file_name, 'r') as f:
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
        with open(new_file_name, 'w') as f:
            f.writelines(new_file_contents)

        # Return download link to the user
        return render_template("home.html", user=current_user, download_link=new_file_name)

    return render_template("home.html", user=current_user)
