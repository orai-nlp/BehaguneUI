from django.shortcuts import render_to_response
from django.template import RequestContext
import xml.etree.ElementTree as ET
import json

def get_target_ids(element):
    references_element = element.find('references')
    if references_element is not None:
        return get_target_ids(references_element)
    
    else:
        span_element = element.find('span')
        targets = span_element.findall('target')
        
        return [target.get('id') for target in targets]

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
            "sentence_end": False,
            "is_entity": False
        }
        if current_sentence is None:
            current_sentence = sentence
        else:
            if sentence != current_sentence:
                result[-1]["sentence_end"] = True
                current_sentence = sentence
        
        result.append(wf_obj)
        
    return result

def add_terms(naf, tokens):
    terms_element = naf.find('terms')
    if terms_element is None:
        return tokens
    
    wf_id_to_term = {}
    
    for term_element in terms_element.findall('term'):
        target_id = get_target_ids(term_element)[0]
        term_id = term_element.get('id')
        term_type = term_element.get('type')
        lemma = term_element.get('lemma')
        simple_pos = term_element.get('pos')
        pos = term_element.get('morphofeat')
        
        wf_id_to_term[target_id] = {
            "term_id": term_id,
            "type": term_type,
            "lemma": lemma,
            "simple_pos": simple_pos,
            "pos": pos
        }
    
    result = []
    for token in tokens:
        term = wf_id_to_term.get(token['id'])
        if term is not None:
            token.update(term)
            
        result.append(token)
        
    return result

def add_entities(naf, tokens):
    entities_element = naf.find('entities')
    if entities_element is None:
        return tokens
        
    term_id_to_entity = {}
        
    for entity_element in entities_element.findall('entity'):
        target_ids = get_target_ids(entity_element)
        entity = {
            "entity_id": entity_element.get('id'),
            "entity_type": entity_element.get('type')
        }
        for target_id in target_ids:
            term_id_to_entity[target_id] = entity
        
    result = []
    for token in tokens:
        term_id = token['term_id']
        if term_id in term_id_to_entity:
            entity = term_id_to_entity[term_id]
            token.update(entity)
            token['is_entity'] = True
            
        result.append(token)

    return result

def visualize(request):
    """Renders the NAF object"""
    naf = parse_naf(request.FILES['file'])
    tokens = retrieve_text(naf)
    tokens = add_terms(naf, tokens)
    tokens = add_entities(naf, tokens)
    
    return render_to_response('naf.html', {'tokens': tokens}, context_instance = RequestContext(request))
