from datetime import datetime
import json
import ssl
import sys

from SPARQLWrapper import JSON, SPARQLWrapper
from nbformat import write

import logging

import interpreter_spotlight

ssl._create_default_https_context = ssl._create_unverified_context


def get_answer(queryString):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    try:
        sparql.setQuery(queryString)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        results["head"].pop("link", None)
        results["results"].pop("distinct", None)
        results["results"].pop("ordered", None)
    except:
        results = {}
    return results


def read_json(file):
    '''
    read json file
    :file: json file path
    :return: content in the json file
    '''
    with open(file, 'r', encoding="utf8") as f:
        qald = json.load(f)
    return qald


def write_json(qald, output='results.json'):
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(qald, f, indent=2)


def modify_ques(qald):
    for q in qald["questions"]:
        questionString = extract_question_string(q)
        queryString = predict_query_string(questionString)
        q["query"]["sparql"] = queryString
        answer = [get_answer(queryString)]

        q["answers"] = answer


def predict_query_string(questionString):
    try:
        info, queryString = interpreter_spotlight.process_question(questionString)
        logging.info(info)
    except:
        queryString = ""
    return queryString


def extract_question_string(q):
    for que_str in q["question"]:
        if que_str['language'] == "en":
            questionString = que_str["string"]
            break
    return questionString


if __name__ == "__main__":
    qald_json = sys.argv[1]
    logging.basicConfig(filename=datetime.now().strftime('result_%H_%M_%d_%m_%Y.log'), level=logging.INFO)
    logging.info("results for {}".format(qald_json))
    qald = read_json(qald_json)
    modify_ques(qald)
    if sys.argv[2]:
        write_json(qald, sys.argv[2])
    else:
        write_json(qald)
