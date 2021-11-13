from ulauncher.utils.string import remove_accents


def test_remove_accents():
    assert remove_accents("Virransäästö") == "Virransaasto"
    assert remove_accents("Éditeur d’image GIMP") == "Editeur dimage GIMP"
    assert remove_accents('Ögbelgilengen Uyğulamalar') == 'Ogbelgilengen Uygulamalar'
