from django.shortcuts import render_to_response
from django.template import RequestContext
import xml.etree.ElementTree as ET
import json

def read_contents(f):
    chunks = []
    for chunk in f:
        chunks.append(chunk)
    
    return "".join(chunks)

def parse_naf(f):
    contents = read_contents(f)
    obj = ET.fromstring(contents)
    return obj

def retrieve_text(naf):
    text_elem = naf.find('text')
    if text_elem is None:
        return {}
    
    result = []
    current_sentence = None
    for wf_elem in text_elem.findall('wf'):
        elem_id = wf_elem.get('id')
        sentence = int(wf_elem.get('sent'))
        paragraph = int(wf_elem.get('para'))
        offset = int(wf_elem.get('offset'))
        length = int(wf_elem.get('length'))
        word = wf_elem.text.strip()
        wf_obj = {
            "id": elem_id,
            "sentence": sentence,
            "paragraph": paragraph,
            "offset": offset,
            "length": length,
            "word": word,
            "sentence_end": False
        }
        if current_sentence is None:
            current_sentence = sentence
        else:
            if sentence != current_sentence:
                result[-1]["sentence_end"] = True
                current_sentence = sentence
        
        result.append(wf_obj)
        
    return result

def visualize(request):
    """Renders the NAF object"""
    naf = parse_naf(request.FILES['file'])
    text = retrieve_text(naf)
    tokens = json.dumps(text)
    return render_to_response('naf.html', {'text': text, 'tokens': tokens}, context_instance = RequestContext(request))
