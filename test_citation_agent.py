import unittest
from citation_agent import PAPERS, work_key, merged, matches_target, bibliography

class CitationLedgerTests(unittest.TestCase):
    def test_incoming_citation_deduplicates_versions(self):
        first={"target":"DLN","title":"Example result on curves","authors":"Alice Example",
               "platform":"arxiv","id":"2611.10001v1","verified":False}
        newer={**first,"id":"2611.10001v2"}
        self.assertEqual(len(merged([first,newer])),1)

    def test_published_and_arxiv_versions_merge_by_bibliographic_identity(self):
        a={"target":"polygons","title":"An exact geometric result",
           "authors":"Alice Example","doi":"10.1000/demo"}
        b={"target":"polygons","title":"An exact geometric result",
           "authors":"Alice Example","arxiv":"2601.10001"}
        self.assertEqual(len(merged([a,b])),1)

    def test_disambiguation_between_similar_ortho_papers(self):
        a=next(x for x in PAPERS if x["id"]=="ortho")
        b=next(x for x in PAPERS if x["id"]=="arithmetic")
        self.assertNotEqual(work_key(a),work_key(b))

    def test_old_preprint_alias_maps_to_published_paper(self):
        p=next(x for x in PAPERS if x["id"]=="polygons")
        self.assertTrue(matches_target("Doan et al. arXiv:2209.13937.",p))

    def test_fulltext_mentions_outside_bibliography_are_not_verified(self):
        document="We discuss arXiv:2605.14574.\nReferences\nA. Smith, unrelated paper."
        p=next(x for x in PAPERS if x["id"]=="DLN")
        self.assertFalse(matches_target(bibliography(document),p))

if __name__=="__main__":
    unittest.main()
