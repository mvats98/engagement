import unittest
from unittest.mock import Mock, patch
from selenium.common.exceptions import TimeoutException
from instagram_actions.comment_post import open_post_with_retry


class PostLoadingTests(unittest.TestCase):
    def run_loading(self, results):
        driver = Mock()
        driver.get_window_size.return_value = {'width': 720, 'height': 1600}
        with patch('instagram_actions.comment_post.WebDriverWait') as wait, \
             patch('instagram_actions.comment_post.subprocess.run') as launch, \
             patch('instagram_actions.comment_post.time.sleep'):
            wait.return_value.until.side_effect = results
            result = open_post_with_retry(driver, 'https://www.instagram.com/p/test/',
                                          'phone', 'com.instagram.android')
            return result, launch.call_count, driver.swipe.call_count

    def test_first_load_does_not_retry(self):
        button = Mock()
        result, launches, swipes = self.run_loading([button])
        self.assertEqual(result, (button, False))
        self.assertEqual((launches, swipes), (1, 0))

    def test_failed_load_reopens_same_post(self):
        button = Mock()
        result, launches, swipes = self.run_loading([TimeoutException()] * 6 + [button])
        self.assertEqual(result, (button, False))
        self.assertEqual((launches, swipes), (2, 5))

    def test_stops_after_three_failed_loads(self):
        result, launches, swipes = self.run_loading([TimeoutException()] * 18)
        self.assertEqual(result, (None, False))
        self.assertEqual((launches, swipes), (3, 15))


if __name__ == '__main__':
    unittest.main()
