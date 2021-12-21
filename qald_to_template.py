'''
template:
target class 1; target class 2; target class 3; question; query; generator query; id

'''

import json
import csv
import argparse
from os import replace
import re
import ssl
from SPARQLWrapper import JSON
from SPARQLWrapper import SPARQLWrapper

PREFIXES = [
        "PREFIX dbr: <http://dbpedia.org/resource/>",
        "PREFIX dbo: <http://dbpedia.org/ontology/>",
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "PREFIX res: <http://dbpedia.org/resource/>",
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
        "PREFIX dbc: <http://dbpedia.org/resource/Category:>",
        "PREFIX dct: <http://purl.org/dc/terms/>",
        "PREFIX dbp: <http://dbpedia.org/property/>",
        "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>",
        "PREFIX dct: <http://purl.org/dc/terms/>",
        "PREFIX foaf: <http://xmlns.com/foaf/0.1/>",
        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>",
        "PREFIX foaf:<http://xmlns.com/foaf/0.1/>",
        "PREFIX yago: <http://dbpedia.org/class/yago/>",
        "PREFIX onto: <http://dbpedia.org/ontology/>",
        "PREFIX db: <http://dbpedia.org/>",
        "PREFIX dbo: <http://dbpedia.org/property/>",
        "PREFIX dbp: <http://dbpedia.org/ontology/>",
        "PREFIX class: <http://dbpedia.org/resource/classes#>",
        "PREFIX dbr: <http://dbpedia.org/property/>"
]


class Template:
    '''
    a class which contains all necessary attributes for template
    '''
    def __init__(self, target_class_1, target_class_2, target_class_3, question, query, generator_query, id) -> None:
        self.target_class_1 = target_class_1        # PREFIX 1
        self.target_class_2 = target_class_2        # PREFIX 2
        self.target_class_3 = target_class_3        # PREFIX 3
        self.question = question                    # replace keyword from question
        self.query = query                          # actual query used for question, replace keyword
        self.generator_query = generator_query      # generate alternative instances for query and question, from WHERE{_ _ _} in query, SELECT DISTINCT ?a (, ?b) WHERE {...}
        self.id = id                                # question id from qald

def read_json(file):
    '''
    read json file
    :file: json file path
    :return: content in the json file
    '''
    with open(file, 'r',encoding="utf8") as f:
        qald = json.load(f)
    return qald

