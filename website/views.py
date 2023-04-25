from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note
from . import db
import json

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

        # Save file to server
        file.save(file.filename)

        # Read file contents
        with open(file.filename, 'r') as f:
            file_contents = f.readlines()

        # Perform RNA to DNA conversion and create new PDB file
        new_file_contents = ''
        for line in file_contents:
            if line.startswith('ATOM'):
                residue_name = line[17:20].strip()
                if residue_name == 'A':
                    line = line[:77] + 'C' + line[78:80] + ' ' + line[81:87] + ' ' + line[88:]
                elif residue_name == 'C':
                    line = line[:77] + 'G' + line[78:80] + ' ' + line[81:87] + ' ' + line[88:]
                elif residue_name == 'G':
                    line = line[:77] + 'C' + line[78:80] + ' ' + line[81:87] + ' ' + line[88:]
                elif residue_name == 'U':
                    line = line[:77] + 'T' + line[78:80] + ' ' + line[81:87] + ' ' + line[88:]
            if line.endswith(' O  \n'):
                line = line[:77] + '  \n'
            new_file_contents += line

        # Save new file to server
        with open(file.filename.split('.')[0] + '_dna.pdb', 'w') as f:
            f.write(new_file_contents)

        flash('File converted successfully!', category='success')
        return render_template("home.html", user=current_user)

    return render_template("home.html", user=current_user)
