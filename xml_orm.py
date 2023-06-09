from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, Session
from xml.etree import ElementTree

engine = create_engine('sqlite:///XML-database.db')
Base = declarative_base()

class XmlNodes(Base):
    """This is database model which contains xml nodes with their structure.
    For example we have <parent><child></child></parent>, then parent and child are
    saved as name in record, parent_node of parent is null and parent of child is the
    primary key of parent record."""
    __tablename__ = 'XmlNodes'
    node_id = Column('node_id', Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_node = Column(Integer, ForeignKey('XmlNodes.node_id'))
    order = Column(Integer, nullable=False)

    def __init__(self, name, parent_node, order):
        self.name = name
        self.parent_node = parent_node
        self.order = order

class XmlAttribute(Base):
    """This is database model which contains attributes and text values of
    specified node"""
    __tablename__ = 'XmlAttributes'
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey('XmlNodes.node_id'))
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    def __init__(self, node_id, key, value):
        self.node_id = node_id
        self.key = key
        self.value = value

Base.metadata.create_all(engine)

def drop_data():
    """This function allows to clear all tables in database."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _save_node(session, node, parent_id):
    """This is internal function which saves nodes recursively in database."""
    for i, child in enumerate(node, 1):
        new_node = XmlNodes(name=child.tag, parent_node=parent_id, order=i)
        session.add(new_node)
        session.flush()
        if child.text and child.text.strip() != '':
            new_text = XmlAttribute(node_id=new_node.node_id, key='__text__', value=child.text)
            session.add(new_text)

        for attribute in child.items():
            new_attr = XmlAttribute(node_id=new_node.node_id, key=attribute[0], value=attribute[1])
            session.add(new_attr)
        _save_node(session, child, new_node.node_id)

def save_xml(xml):
    """This function saves xml document into database. It throws ElementTree.ParseError when
    xml parsing fail."""
    root = ElementTree.fromstring(xml)

    with Session(engine) as session:
        root_node = XmlNodes(name=root.tag, parent_node=None, order=1)
        session.add(root_node)
        session.flush()
        if root.text and root.text.strip() != '':
            new_text = XmlAttribute(node_id=root_node.node_id, key='__text__', value=root.text)
            session.add(new_text)
        _save_node(session, root, root_node.node_id)
        try:
            session.commit()
        except exc.SQLAlchemyError:
            session.rollback() # there were changes in database


def _load_attributes(session, node, node_id):
    """This is internal function which loads node attribiutes."""
    attributes = session.query(XmlAttribute).filter(XmlAttribute.node_id == node_id).all()
    for attrib in attributes:
        if attrib.key == '__text__':
            node.text = attrib.value
        else:
            node.set(attrib.key, attrib.value)

def _load_node(session, parent, parent_node_id):
    """This is internal function which loads nodes from database."""
    nodes = session.query(XmlNodes).filter(XmlNodes.parent_node == parent_node_id).order_by(XmlNodes.order).all()
    for node in nodes:
        new_node = ElementTree.SubElement(parent, node.name)
        _load_attributes(session, new_node, node.node_id)
        _load_node(session, new_node, node.node_id)

def load_xml(id):
    """This function returns xml document.
    - id is the id of root node of the given xml. It can be read using available_xml function"""
    with Session(engine) as session:
        root = session.query(XmlNodes).filter(XmlNodes.parent_node == None, XmlNodes.node_id == id).first()
        root_node = ElementTree.Element(root.name)
        _load_attributes(session, root_node, root.node_id)
        _load_node(session, root_node, root.node_id)
    return ElementTree.tostring(root_node, encoding='utf8', method='xml').decode().replace("><", ">\n<")

def available_xml():
    """This function returns name and id of all xml documents in database"""
    with Session(engine) as session:
        return session.query(XmlNodes.node_id, XmlNodes.name).filter(XmlNodes.parent_node == None).all()

def _delete_node(session, node):
    """This is internal function which deletes nodes recursively from database."""
    for del_node in session.query(XmlNodes).filter(XmlNodes.parent_node == node).all():
        _delete_node(session, del_node.node_id)
        session.query(XmlAttribute).filter(XmlAttribute.node_id == del_node.node_id).delete()
        session.commit()
        session.query(XmlNodes).filter(XmlNodes.node_id == del_node.node_id).delete()
        session.commit()

def delete_xml(id):
    """This function deletes xml document from database by the given root node id."""
    with Session(engine) as session:
        root = session.query(XmlNodes).filter(XmlNodes.node_id == id)
        _delete_node(session, root.first().node_id)
        root.delete()
        session.commit()

def _iterate_to_get_id_by_line_number(session, id, search_line, curr_line):
    """This is internal function which counts line number."""
    curr_line[0] += 1
    if curr_line[0] == search_line:
        return id
    for child in session.query(XmlNodes).filter(XmlNodes.parent_node == id).order_by(XmlNodes.order).all():
        if found_id := _iterate_to_get_id_by_line_number(session, child.node_id, search_line, curr_line):
            return found_id

def get_id_by_line_number(line, root_id):
    """This function returns node id which is correlated with line
    <parent> this is line 1
        <node1></node1> line 2
        <node1></node1> line 3
    </parent> this is not line"""
    with Session(engine) as session:
        return _iterate_to_get_id_by_line_number(session, root_id, line, [0])    

def update_node_value(root_id, line_num, pair):
    """This function searches for equal key in specified line(line_num) in the given xml(root_id)."""
    key, value = pair.split("=")
    with Session(engine) as session:
        attrib = session.query(XmlAttribute).filter(XmlAttribute.node_id == get_id_by_line_number(line_num, root_id), XmlAttribute.key == key).first()
        attrib.value = value
        session.commit()

def add_sub_xml(root_id, line_num, xml):
    """This function adds xml as the child of node in the given line."""
    node = ElementTree.fromstring(xml)
    parent_id = get_id_by_line_number(line_num, root_id)
    with Session(engine) as session:
        child_count = session.query(XmlNodes).filter(XmlNodes.parent_node == parent_id).count()
        new_node = XmlNodes(name=node.tag, parent_node=parent_id, order=child_count+1)
        session.add(new_node)
        session.flush()
        if node.text and node.text.strip() != '':
            new_text = XmlAttribute(node_id=new_node.node_id, key='__text__', value=node.text)
            session.add(new_text)
        
        for attribute in node.items():
            new_attr = XmlAttribute(node_id=new_node.node_id, key=attribute[0], value=attribute[1])
            session.add(new_attr)
        _save_node(session, node, new_node.node_id)
        try:
            session.commit()
        except exc.SQLAlchemyError:
            session.rollback() # there were changes in database

def change_node_order(root_id, line_num, target_position):
    """This function allows to change order of node
    - root_id is id of xml root node
    - line_num is the line where is the node which will change position
    - target_position is number of the position to change on"""
    target_position = int(target_position)
    if target_position < 1:
        raise Exception()
    node_id = get_id_by_line_number(line_num, root_id)
    with Session(engine) as session:
        a = session.query(XmlNodes).filter(XmlNodes.node_id == node_id).first()
        b = session.query(XmlNodes).filter(XmlNodes.parent_node == a.parent_node, XmlNodes.order == target_position).first()
        b.order = a.order
        a.order = target_position
        session.commit()

def find_node_with_value(root_id, find):
    """This function searches for the value(find) in specified xml document(root_id)."""
    nodes = ''
    with Session(engine) as session:
        attribiutes = session.query(XmlAttribute).filter(XmlAttribute.value == find).all()
        nodes = []
        for attrib in attribiutes:
            node = session.query(XmlNodes).filter(XmlNodes.node_id == attrib.node_id).first()
            curr_attrib = session.query(XmlAttribute).filter(XmlAttribute.node_id == node.node_id).all()
            nodes.append(f'<{node.name}'+ " ".join(["", *[curr.key+'=\"'+curr.value+"\"" for curr in curr_attrib if curr.key != "__text__"]]) + f'>{str(*[curr.value for curr in curr_attrib if curr.key == "__text__"])}</{node.name}>')
    return nodes