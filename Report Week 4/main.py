from flask import Flask, render_template_string
import sqlite3, os

app = Flask(__name__)
DB_FILE = 'pageviews.db'

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pageviews (
                site TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

def increment_view(site):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM pageviews WHERE site = ?', (site,))
    row = cursor.fetchone()
    if row:
        cursor.execute('UPDATE pageviews SET count = count + 1 WHERE site = ?', (site,))
    else:
        cursor.execute('INSERT INTO pageviews (site, count) VALUES (?, 1)', (site,))
    conn.commit()
    conn.close()

def get_views(site):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM pageviews WHERE site = ?', (site,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

@app.route('/page/<site>')
def page(site):
    increment_view(site)
    count = get_views(site)
    return render_template_string("""
        <h1>{{ site | capitalize }} page</h1>
        <p>Lượt xem: {{ count }}</p>
        <button onclick="window.location.reload()">Refresh</button>
    """, site=site, count=count)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
