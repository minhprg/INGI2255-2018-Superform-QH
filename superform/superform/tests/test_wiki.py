from superform.plugins.wiki import format_title, format_text


def test_format_title():
    title = 'my-super, title, with ;lot <of \/fails \\like \nthis ?or @this &and %that'

    assert format_title(title) == 'my-supertitlewithlotoffailslikethisorthisandthat'


def test_format_text():
    title, description = 'my title', 'my description'

    assert format_text(title, description) == '(:title my title:)my description'
