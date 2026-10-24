from zzz_lv.gui.view.home.tutorial_content import QUICK_STEPS, build_tutorial_pages


def test_pages_and_keys() -> None:
    pages = build_tutorial_pages('F9', 'F10')
    assert [p.key for p in pages] == ['prepare', 'settings', 'lost_void', 'battle', 'faq']
    assert len({p.key for p in pages}) == len(pages)
    for page in pages:
        assert page.title and page.intro
        assert page.steps
        for step in page.steps:
            assert step.title.strip() and step.body.strip()


def test_hotkeys_are_filled_in() -> None:
    text = ''.join(
        f'{s.title}{s.body}' for p in build_tutorial_pages('F7', 'F8') for s in p.steps
    )
    assert 'F7' in text and 'F8' in text
    # 默认键位不能写死在内容里
    assert 'F9' not in text and 'F10' not in text


def test_quick_steps_match_banner() -> None:
    assert len(QUICK_STEPS) == 3
