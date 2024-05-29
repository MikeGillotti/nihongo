from flask import Flask, render_template, request
import pandas as pd
from sudachipy import dictionary
from pykakasi import kakasi

app = Flask(__name__)

# Load data from CSV
data = pd.read_csv('static/sentence.csv')
navigation_data = pd.read_csv('static/navigation.csv')  # Load the navigation CSV

# Extract category names from the navigation CSV columns
category_names = navigation_data.columns.tolist()

# Initialize Sudachi tokenizer
tokenizer = dictionary.Dictionary().create()

# Initialize Kakasi for converting Kanji to Hiragana
kks = kakasi()
kks.setMode('J', 'H')  # Japanese Kanji to Hiragana
conv = kks.getConverter()

def tokenize_and_add_furigana(sentence):
    tokens = tokenizer.tokenize(sentence)
    token_info = []
    for token in tokens:
        surface = token.surface()
        reading = conv.do(surface) if token.reading_form() else surface
        token_info.append(f"{surface}({reading})" if surface != reading else surface)
    return ' '.join(token_info)

@app.route('/', methods=['GET'])
def index():
    return render_template('navigation.html', categories=category_names)

@app.route('/category/<category>', methods=['GET'])
def category_view(category):
    if category not in category_names:
        return "Category not found"

    page = int(request.args.get('page', 1))
    per_page = 50

    # Filter data by category
    filtered_navigation = navigation_data[navigation_data[category] == 1]
    words = filtered_navigation['Word'].tolist()
    pattern = '|'.join(words)
    # Filter sentences by words
    filtered_sentences = data[data['Sentence'].str.contains(pattern, case=False, na=False)]

    total_rows = len(filtered_sentences)
    total_pages = (total_rows // per_page) + (1 if total_rows % per_page != 0 else 0)

    start = (page - 1) * per_page
    end = start + per_page
    filtered_sentences = filtered_sentences.iloc[start:end]
    row_data = [
        {k: tokenize_and_add_furigana(v) if k != 'Sentence' else v for k, v in row.items() if pd.notna(v)}  # Filter out NaN values
        for row in filtered_sentences.drop(columns=filtered_sentences.columns[0]).to_dict(orient='records')
    ]

    return render_template('index.html', row_data=row_data, current_page=page, total_pages=total_pages, category=category)

if __name__ == '__main__':
    app.run(debug=True)
