from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

db_config = {
    'host': '10.0.0.101',
    'user': 'OAG-workstation',
    'password': 'EB8470p',
    'database': 'utleiedata'
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    avg_rent = 0
    # Use request.form directly so we can use .getlist() in the template
    form = request.form
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM data WHERE 1=1"
        params = []

        # --- MULTIPLE SELECTION: BOLIGTYPE ---
        boligtyper = request.form.getlist('Boligtype')
        if boligtyper:
            # Creates placeholders: IN (%s, %s, %s)
            placeholders = ', '.join(['%s'] * len(boligtyper))
            query += f" AND Boligtype IN ({placeholders})"
            params.extend(boligtyper)

        # --- TEXT FILTERS ---
        for field in ['Etasje', 'Energimerke', 'Poststed', 'Postnummer']:
            val = request.form.get(field)
            if val and val.strip():
                query += f" AND {field} LIKE %s"
                params.append(f"%{val}%")

        # --- EXACT FILTERS ---
        for field in ['AntallSoverom', 'AntallRom']:
            val = request.form.get(field)
            if val and val.strip():
                query += f" AND {field} = %s"
                params.append(val)

        # --- PARKERING / BALKONG: "Begge" means "don't filter" ---
        for field in ['Parkering', 'Balkong']:
            val = request.form.get(field)
            if val and val.strip() and val != 'Begge':
                query += f" AND {field} = %s"
                params.append(val)

        # --- RANGE FILTERS ---
        for field in ['ArealPrimerrom', 'Tomteareal']:
            f_min = request.form.get(f"{field}_min")
            f_max = request.form.get(f"{field}_max")
            if f_min:
                query += f" AND {field} >= %s"
                params.append(f_min)
            if f_max:
                query += f" AND {field} <= %s"
                params.append(f_max)

        # --- STATUS ---
        status = request.form.get('status_filter')
        if status == 'Ukjent':
            query += " AND (UtleidMerke IS NULL OR UtleidMerke = '')"
        elif status == 'Utleid':
            query += " AND (UtleidMerke IS NOT NULL AND UtleidMerke != '')"

        # --- DATE RANGE FILTER ---
        date_from = request.form.get('SistEndretDT_min')
        date_to = request.form.get('SistEndretDT_max')
        if date_from:
            query += " AND SistEndretDT >= %s"
            params.append(date_from)
        if date_to:
            query += " AND SistEndretDT <= %s"
            params.append(date_to + " 23:59:59")  # Include the entire end date

        cursor.execute(query, params)
        results = cursor.fetchall()

        print(query)
        if results:
            total_rent = sum(row['Leiepris'] for row in results if row['Leiepris'])
            avg_rent = total_rent / len(results)

        cursor.close()
        conn.close()

    return render_template('index.html', results=results, form=form, avg_rent=avg_rent)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
