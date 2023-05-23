import xml_orm
import unittest

class TestXMLMethods(unittest.TestCase):
    def test_save_xml(self):
        xml_orm.drop_data()

    def test_save_load_xml(self):
        xml_string = '<?xml version="1.0" encoding="utf8"?><root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>'
        xml_orm.save_xml(xml_string)
        self.assertEqual(xml_string.replace(" ", "").replace("\n", "").replace("'", "\""), xml_orm.load_xml().replace(" ", "").replace("\n", "").replace("'", "\""))


if __name__ == '__main__':
    unittest.main()