import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from citation_agent import PAPERS, work_key, merged, matches_target, bibliography
from citation_identity import build_ledger, independence
import citation_agent as agent

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

    def test_identifier_bridge_is_transitive_and_keeps_evidence(self):
        a={"target":"DLN","title":"First published geometric title","authors":"Alice Example","doi":"10.1000/demo","verified":True,"source":"PDF reference"}
        b={"target":"DLN","title":"Earlier geometric preprint title","authors":"Alice Example","doi":"https://doi.org/10.1000/DEMO","arxiv":"2601.10001"}
        c={"target":"DLN","title":"Earlier geometric preprint title","authors":"Alice Example","platform":"arxiv","id":"2601.10001v3","source":"index"}
        out=merged([a,b,c])
        self.assertEqual(len(out),1)
        self.assertTrue(out[0]["verified"])
        self.assertEqual(len(out[0]["evidence"]),2)

    def test_same_citing_work_two_targets_is_two_edges_one_work(self):
        papers=[{"id":"a","authors":["Minh Doan"]},{"id":"b","authors":["Minh Doan"]}]
        row={"target":"a","title":"A sufficiently long citing paper","authors":"Alice Example","arxiv":"2601.10001","verified":True}
        data=build_ledger(papers,[row,{**row,"target":"b"}],{})
        self.assertEqual(data["counts"]["verified"],2)
        self.assertEqual(data["counts"]["unique_citing_works"],1)

    def test_vietnamese_author_order_and_missing_names(self):
        p={"authors":["Nhat Minh Doan"]}
        self.assertEqual(independence(p,{"authors":"Đoàn Nhật Minh"}),"overlap")
        self.assertEqual(independence(p,{"authors":"N. M. Doan"}),"overlap")
        self.assertEqual(independence(p,{"authors":""}),"unknown")

    def test_identical_titles_different_authors_are_distinct(self):
        a={"target":"DLN","title":"A sufficiently long geometric title","authors":"Alice Example","doi":"10.1/a"}
        b={**a,"authors":"Bob Example","doi":"10.1/b"}
        self.assertEqual(len(merged([a,b])),2)

    def test_secret_is_removed_from_errors(self):
        with patch.dict(os.environ,{"OPENALEX_API_KEY":"private-test-value"}):
            result=agent.safe_error("error api_key=private-test-value&token=other-secret")
        self.assertNotIn("private-test-value",result)
        self.assertNotIn("other-secret",result)

    def test_exhausted_rate_limit_is_reported_and_deferred(self):
        response=type("Response",(),{"status_code":429})()
        agent.failed_hosts.clear();agent.errors.clear()
        with patch.object(agent.session,"get",return_value=response) as request, patch.object(agent.time,"sleep"):
            self.assertIsNone(agent.get("https://example.test/works"))
            self.assertIsNone(agent.get("https://example.test/works"))
        self.assertEqual(request.call_count,2)
        self.assertIn("429",agent.errors[0])
        agent.failed_hosts.clear();agent.errors.clear()

    def test_partial_checkpoint_preserves_verified_evidence(self):
        row={"target":"DLN","title":"A sufficiently long citing title","authors":"Alice Example","doi":"10.1/a","verified":True}
        candidate={**row,"verified":False,"arxiv":"2601.10001"}
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/"discovered.json"
            with patch.object(agent,"DIR",Path(directory)),patch.object(agent,"DEST",dest):
                verified=[row];candidates=[candidate]
                agent.checkpoint(candidates,verified,"partial")
                self.assertEqual(json.loads(dest.read_text())["collection_status"],"partial")
                self.assertEqual(len(json.loads((Path(directory)/"verified.json").read_text())),1)
                self.assertEqual(candidates,[])

    def test_identifier_prefix_is_not_a_reference_match(self):
        p=next(x for x in PAPERS if x["id"]=="DLN")
        self.assertFalse(matches_target("arXiv:2605.145740",p))

    def test_alphanumeric_reference_excerpt_contains_the_match(self):
        p=next(x for x in PAPERS if x["id"]=="polygons")
        references="[AB01] Unrelated work.\n"+"irrelevant detail. "*100+"\n[DKLT22] Doan et al., arXiv:2209.13937.\n[ZZ24] Another paper."
        excerpt=agent.evidence_excerpt(references,p)
        self.assertIn("2209.13937",excerpt)
        self.assertNotIn("irrelevant detail",excerpt)

    def test_short_title_with_author_is_verified(self):
        p=next(x for x in PAPERS if x["id"]=="pants")
        self.assertTrue(matches_target("[DPT23] Nhat Minh Doan, Hugo Parlier and Ser Peow Tan. Measuring pants. Transactions AMS, 2023.",p))
        self.assertFalse(matches_target("A tailor explains measuring pants for clothing.",p))

    def test_related_ortho_titles_are_not_counted_twice(self):
        p=next(x for x in PAPERS if x["id"]=="ortho")
        arithmetic=next(x for x in PAPERS if x["id"]=="arithmetic")
        entry="[DL26] Nhat Minh Doan and Khanh Le. Some arithmetic aspects of ortho-integral surfaces. Transactions AMS, 2026."
        self.assertFalse(matches_target(entry,p))
        self.assertTrue(matches_target(entry,arithmetic))
        self.assertTrue(matches_target(entry+"\n[Doa25] Nhat Minh Doan. Ortho-integral surfaces. Advances in Mathematics, 2025.",p))

    def test_page_number_prefix_does_not_hide_bibliography(self):
        document="Main text.\n35References\n[Doa25] Nhat Minh Doan. Ortho-integral surfaces."
        self.assertEqual(bibliography(document).strip(),"[Doa25] Nhat Minh Doan. Ortho-integral surfaces.")

    def test_contents_heading_does_not_turn_body_mentions_into_citations(self):
        document="Contents\nReferences\n37\nIntroduction\nDoan wrote Measuring pants.\nReferences\n[1] Alice Example. Another work."
        p=next(x for x in PAPERS if x["id"]=="pants")
        self.assertFalse(matches_target(bibliography(document),p))

    def test_versioned_identifier_and_line_wrapped_title(self):
        p=next(x for x in PAPERS if x["id"]=="DLN")
        self.assertTrue(matches_target("[1] N. M. Doan et al. arXiv:2605.14574v3.",p))
        filling=next(x for x in PAPERS if x["id"]=="filling")
        self.assertTrue(matches_target("[20] N. M. Doan. Geometric filling curves on punc-\ntured surfaces. Glasgow Mathematical Journal, 2023.",filling))

if __name__=="__main__":
    unittest.main()

