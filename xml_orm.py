from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, Session
from xml.etree import ElementTree

engine = create_engine('sqlite:///XML-database.db')
Base = declarative_base()

class XmlNodes(Base):
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
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def save_node(session, node, parent_id):
    for i, child in enumerate(node):
        new_node = XmlNodes(name=child.tag, parent_node=parent_id, order=i)
        session.add(new_node)
        session.flush()
        if child.text and child.text.strip() != '':
            new_text = XmlAttribute(node_id=new_node.node_id, key='__text__', value=child.text)
            session.add(new_text)

        for attribute in child.items():
            new_attr = XmlAttribute(node_id=new_node.node_id, key=attribute[0], value=attribute[1])
            session.add(new_attr)
        save_node(session, child, new_node.node_id)

def save_xml(xml):
    root = ElementTree.fromstring(xml)

    with Session(engine) as session:
        root_node = XmlNodes(name=root.tag, parent_node=None, order=0)
        session.add(root_node)
        session.flush()
        if root.text and root.text.strip() != '':
            new_text = XmlAttribute(node_id=root_node.node_id, key='__text__', value=root.text)
            session.add(new_text)
        save_node(session, root, root_node.node_id)
        try:
            session.commit()
        except exc.SQLAlchemyError:
            session.rollback() # there were changes in database


def load_attributes(session, node, node_id):
    attributes = session.query(XmlAttribute).filter(XmlAttribute.node_id == node_id).all()
    for attrib in attributes:
        if attrib.key == '__text__':
            node.text = attrib.value
        else:
            node.set(attrib.key, attrib.value)

def load_node(session, parent, parent_node_id):
    nodes = session.query(XmlNodes).filter(XmlNodes.parent_node == parent_node_id).order_by(XmlNodes.order).all()
    for node in nodes:
        new_node = ElementTree.SubElement(parent, node.name)
        load_attributes(session, new_node, node.node_id)
        load_node(session, new_node, node.node_id)

def load_xml(id):
    with Session(engine) as session:
        root = session.query(XmlNodes).filter(XmlNodes.parent_node == None, XmlNodes.node_id == id).first()
        root_node = ElementTree.Element(root.name)
        load_attributes(session, root_node, root.node_id)
        load_node(session, root_node, root.node_id)
    return ElementTree.tostring(root_node, encoding='utf8', method='xml').decode().replace("><", ">\n<")

def available_xml():
    with Session(engine) as session:
        return session.query(XmlNodes.node_id, XmlNodes.name).filter(XmlNodes.parent_node == None).all()

def delete_node(session, node):
    for del_node in session.query(XmlNodes).filter(XmlNodes.parent_node == node).all():
        delete_node(session, del_node.node_id)
        session.query(XmlAttribute).filter(XmlAttribute.node_id == del_node.node_id).delete()
        session.commit()
        session.query(XmlNodes).filter(XmlNodes.node_id == del_node.node_id).delete()
        session.commit()

def delete_xml(id):
    with Session(engine) as session:
        root = session.query(XmlNodes).filter(XmlNodes.node_id == id)
        delete_node(session, root.first().node_id)
        root.delete()
        session.commit()

def update_node_value(id, pair):
    key, value = pair.split("=")
    with Session(engine) as session:
        attrib = session.query(XmlAttribute).filter(XmlAttribute.node_id == id, XmlAttribute.key == key).first()
        attrib.value = value
        session.commit()