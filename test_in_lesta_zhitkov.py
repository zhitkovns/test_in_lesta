from flask import Flask, render_template, request, redirect, url_for, flash, session
import math
from collections import Counter
import os
import string

app = Flask(__name__)
app.secret_key = 'dev-key'
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

uploaded_files = []

def process_text(text):
    """Очистка текста и разбиение на слова"""
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    return [word for word in text.split() if len(word) > 2] # Слишком малые слова отбрасываем

def calculate_stats(all_docs_words):
    """Расчет статистики с сортировкой"""
    # Расчет TF для каждого документа
    tfs = [Counter(doc_words) for doc_words in all_docs_words]
    
    # Расчет IDF
    total_docs = len(all_docs_words)
    idf = {}
    all_words = set(word for doc in all_docs_words for word in doc)
    
    for word in all_words:
        docs_with_word = sum(1 for doc in all_docs_words if word in doc)
        idf[word] = math.log(total_docs / (docs_with_word))
    
    # Формирование результатов
    results = []
    for doc_id, tf in enumerate(tfs):
        for word, count in tf.items():
            tf_val = count / sum(tf.values())
            results.append({
                'word': word,
                'tf': tf_val,
                'idf': idf[word],
                'tfidf': tf_val * idf[word],
                'doc_id': doc_id + 1 # Красивая нумерация документов
            })
    
    # Сортировка по IDF (убывание), затем по TF (убывание)
    return sorted(results, key=lambda x: (-x['idf'], -x['tf']))[:50]

@app.route('/', methods=['GET', 'POST'])
def uploads():
    session.pop('_flashes', None)

    global uploaded_files
    
    if request.method == 'POST':
        uploaded_files = []
        
        if 'files' not in request.files:
            flash('Выберите хотя бы один файл', 'error')
            return redirect(request.url)
            
        files = request.files.getlist('files')
        valid_files = []
        
        for file in files:
            if file.filename == '':
                continue   
            if not file.filename.endswith('.txt'):
                flash(f'Файл {file.filename} не является текстовым (.txt)', 'warning')
                continue
            try:
                content = file.read().decode('utf-8')
                if not content.strip():  # Если файл пустой или содержит только пробелы
                    flash(f'Файл {file.filename} пустой', 'warning')
                    continue
                words = process_text(content)
                valid_files.append({
                    'name': file.filename,
                    'content': content,
                    'words': words
                })
            except Exception as e:
                flash(f'Ошибка чтения файла {file.filename}: {str(e)}', 'error')
        
        if valid_files:
            uploaded_files = valid_files
            return redirect(url_for('results'))
        else:
            flash('Не удалось загрузить ни одного файла', 'error')
    
    return render_template('upload.html')

@app.route('/results')
def results():
    all_words = [file['words'] for file in uploaded_files]
    stats = calculate_stats(all_words)
    
    return render_template('result.html',
                         data=stats,
                         file_names=[f['name'] for f in uploaded_files])

@app.route('/clear')
def clear_data():
    global uploaded_files
    uploaded_files = []
    return redirect(url_for('uploads'))

if __name__ == '__main__':
    app.run(debug=True)