import json
import unittest
from io import StringIO

from wikiextractor.extract import Extractor, lowercase_visible_text


class LowercaseVisibleTextTests(unittest.TestCase):

    def setUp(self):
        self.keep_links = Extractor.keepLinks
        self.html_formatting = Extractor.HtmlFormatting
        self.to_json = getattr(Extractor, 'to_json', None)

    def tearDown(self):
        Extractor.keepLinks = self.keep_links
        Extractor.HtmlFormatting = self.html_formatting
        if self.to_json is None:
            try:
                del Extractor.to_json
            except AttributeError:
                pass
        else:
            Extractor.to_json = self.to_json

    def test_clean_text_lowercases_prose_sections_and_unicode(self):
        extractor = Extractor('1', '2', 'https://Example.test/wiki/', 'Mixed Title', [])

        paragraphs = extractor.clean_text(
            '== Mixed SECTION ==\nCAFÉ İstanbul TEXT',
            expand_templates=False,
        )

        self.assertEqual(['mixed section.', 'café i̇stanbul text'], paragraphs)

    def test_preserves_markup_entities_and_urls(self):
        text = (
            '<A DATA-Name="MixedValue" href="https://Example.test/CasePath">'
            'Mixed LABEL</A> https://Example.test/OtherPath &Aacute;'
        )

        self.assertEqual(
            '<A DATA-Name="MixedValue" href="https://Example.test/CasePath">'
            'mixed label</A> https://Example.test/OtherPath &Aacute;',
            lowercase_visible_text(text),
        )

    def test_preserves_escaped_markup(self):
        text = '&lt;A DATA-Name="MixedValue"&gt;Mixed LABEL&lt;/A&gt;'

        self.assertEqual(
            '&lt;A DATA-Name="MixedValue"&gt;mixed label&lt;/A&gt;',
            lowercase_visible_text(text),
        )

    def test_clean_text_preserves_link_target_and_lowercases_label(self):
        Extractor.keepLinks = True
        extractor = Extractor('1', '2', 'https://Example.test/wiki/', 'Mixed Title', [])

        paragraphs = extractor.clean_text(
            '[[Mixed Target|Mixed LABEL]]',
            expand_templates=False,
            html_safe=False,
        )

        self.assertEqual(
            ['<a href="Mixed%20Target">mixed label</a>'],
            paragraphs,
        )

    def test_doc_output_preserves_title_and_metadata(self):
        Extractor.to_json = False
        extractor = Extractor(
            'PageID',
            'RevisionID',
            'https://Example.test/wiki/',
            'Mixed Title',
            ['Mixed BODY'],
        )
        out = StringIO()

        extractor.extract(out)

        output = out.getvalue()
        self.assertIn(
            '<doc id="PageID" url="https://Example.test/wiki/?curid=PageID" '
            'title="Mixed Title">',
            output,
        )
        self.assertIn('\nMixed Title\n\nmixed body\n', output)

    def test_json_output_preserves_title_and_metadata(self):
        Extractor.to_json = True
        extractor = Extractor(
            'PageID',
            'RevisionID',
            'https://Example.test/wiki/',
            'Mixed Title',
            ['Mixed BODY'],
        )
        out = StringIO()

        extractor.extract(out)

        output = json.loads(out.getvalue())
        self.assertEqual('PageID', output['id'])
        self.assertEqual('RevisionID', output['revid'])
        self.assertEqual('https://Example.test/wiki/?curid=PageID', output['url'])
        self.assertEqual('Mixed Title', output['title'])
        self.assertEqual('mixed body', output['text'])


if __name__ == '__main__':
    unittest.main()
