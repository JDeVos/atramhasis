import unittest

from pyramid.httpexceptions import HTTPMethodNotAllowed
from skosprovider.providers import DictionaryProvider
from skosprovider_sqlalchemy.models import Concept, Collection, Note, Label, ConceptScheme, Match, MatchType
from skosprovider_sqlalchemy.providers import SQLAlchemyProvider
from skosprovider.skos import(
    Concept as SkosConcept,
    Collection as SkosCollection
)

from atramhasis.utils import from_thing, internal_providers_only


species = {
    'id': 3,
    'uri': 'http://id.trees.org/3',
    'labels': [
        {'type': 'prefLabel', 'language': 'en', 'label': 'Trees by species'},
        {'type': 'prefLabel', 'language': 'nl', 'label': 'Bomen per soort'}
    ],
    'type': 'collection',
    'members': ['1', '2'],
    'notes': [
        {
            'type': 'editorialNote',
            'language': 'en',
            'note': 'As seen in How to Recognise Different Types of Trees from Quite a Long Way Away.'
        }
    ]
}


class TestFromThing(unittest.TestCase):
    def setUp(self):
        conceptscheme = ConceptScheme()
        conceptscheme.uri = 'urn:x-atramhasis-demo'
        conceptscheme.id = 1
        self.concept = Concept()
        self.concept.type = 'concept'
        self.concept.id = 11
        self.concept.concept_id = 101
        self.concept.uri = 'urn:x-atramhasis-demo:TREES:101'
        self.concept.conceptscheme_id = 1
        self.concept.conceptscheme = conceptscheme

        notes = []
        note = Note(note='test note', notetype_id='example', language_id='en')
        note2 = Note(note='note def', notetype_id='definition', language_id='en')
        notes.append(note)
        notes.append(note2)
        self.concept.notes = notes

        labels = []
        label = Label(label='een label', labeltype_id='prefLabel', language_id='nl')
        label2 = Label(label='other label', labeltype_id='altLabel', language_id='en')
        label3 = Label(label='and some other label', labeltype_id='altLabel', language_id='en')
        labels.append(label)
        labels.append(label2)
        labels.append(label3)
        self.concept.labels = labels

        matches = []
        match1 = Match()
        match1.uri ='urn:test'
        match1.concept = self.concept
        match1.matchtype = MatchType(name='closeMatch', description='')
        match2 = Match()
        match2.uri ='urn:test'
        match2.concept = self.concept
        match2.matchtype = MatchType(name='closeMatch', description='')
        matches.append(match1)
        matches.append(match2)
        self.matches = matches

        self.collection = Collection()
        self.collection.type = 'collection'
        self.collection.id = 12
        self.collection.concept_id = 102
        self.collection.uri = 'urn:x-atramhasis-demo:TREES:102'
        self.collection.conceptscheme_id = 1
        self.collection.conceptscheme = conceptscheme

    def test_thing_to_concept(self):
        skosconcept = from_thing(self.concept)
        self.assertTrue(isinstance(skosconcept, SkosConcept))
        self.assertEqual(skosconcept.id, 101)
        self.assertEqual(len(skosconcept.labels), 3)
        self.assertEqual(len(skosconcept.notes), 2)
        self.assertEqual(skosconcept.uri, 'urn:x-atramhasis-demo:TREES:101')

    def test_thing_to_collection(self):
        skoscollection = from_thing(self.collection)
        self.assertTrue(isinstance(skoscollection, SkosCollection))
        self.assertEqual(skoscollection.id, 102)
        self.assertEqual(skoscollection.uri, 'urn:x-atramhasis-demo:TREES:102')


class DummyViewClassForTest(object):

    def __init__(self):
        self.provider = None
        self.dummy = None

    def all_providers(self, dummy):
        self.dummy = dummy

    @internal_providers_only
    def internal_providers(self, dummy):
        self.dummy = dummy


class TestInternalProviderOnly(unittest.TestCase):

    def setUp(self):
        self.dummy = DummyViewClassForTest()

    def test_all_providers(self):
        self.dummy.provider = DictionaryProvider(list=[species], metadata={'id': 'Test'})
        self.dummy.all_providers('ok')
        self.assertEqual(self.dummy.dummy, 'ok')

    def test_internal_providers(self):
        self.dummy.provider = SQLAlchemyProvider(metadata={'id': 'Test', 'conceptscheme_id': 1},
                                                 session_maker=None)
        self.dummy.internal_providers('ok')
        self.assertEqual(self.dummy.dummy, 'ok')

    def test_external_providers(self):
        self.dummy.provider = SQLAlchemyProvider(metadata={'id': 'Test', 'conceptscheme_id': 1,
                                                           'subject': ['external']},
                                                 session_maker=None)
        self.assertRaises(HTTPMethodNotAllowed, self.dummy.internal_providers, 'ok')
        self.assertIsNone(self.dummy.dummy)

    def test_no_sqlalchemyprovider(self):
        self.dummy.provider = DictionaryProvider(list=[species], metadata={'id': 'Test'})
        self.assertRaises(HTTPMethodNotAllowed, self.dummy.internal_providers, 'ok')
        self.assertIsNone(self.dummy.dummy)
