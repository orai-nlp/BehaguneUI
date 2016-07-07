class Node:
    def __init__(self, elem_id, label, **kwargs):
        self.elem_id = elem_id
        self.label = label
        self.name = "({0}) {1}".format(elem_id, label)
        self.parent = kwargs.get('parent', None)
        self.children = kwargs.get('children', [])
        
    def to_dict(self):
        result = { "name": self.name }
        if self.parent is None:
            result['parent'] = None
        else:
            result['parent'] = self.parent.name
        result['children'] = [child.to_dict() for child in self.children]
        result['level'] = '#008AB8'
        if len(self.children) > 0:
            result['level'] = '#FFF'
        
        return result
    
def get_tokens_per_term_id(tokens):
    result = {}
    for token in tokens:
        result[token['term_id']] = token
        
    return result

def parse_tree_element(tree_element, tokens_per_term_id):
    """Parses a tree element in the NAF format to a Python dictionary"""
    
    nodes_labels = {}
    for nt_element in tree_element.findall('nt'):
        elem_id = nt_element.get('id')
        elem_label = nt_element.get('label')
        nodes_labels[elem_id] = elem_label
        
    for t_element in tree_element.findall('t'):
        elem_id = t_element.get('id')
        span_element = t_element.find('span')
        target_element = span_element.find('target')
        term_id = target_element.get('id')
        token = tokens_per_term_id[term_id]
        elem_label = token['word']
        nodes_labels[elem_id] = elem_label
        
    nodes = {}
    for edge_element in tree_element.findall('edge'):
        child_id = edge_element.get('from')
        child_label = nodes_labels[child_id]
        child_node = nodes.get(child_id, Node(child_id, child_label))
        
        parent_id = edge_element.get('to')
        parent_label = nodes_labels[parent_id]
        parent_node = nodes.get(parent_id, Node(parent_id, parent_label))
        
        child_node.parent = parent_node
        parent_node.children.append(child_node)
        
        nodes[child_id] = child_node
        nodes[parent_id] = parent_node
        
    for node in nodes.values():
        if node.parent is None:
            return node

def parse_constituency(naf, tokens):
    """
    Returns a list of trees.
    Each tree is a dictionary object in this form:
    {
        "name": "Root node",
        "parent": null,
        "children": [
            {
                "name": "Child node 1",
                "parent": "Root node",
                "children": [
                    ... more sub-children
                ]
            },
            ... more children
        ]
    }
    """
    constituency_element = naf.find('constituency')
    if constituency_element is None:
        return []
    tree_elements = constituency_element.findall('tree')
    tokens_per_term_id = get_tokens_per_term_id(tokens)
    trees = [parse_tree_element(tree_element, tokens_per_term_id) for tree_element in tree_elements]
    
    return trees
