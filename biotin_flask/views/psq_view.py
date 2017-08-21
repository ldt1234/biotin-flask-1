"""Reformats HTML reports generated by the PSQ Assay Design Software and outputs
a concise summary in a single CSV file

This module parses HTML files uploaded by the user for primer design information,
reorganizes this information and writes this information into a csv file

Either a single HTML file or multiple HTML files can be
provided.
"""

import os, io, csv, StringIO
from flask import render_template, request, flash, make_response
from werkzeug import secure_filename

from biotin_flask import app
from biotin_flask.models.utils import ParsePsy

__author__ = 'Eric Zhou'
__copyright__ = 'Copyright (C) 2017, EpigenDx Inc.'
__credits__ = ['Eric Zhou']
__version__ = '0.0.1'
__status__ = 'Production'

@app.route('/misc/psq', methods=['GET', 'POST'])
def psq():

    """Handle GET or POST requests to the psq URL.

    Form args:
        f:      (File) list of HTML files uploaded by user

    Returns:
        A CSV file.

    """

    # Render an empty form for GET request
    if request.method == 'GET':
        return render_template('psq/form.html')

    # Otherwise validate the form on a POST request and process uploaded files
    f = request.files.getlist('html')

    if not f[0]:
        flash('A reqired field is missing', 'error')
        return render_template('psq/form.html')

    # Throw error if any file does not have .html extension
    filefront, extension, filename = '', '', ''
    for file in f:
        filename = secure_filename(file.filename)
        filefront, extension = os.path.splitext(filename)
        if not extension == '.html':
            flash('Only .html files are allowed.', 'error')
            return render_template('psq/form.html')

    # Begin cleaning and parsing the html file
    clean = []
    output = []
    p = ParsePsy() # ParsePsy is a class Eric wrote in utils.py that parses the html file
    for index, file in enumerate(f):
        # Convert file into string
        html = ''
        for line in file:
            html = html + line

        # Let ParsePsy() clean the html
        p.feed(html)
        clean.append(p.data)
        # Reset ParsePsy()
        p.data = []
        p.close()

        # Begin parsing for data
        data = []
        counter = 0
        neighbor = 0

        for item in clean[index]:
            if neighbor > 0:
                data.append(item)
                neighbor -= 1
                continue

            if counter == 0:
                # Look for Assay Name
                if item.replace(' ', '') == 'AssayName':
                    neighbor = 1
                    counter += 1

            elif counter == 1:
                # Look for Score:
                if item.split()[0] == 'Score:':
                    data.append(item.split()[1])
                    counter += 1

            elif counter == 2:
                # Look for F1 Primer
                if item == 'F1':
                    neighbor = 4
                    counter += 1

            elif counter == 3:
                # Look for R1 Primer
                if item == 'R1':
                    neighbor = 4
                    counter+=1

            elif counter == 4:
                # Look for S1 Primer
                if item == 'S1':
                    neighbor = 4
                    counter += 1

            elif counter == 5:
                # Look for Amplicon Length
                if item.replace(' ', '') == 'Ampliconlength':
                    neighbor = 1
                    counter += 1

            elif counter == 6:
                # Look for Amplicon %GC
                if item.replace(' ', '') == 'Amplicon\r\n%GC':
                    neighbor = 1
                    counter += 1

            elif counter == 7:
                break

        if len(data) != 16:
            flash('The uploaded file(s) are not in the correct format', 'error')
            return render_template('psq/form.html')
        output.append(data)

    # Prepare csv printer
    dest = StringIO.StringIO()
    writer = csv.writer(dest)

    # Print header
    writer.writerow( ["NGS#", "Assay ID", "Length", "Tm", "GC%", "Amplicon GC%",
                      "Amplicon size", "Assay Design Score", "Amplicon coordinates (GRCm38/mm10)",
                      "Strand", "# CpG", "# SNP", "Primer ID", "Primer Sequences", "Ta",
                      "Mg2+", "Note"] )

    # Loop through output
    row = [''] * 17
    for file in output:
        row[1] = file[0]
        row[2] = file[3]
        row[3] = file[4]
        row[4] = file[5]
        row[5] = file[15]
        row[6] = file[14]
        row[7] = file[1]
        row[13] = file[2]
        writer.writerow( row )
        row = [""] * 17
        row[2] = file[7]
        row[3] = file[8]
        row[4] = file[9]
        row[13] = file[6]
        writer.writerow(row)
        row = [""] * 17
        row[2] = file[11]
        row[3] = file[12]
        row[4] = file[13]
        row[13] = file[10]
        writer.writerow(row)
        row = [""] * 17

    # Make response
    response = make_response(dest.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=result.csv"
    return response