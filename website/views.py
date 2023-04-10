# from flask import Blueprint, render_template, request, flash, jsonify
# from flask_login import login_required, current_user
# from .models import Note
# from . import db
# import json

# views = Blueprint('views', __name__)


# @views.route('/', methods=['GET', 'POST'])
# @login_required
# def home():
#     if request.method == 'POST': 
#         note = request.form.get('note')#Gets the note from the HTML 

#         if len(note) < 1:
#             flash('Note is too short!', category='error') 
#         else:
#             new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note 
#             db.session.add(new_note) #adding the note to the database 
#             db.session.commit()
#             flash('Note added!', category='success')

#     return render_template("home.html", user=current_user)


# @views.route('/delete-note', methods=['POST'])
# def delete_note():  
#     note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
#     noteId = note['noteId']
#     note = Note.query.get(noteId)
#     if note:
#         if note.user_id == current_user.id:
#             db.session.delete(note)
#             db.session.commit()

#     return jsonify({})


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
                    line = line[:17] + ' DA ' + line[21:]
                elif residue_name == 'C':
                    line = line[:17] + ' DC ' + line[21:]
                elif residue_name == 'G':
                    line = line[:17] + ' DG ' + line[21:]
                elif residue_name == 'U':
                    line = line[:17] + ' DT ' + line[21:]
            new_file_contents += line

        new_file_name = 'converted_' + file.filename
        with open(new_file_name, 'w') as f:
            f.writelines(new_file_contents)

        # Return download link to user
        return render_template("home.html", user=current_user, download_link=new_file_name)

    return render_template("home.html", user=current_user)
