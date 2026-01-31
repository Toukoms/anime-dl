import unittest
from extractors.streamtape import _find_get_video_path

class TestStreamtapeParser(unittest.TestCase):
    def test_absolute_link(self):
        html = '<a href="https://streamtape.com/get_video?id=abc&expires=123&signature=xyz">link</a>'
        self.assertEqual(_find_get_video_path(html), "https://streamtape.com/get_video?id=abc&expires=123&signature=xyz")

    def test_relative_link(self):
        html = '<a id="robotlink" href="/get_video?id=abc&expires=123&signature=xyz">link</a>'
        self.assertEqual(_find_get_video_path(html), "/get_video?id=abc&expires=123&signature=xyz")

    def test_script_build(self):
        html = 'var s="/get_video?id=abc&expires=123&signature=xyz";'
        self.assertTrue(_find_get_video_path(html).startswith("/get_video?id=abc"))

if __name__ == "__main__":
    unittest.main()
