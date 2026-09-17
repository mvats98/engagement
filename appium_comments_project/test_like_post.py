import unittest
from unittest.mock import Mock, patch

from instagram_actions.like_post import like_current_post


class ImmediateWait:
    def __init__(self, driver, timeout):
        self.driver = driver

    def until(self, predicate):
        result = predicate(self.driver)
        if not result:
            raise TimeoutError("State not confirmed")
        return result


class LikePostTests(unittest.TestCase):
    def setUp(self):
        self.state = {"selected": "false", "checked": "false", "content-desc": "Like"}
        self.button = Mock()
        self.button.is_displayed.return_value = True
        self.button.is_enabled.return_value = True
        self.button.get_attribute.side_effect = self.state.get
        self.driver = Mock()
        self.driver.find_element.return_value = self.button
        patcher = patch("instagram_actions.like_post.WebDriverWait", ImmediateWait)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_likes_once_and_confirms_state(self):
        self.button.click.side_effect = lambda: self.state.update(selected="true")
        self.assertTrue(like_current_post(self.driver, "custom.package"))
        self.button.click.assert_called_once()
        self.driver.find_element.assert_called_with("id", "custom.package:id/row_feed_button_like")
        self.driver.press_keycode.assert_not_called()

    def test_does_not_unlike_existing_like(self):
        for attributes in ({"selected": "true"}, {"checked": "true"}, {"content-desc": "Unlike"}):
            with self.subTest(attributes=attributes):
                self.state.update(selected="false", checked="false", **{"content-desc": "Like"})
                self.state.update(attributes)
                self.assertTrue(like_current_post(self.driver))
                self.button.click.assert_not_called()

    def test_uncertain_like_is_not_clicked_again(self):
        self.assertFalse(like_current_post(self.driver))
        self.button.click.assert_called_once()

    def test_missing_button_returns_failure(self):
        self.driver.find_element.side_effect = RuntimeError("Missing button")
        self.assertFalse(like_current_post(self.driver))
        self.button.click.assert_not_called()


if __name__ == "__main__":
    unittest.main()
