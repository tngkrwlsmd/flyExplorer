"""Regression contracts for native popup chevrons and toolbar skin."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

class NativeLegacyUiContract(unittest.TestCase):
 def test_localized_workspace_menu_has_no_corrupt_placeholders(self):
  doc=ET.parse(ROOT/'src/fxfile/Languages/Korean.xml')
  strings={n.attrib['ID']:n.text for n in doc.iter('String') if n.attrib.get('ID','').startswith('cmd.workspace.')}
  assert len(strings)==3,strings
  for key,value in strings.items():
   self.assertTrue(value and '\uC791\uC5C5 \uACF5\uAC04' in value,(key,value))
   self.assertNotIn('??',value,(key,value))

 def test_single_large_submenu_chevron_without_font_dependency(self):
  text=(ROOT/'src/fxfile/gui/BCMenu.cpp').read_text(encoding='utf-8-sig')
  start=text.index('void BCMenu::drawSubmenuChevron(')
  end=text.index('void BCMenu::drawText(',start)
  block=text[start:end]
  self.assertIn('scaleForWindow(5, sMetricHwnd)',block)
  self.assertIn('scaleForWindow(2, sMetricHwnd)',block)
  self.assertEqual(block.count('aDC->LineTo('),2)
  self.assertNotIn('Segoe Fluent Icons',block)
  self.assertIn('mHighContrast',block)

 def test_native_customize_uses_dialog_scrollbar_and_dark_palette(self):
  text=(ROOT/'src/fxfile/gui/rebar/CustomizeDialog.cpp').read_text(encoding='utf-8-sig')
  start=text.index('void CCustomizeDialog::RefreshModernAppearance()')
  section=text[start:]
  self.assertIn('ModernUI::applyDialogControlTheme(',section)
  self.assertIn('ModernUI::resetControlTheme(',section)
  self.assertIn('OnEraseBkgnd(CDC* pDC)',text)
  self.assertIn('CTLCOLOR_STATIC',text)
  self.assertIn('mHighContrast',text)

if __name__=='__main__': unittest.main()
