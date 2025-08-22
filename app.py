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

default_forbidden_words = ["aldrig", "alldeles", "allra", "alltid", "andades", "aningen", "att", "både", "bara", "blick", "bör", "borde", "började", "börjar", "bra", "då", "där", "definitivt", "dessutom", "direkt", "dock", "egentligen", "en aning", "en stund", "enormt", "ens", "ett tag", "faktiskt", "fantastiskt", "fast", "fastän", "för övrigt", "förmodligen", "försiktigt", "försöker", "försökte", "förstås", "fortfarande", "förvisso", "fram", "ganska", "gärna", "gjorde", "gör", "gråt", "grät", "grimasera", "hade", "håller på", "handen", "har", "här", "hela", "heller", "helt", "höll på", "i ordning", "i princip", "inombords", "intill", "ju", "just", "kan", "kände", "kändes", "känner", "känns", "kanske", "knappt", "kom", "kommer att", "kunde", "liksom", "lite", "log", "märker", "märkte", "måste", "med", "medan", "men", "möjligen", "mycket", "någonsin", "nämligen", "när", "närmast", "nästan", "ner", "nickade", "nog", "nu", "nu", "oavsett", "och så", "också", "oerhört", "ofta", "om", "otroligt", "plötsligt", "precis", "redan", "riktigt", "så", "så som", "sådan", "såg", "såg ut", "säkert", "sällan", "samtidigt", "såsom", "satte", "sätter", "sedan", "ser", "ser ut", "själv", "ska", "skakade på huvudet", "skrattade", "skrattade till", "skulle", "skulle kunna", "slutade", "slutar", "snart", "som", "som om", "ställde", "ställer", "ständigt", "startade", "startar", "stönade", "suckade", "tårar", "till slut", "tillsynes", "tittade", "tittar", "troligen", "troligtvis", "trots", "tvingade", "ungefär", "upp", "uppenbarligen", "ut", "utan", "utav", "vad menar du", "väl", "väldigt", "verkade", "verkar", "verkligen", "viktigt"]


def highlight_forbidden(text, forbidden_phrases, css_class):
    """
    text: str, den text som ska analyseras
    forbidden_phrases: list[str], både enstaka ord och begrepp (från CSV)
    css_class: CSS-klassen för highlight
    """
    # rensa och sortera så längsta begrepp kommer först
    forbidden_clean = [p.strip().lower() for p in forbidden_phrases if p.strip()]
    forbidden_clean.sort(key=len, reverse=True)

    highlighted_text = text
    total_matches = 0

    for phrase in forbidden_clean:
        # gör regex som matchar hela frasen som ord (case-insensitive)
        pattern = r'\b' + re.escape(phrase) + r'\b'

        # använd lambda för att bevara original-casing i texten
        def repl(match):
            nonlocal total_matches
            total_matches += 1
            return f'<span class="{css_class}">{match.group(0)}</span>'

        highlighted_text = re.sub(pattern, repl, highlighted_text, flags=re.IGNORECASE)

    return highlighted_text, total_matches


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        content = file.read().decode('utf-8')
        words = re.split(r'[\n]+', content)
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
        words = re.split(r'[,]+', content)
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

        doc = nlp(input_text)
        # räkna ord och meningar
        num_sentences = len(doc.sentences)
        num_words = sum(1 for sent in doc.sentences for w in sent.words if w.upos != "PUNCT")
        num_long_words = sum(1 for sent in doc.sentences for w in sent.words if w.upos != "PUNCT" and len(w.text) > 6)

        if num_sentences > 0 and num_words > 0:
            lix = (num_words / num_sentences) + (100 * num_long_words / num_words)
        else:
            lix = 0

        for line in lines:
            if not line.strip():
                highlighted.append("<br>")
                continue
            doc_line = nlp(line)
            total_words += sum(
                1 for sent in doc_line.sentences for w in sent.words if w.upos != "PUNCT"
            )
            line_highlighted = []
            if selected_class == 'forbidden':
                line_text = " ".join([w.text for s in doc_line.sentences for w in s.words])
                highlighted_line, n = highlight_forbidden(line_text, forbidden_words, POS_MAPPING['FORBIDDEN'])
                highlighted.append(highlighted_line)
                class_count += n
            else:
                # din vanliga loop för adjektiv/verb osv.
                for sent in doc_line.sentences:
                    for word in sent.words:
                        token_text = word.text
                        css_class = POS_MAPPING.get(word.upos)
                        if css_class == selected_class:
                            token_text = f'<span class="{css_class}">{token_text}</span>'
                            class_count += 1
                        line_highlighted.append(token_text)
                highlighted.append(" ".join(line_highlighted))
        result_html = "<br>".join(highlighted)
        stats = {
            "count": class_count,
            "percentage": round((class_count / total_words) * 100, 1) if total_words else 0.0,
            "total": total_words,
            "lix": round(lix)
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