def output_csv(templates, file_name):
    '''
    output a csv file in file_name
    :templates: list of Template objects
    :file_name: name of the output csv file
    '''
    with open(file_name, "w", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        for template in templates:
            writer.writerow([
                template.target_class_1,
                template.target_class_2,
                template.target_class_3,
                template.question,
                template.query,
                template.generator_query,
                template.id
            ])

def extract_templates(qald):
    '''
    build templates from qald
    :qald: raw qald data dictionary 
    :return: list of Template objects
    '''
    templates = []
    total = len(qald['questions'])
    for ques in qald['questions']:
        id = ques['id']
        sparql_query = ques['query']['sparql']
        for que_str in ques["question"]:
            if que_str['language']=="en":
                question = que_str["string"]
                keywords = reform_keywords(que_str["keywords"])
                break
        print('processing question <{}>'.format(question), end=" ")
        print('{} / {}'.format(id, total))
        generator_query, changed_kw = create_generator_query(keywords, sparql_query)
        new_question, new_query = replace_keywords(changed_kw, question, sparql_query)

        classes = extract_classes(sparql_query, changed_kw)
        if classes:
            try:
                target_class_1 = classes[0]
            except:
                target_class_1 = ''
            try:
                target_class_2 = classes[1]
            except:
                target_class_2 = ''
            try:
                target_class_3 = classes[2]
            except:
                target_class_3 = ''
            templates.append(Template(target_class_1, target_class_2, target_class_3, new_question, new_query, generator_query, id))
        else:
            print('unable to find replacements for <{}>, ignored'.format(question))
    return templates

def create_generator_query(keywords, query):
    '''
    create generator query
    :keywords: keywords list
    :query: sparql query
    :return: generator query, dict for changed keywords in format {chr_num: [kw_option1, kw_option2,...],...}
    '''
    where = re.findall(r'\{.*\}', query)[0]
    candidates = where.split(' ')
    chr_num = 97    # begin with ?a
    vars = []
    changed_kw = {}
    for kw in keywords:
        for part in candidates:
            instance = re.findall(r'[a-z]{3}:.*?'+kw, part)
            if instance:
                new_kw = instance[0]
                changed_kw[chr_num] = [kw]
                if new_kw[4:] != kw:
                    changed_kw[chr_num].append(new_kw[4:])
                vars.append('?'+chr(chr_num))
                where = where.replace(new_kw, '?'+chr(chr_num))
                chr_num += 1
                break
    # prefix = find_prefix(query)
    generator_query = "select distinct {} where {}".format(','.join(vars), where)
    return generator_query, changed_kw

def extract_classes(query, keywords):
    '''
    extract target classes for changed instances
    :query: sparql query string
    :keywords: dict of pairs: replaced keywords and by which character in ASCII number
    :return: list of types of instances which is replaced by <A>,<B>
    '''
    types = []
    where = re.findall(r'\{.*\}', query)[0]
    candidate = where.split(' ')
    for kw_num, kws in keywords.items():
        for kw in kws:
            for part in candidate:
                instance_list = re.findall(r'[a-z]{3}:.*?'+kw, part)
                if instance_list:
                    instance = instance_list[0]
            type_query = '''
                PREFIX dbr: <http://dbpedia.org/resource/>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX res: <http://dbpedia.org/resource/>
                SELECT ?type WHERE {{
                    {} rdf:type ?type
                }}
            '''.format(instance)
            try:
                type = get_type(type_query)
                if type:
                    types.append(type)
                else:
                    types.append('')
            except:
                types.append('')
            break
    return types

def get_type(query: str) -> dict:
    '''
    used by extract_classes to get type of a keyword with prefix dbo
    :query: sparql query to ask type in dbpedia
    :return: type of the asked keyword
    '''
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    # sparql.query() returns HTML response
    # convert() converts response to dictionary
    prefix = 'http://dbpedia.org/ontology/'
    answers = sparql.query().convert()['results']['bindings']
    for answer in answers:
        type = answer['type']['value']
        if prefix in type:
            return type

def find_vars(query):
    '''
    find variables from sparql query
    :query: sparql query
    :return: variable list
    '''
    query = query.split("{")[0]
    vars = re.findall(r'\?[a-z]+', query)
    return vars

def find_prefix(query):
    '''
    extract PREFIX from query
    :query: sparql query
    :return: PREFIX list
    '''
    return re.findall(r'PREFIX.*?/>', query)

def reform_keywords(keywords):
    '''
    reform keywords to list and with '_' instead of ' '
    :keywords: keywords as string
    :return: keywords as list
    '''
    kw_list = keywords.split(", ")
    kw_list = [word.strip().replace(" ","_") for word in kw_list]
    return kw_list


def replace_keywords(keywords, question, query):
    '''
    replace keywords in question and query with <A>, <B>, ... 
    if they are replaced by results from generator query
    :keywords: dict of pairs: replaced keywords included alternatives and by which character in ASCII number
    :question: the original question
    :query: the original query
    :return: question and query with instances replaced by <A>, <B>, ...
    '''
    where = re.findall(r'\{.*\}', query)[0]
    candidates = where.split(' ')
    for chr_num, kws_list in keywords.items():
        replace_char = '<'+chr(chr_num-32)+'>'
        for kw in kws_list:
            if '(' in kw or ')' in kw:
                continue
            for part in candidates:
                instances_list = re.findall(r'[a-z]{3}:.*?'+kw, part)
                if instances_list:
                    instance = instances_list[0]
                    query = query.replace(instance, replace_char)
            kw_space = kw.replace('_',' ')
            if kw_space in question:
                question = question.replace(kw_space, replace_char)
    # prefixes = find_prefix(query)
    for prefix in PREFIXES:
        query = query.replace(prefix, '').lstrip()
    return question, query



if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='qald_data', help='training dataset in qald format',required=True)
    parser.add_argument('--output', dest='output_csv', help='output directory of template csv', required=True) # only requires output repository

    args = parser.parse_args()

    dataset = args.qald_data
    output = args.output_csv + '\output.csv'

    # to avoid [SSL: CERTIFICATE_VERIFY_FAILED] error
    ssl._create_default_https_context = ssl._create_unverified_context

    qald = read_json(dataset)
    templates = extract_templates(qald)
    output_csv(templates, output)
    print('template is output in {}'.format(output))
    