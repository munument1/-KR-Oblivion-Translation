import unittest
from obcjk_text_backend import remove_english_name_glosses
class NameGlossTests(unittest.TestCase):
    def test_only_added_original_names_are_removed(self):
        text='보씨엘(Bothiel)에게 알스(Ales) 캠프에서 받은 쪽지 (설명)와 수치(25%), 형식(%s), 원문(unrelated)'
        cleaned,removed=remove_english_name_glosses(text,'Bothiel at Camp Ales')
        self.assertEqual(removed,['Bothiel','Ales'])
        self.assertEqual(cleaned,'보씨엘에게 알스 캠프에서 받은 쪽지 (설명)와 수치(25%), 형식(%s), 원문(unrelated)')
    def test_original_parenthetical_and_markup_preserved(self):
        text="<font face=5>표기(Note)와 다그니(Dagny's)"
        cleaned,removed=remove_english_name_glosses(text,"A (Note) from Dagny's Camp")
        self.assertEqual(cleaned,'<font face=5>표기(Note)와 다그니')
        self.assertEqual(removed,["Dagny's"])
