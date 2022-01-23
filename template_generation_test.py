from email import generator
from venv import create
from qald_to_template import create_generator_query, extract_classes, find_prefix, find_vars, reform_keywords, replace_keywords
import ssl
import unittest

ssl._create_default_https_context = ssl._create_unverified_context

class Q:
    def __init__(self, question, query, keywords) -> None:
        self.question = question
        self.query = query
        self.keywords = reform_keywords(keywords)
    
    def test_classes(self):
        g_q, changed_kw = create_generator_query(self.keywords, self.query)
        print('Classes: ')
        print(extract_classes(self.query, changed_kw))
    
    def test_generator_query(self):
        g_q, changed_kw = create_generator_query(self.keywords, self.query)
        print('generator query: ')
        print(g_q)
        print('changed keywords: ')
        print(changed_kw)

    def test_var(self):
        vars = find_vars(self.query)
        print('vars: ')
        print(vars)
    
    def test_replace_keywords(self):
        g_q, changed_kw = create_generator_query(self.keywords, self.query)
        new_question, new_query = replace_keywords(changed_kw, self.question, self.query)
        return new_question, new_query

Q2 = Q(
    "Which movies starring Mickey Rourke were directed by Guy Ritchie?",
    "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX res: <http://dbpedia.org/resource/> PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> SELECT DISTINCT ?uri WHERE { ?uri rdf:type dbo:Film ; dbo:starring res:Mickey_Rourke ; dbo:director res:Guy_Ritchie }",
    "movies, starring, Mickey Rourke, directed, Guy Ritchie"
)

Q3 = Q(
    "Who was the wife of U.S. president Lincoln?",
    "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX res: <http://dbpedia.org/resource/> SELECT DISTINCT ?uri WHERE { res:Abraham_Lincoln dbo:spouse ?uri }",
    "U.S. president, Lincoln, wife"
)

Q4 = Q(
    "What is the currency of the Czech Republic?",
    "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX res: <http://dbpedia.org/resource/> SELECT DISTINCT ?uri WHERE { res:Czech_Republic dbo:currency ?uri }",
    "Czech republic, currency"
)

Q5 = Q(
    "What are the five boroughs of New York?",
    "PREFIX dbo: <http://dbpedia.org/ontology/> SELECT DISTINCT ?uri WHERE { ?uri dbo:governmentType <http://dbpedia.org/resource/Borough_(New_York_City)> }",
    "five boroughs, New York"
)

class TestQtT(unittest.TestCase):
    def test_57(self):
        question = Q(
                "Who is the mayor of Tel Aviv?",
                "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX res: <http://dbpedia.org/resource/> SELECT DISTINCT ?uri WHERE { res:Tel_Aviv dbo:leaderName ?uri }",
                "Tel Aviv, mayor")
        new_ques, new_query = question.test_replace_keywords()
        self.assertEqual(new_ques, "who is the mayor of <A>?")
        self.assertEqual(new_query, "SELECT DISTINCT ?uri WHERE { <A> dbo:leaderName ?uri }")

    def test_142(self):
        question = Q(
            "What is the currency of the Czech Republic?",
            "PREFIX dbo: <http://dbpedia.org/ontology/> PREFIX res: <http://dbpedia.org/resource/> SELECT DISTINCT ?uri WHERE { res:Czech_Republic dbo:currency ?uri }",
            "Czech republic, currency")
        generator_query, changed_kw = create_generator_query(question.keywords, question.query)
        self.assertEqual(generator_query, "select distinct ?a, ?b where { ?a ?b ?uri }")
        new_ques, new_query = question.test_replace_keywords()
        self.assertEqual(new_ques, "what is the <B> of the <A>?")
        # self.assertEqual(new_query, "SELECT DISTINCT ?uri WHERE { <A> dbo:currency ?uri }")



if __name__ == '__main__':
    unittest.main()