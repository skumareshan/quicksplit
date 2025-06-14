from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
import pytesseract
import os
import re
from werkzeug.utils import secure_filename
from pillow_heif import register_heif_opener
register_heif_opener()


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- OCR & Parsing Logic ---
def parse_items(text):
    items = []
    for line in text.split('\n'):
        match = re.search(r'(.+?)\s+\$?(\d+\.\d{2})$', line.strip())
        if match:
            item = match.group(1).strip()
            price = float(match.group(2))
            items.append({'item': item, 'price': price})
    return items

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['receipt']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image = Image.open(filepath).convert('RGB')
            text = pytesseract.image_to_string(image)
            items = parse_items(text)

            return render_template('assign.html', items=items)
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    people = {}
    total = 0
    for key in request.form:
        if key.startswith('item_'):
            index = key.split('_')[1]
            item_name = request.form[f'item_{index}']
            price = float(request.form[f'price_{index}'])
            names = request.form[f'names_{index}']

            if names.strip().lower() == 'ignore':
                continue

            name_list = [name.strip() for name in names.split(',') if name.strip()]
            split_price = price / len(name_list)
            total += price
            for name in name_list:
                people.setdefault(name, []).append({'item': item_name, 'price': split_price})

    totals = {name: sum(i['price'] for i in items) for name, items in people.items()}
    return render_template('result.html', totals=totals, total=total)

if __name__ == '__main__':
    app.run(debug=True)
