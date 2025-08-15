from flask import Flask, render_template, request, redirect, url_for
import stanza
import os
import numpy
import re
from natsort import natsorted

import logging
logging.basicConfig(level=logging.INFO)

model_dir = os.environ.get("STANZA_RESOURCES_DIR", "./stanza_resources")
sv_model_path = os.path.join(model_dir, "sv")

# Ladda modellen endast om den inte finns
if not os.path.exists(sv_model_path):
    print("Laddar ner svensk modell...")
    stanza.download("sv", model_dir=model_dir)

nlp = stanza.Pipeline(lang='sv', processors='tokenize,pos', model_dir=model_dir)

app = Flask(__name__)

POS_MAPPING = {
    "ADJ": "adjektiv",
    "ADV": "adverb",
    "VERB": "verb",
    "PRON": "pronomen",
    "FORBIDDEN": "forbidden"
}

default_forbidden_words = ["aldrig", "alldeles", "allra", "alltid", "andades", "aningen", "att", "bara", "blick", "borde", "bra", "båda", "både", "bör", "började", "börjar", "definitivt", "dessutom", "direkt", "dock", "då", "där", "egentligen", "enormt", "ens", "faktiskt", "fantastiskt", "fast", "fastän", "fortfarande", "fram", "förmodligen", "försiktigt", "förstås", "försöker", "försökte", "förvisso", "ganska", "gjorde", "grimasera", "gråt", "grät", "gärna", "gör", "hade", "handen", "hans", "har", "hela", "heller", "helt", "hennes", "håller", "på", "här", "inombords", "intill", "ju", "just", "kan", "kanske", "knappt", "kom", "kunde", "kände", "kändes", "känner", "känns", "liksom", "lite", "log", "man", "med", "medan", "men", "mycket", "måste", "märker", "märkte", "möjligen", "ner", "nickade", "nog", "nu", "nu", "någon", "någonsin", "nämligen", "när", "närmast", "nästan", "oavsett", "också", "oerhört", "ofta", "om", "otroligt", "plötsligt", "precis", "redan", "riktigt", "samtidigt", "satte", "sedan", "ser", "sin", "själv", "ska", "skrattade", "skrattade", "till", "skulle", "skulle", "kunna", "slutade", "slutar", "snart", "som", "startade", "startar", "ställde", "ställer", "ständigt", "stönade", "suckade", "så", "sådan", "såg", "såsom", "säkert", "sällan", "sätter", "tillsynes", "tittade", "tittar", "troligen", "troligtvis", "trots", "tvingade", "tårar", "ungefär", "upp", "uppenbarligen", "ut", "utan", "utav", "varsin", "varsitt", "verkade", "verkar", "verkligen", "viktigt", "väl", "väldigt"]

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        content = file.read().decode('utf-8')
        words = re.split(r'[,\s]+', content)
        forbidden_words = [word.strip().lower() for word in words if word.strip()]
        forbidden_words = natsorted(list(set(forbidden_words)))

        return render_template(
         'index.html',
         result='',
         stats={},
         forbidden_words=', '.join(forbidden_words))
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    result_html = ""
    stats = {}
    content = request.form.get('forbidden_words', '')
    if content == '':
        forbidden_words = default_forbidden_words
    else:
        words = re.split(r'[,\s]+', content)
        forbidden_words = [word.strip().lower() for word in words if word.strip()]
        forbidden_words = natsorted(list(set(forbidden_words)))

    # logging.info(f"forbidden_words:{forbidden_words}")
    if request.method == 'POST':
        input_text = request.form.get('input_text', '')
        selected_class = request.form.get('show_class', '')
        doc = nlp(input_text)

        highlighted = []
        class_count = 0
        total_words = 0

        lines = input_text.splitlines()

        for line in lines:
            if not line.strip():
                highlighted.append("<br>")
                continue
            doc_line = nlp(line)
            line_highlighted = []
            for sent in doc_line.sentences:
                for word in sent.words:
                    total_words += 1
                    token_text = word.text
                    if selected_class == 'forbidden':
                        css_class = POS_MAPPING.get('FORBIDDEN')
                        if token_text.lower() in forbidden_words:
                            token_text = f'<span class="{css_class}">{token_text}</span>'
                            class_count += 1
                    else:
                        css_class = POS_MAPPING.get(word.upos)
                        if css_class == selected_class:
                            token_text = f'<span class="{css_class}">{token_text}</span>'
                            class_count += 1

                    line_highlighted.append(token_text)
            highlighted.append(" ".join(line_highlighted))
        result_html = "<br>".join(highlighted)
        stats = {
            "count": class_count,
            "percentage": round((class_count / total_words) * 100, 2) if total_words else 0.0,
            "total": total_words
        }
    return render_template(
         'index.html', 
         result=result_html, 
         stats=stats,
         forbidden_words=', '.join(forbidden_words))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7860)

