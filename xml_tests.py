import xml_orm
import unittest

class TestXMLMethods(unittest.TestCase):
    def setUp(self):
        xml_orm.drop_data()
    
    @classmethod
    def tearDownClass(self):
        xml_orm.drop_data()

    def test_clear_database(self):
        xml_orm.save_xml('<test></test>')
        xml_orm.drop_data()
        self.assertEqual(xml_orm.available_xml(), [])

    def test_save_load_xml(self):
        xml_string = '<?xml version="1.0" encoding="utf8"?><root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>'
        xml_orm.save_xml(xml_string)
        self.assertEqual(xml_string.replace(" ", "").replace("\n", "").replace("'", "\""), xml_orm.load_xml(xml_orm.available_xml()[0].node_id).replace(" ", "").replace("\n", "").replace("'", "\""))

    def test_available_xml(self):
        xml_orm.save_xml('<node></node>')
        xml_orm.save_xml('<test></test>')
        saved = [(1, 'node'), (2, 'test')]
        self.assertEqual(xml_orm.available_xml(), saved)

    def test_delete_xml(self):
        xml_orm.save_xml('<node></node>')
        xml_orm.delete_xml(1)
        self.assertEqual(xml_orm.available_xml(), [])

    def test_get_id_by_line_number(self):
        xml_orm.save_xml('<root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>')
        self.assertEqual(xml_orm.get_id_by_line_number(3, 1), 3)

    def test_upadate_node_value(self):
        xml_orm.save_xml('<root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>')
        xml_orm.update_node_value(1, 2, 'id=2')
        xml_orm.update_node_value(1, 3, '__text__=test')
        result = '<root><person id="2" name="John"><age>test</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>'
        loaded = xml_orm.load_xml(1)
        self.assertEqual(loaded[loaded.find('\n')+1:], result.replace("><", ">\n<"))

    def test_add_sub_node(self):
        xml = ['<root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person>', '</root>']
        add = '<person id="3" name="Kamil"><age>23</age><gender>Male</gender></person>'
        xml_orm.save_xml(xml[0]+xml[1])
        xml_orm.add_sub_xml(1, 1, add)
        loaded = xml_orm.load_xml(1)
        self.assertEqual(xml[0]+add+xml[1], loaded[loaded.find('\n')+1:].replace('\n', ''))

    def test_change_order(self):
        xml_orm.save_xml('<root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>')
        xml_orm.change_node_order(1, 2, 2)
        expected = '<root><person id="2" name="Jane"><age>25</age><gender>Female</gender></person><person id="1" name="John"><age>30</age><gender>Male</gender></person></root>'
        loaded = xml_orm.load_xml(1)
        self.assertEqual(expected, loaded[loaded.find('\n')+1:].replace('\n', ''))
    
    def test_find(self):
        xml_orm.save_xml('<root><person id="1" name="John"><age>30</age><gender>Male</gender></person><person id="2" name="Jane"><age>25</age><gender>Female</gender></person></root>')
        self.assertEqual(xml_orm.find_node_with_value(1, 1), ['<person id="1" name="John"></person>'])
        self.assertEqual(xml_orm.find_node_with_value(1, 25), ['<age>25</age>'])

if __name__ == '__main__':
    unittest.main()