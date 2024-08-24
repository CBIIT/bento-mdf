"""
Tests for bento_mdf.diff
"""


from bento_mdf.diff import (
    Diff,
    diff_collection_atts,
    diff_entities,
    diff_object_atts,
    diff_simple_atts,
    get_collection_atts,
    get_ent_atts,
    get_object_atts,
    get_simple_atts,
)
from bento_meta.model import Model
from bento_meta.objects import Concept, Edge, Node, Property, Tag, Term, ValueSet

# constants
TEST_HANDLE = "test"
NODES = "nodes"
EDGES = "edges"
PROPS = "props"
TERMS = "terms"

NODE_ATTS = get_ent_atts(ent_type=NODES, diff=Diff())
EDGE_ATTS = get_ent_atts(ent_type=EDGES, diff=Diff())
PROP_ATTS = get_ent_atts(ent_type=PROPS, diff=Diff())
TERM_ATTS = get_ent_atts(ent_type=TERMS, diff=Diff())

NODE_HANDLE_1 = "subject"
NODE_HANDLE_2 = "diagnosis"
EDGE_HANDLE = "of_subject"
EDGE_KEY = (EDGE_HANDLE, NODE_HANDLE_2, NODE_HANDLE_1)
PROP_HANDLE_1 = "primary_disease_site"
PROP_KEY = (PROP_HANDLE_1, NODE_HANDLE_2)
PROP_HANDLE_2 = "id"
TERM_VALUE_1 = "Lung"
TERM_ORIGIN_1 = "NCIt"
TERM_KEY_1 = (TERM_VALUE_1, TERM_ORIGIN_1)
TERM_VALUE_2 = "Kidney"
TERM_ORIGIN_2 = "NCIm"
TERM_KEY_2 = (TERM_VALUE_2, TERM_ORIGIN_2)


class TestDiffEntities:
    """Unit tests for added/removed entities"""

    node = Node({"handle": NODE_HANDLE_1})
    edge = Edge({"handle": EDGE_HANDLE})
    prop = Property({"handle": PROP_HANDLE_1})
    term = Term({"value": TERM_VALUE_1, "origin_name": TERM_ORIGIN_1})

    def test_add_node(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_b.nodes[NODE_HANDLE_1] = self.node
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[NODES]
        expected = {"added": {NODE_HANDLE_1: self.node}, "common": {}, "removed": {}}
        assert actual == expected

    def test_remove_node(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_a.nodes[NODE_HANDLE_1] = self.node
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[NODES]
        expected = {"added": {}, "common": {}, "removed": {NODE_HANDLE_1: self.node}}
        assert actual == expected

    def test_add_edge(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_b.edges[EDGE_KEY] = self.edge
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[EDGES]
        expected = {"added": {EDGE_KEY: self.edge}, "common": {}, "removed": {}}
        assert actual == expected

    def test_remove_edge(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_a.edges[EDGE_KEY] = self.edge
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[EDGES]
        expected = {"added": {}, "common": {}, "removed": {EDGE_KEY: self.edge}}
        assert actual == expected

    def test_add_prop(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_b.props[PROP_KEY] = self.prop
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[PROPS]
        expected = {"added": {PROP_KEY: self.prop}, "common": {}, "removed": {}}
        assert actual == expected

    def test_remove_prop(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_a.props[PROP_KEY] = self.prop
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[PROPS]
        expected = {"added": {}, "common": {}, "removed": {PROP_KEY: self.prop}}
        assert actual == expected

    def test_add_term(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_b.terms[TERM_KEY_1] = self.term
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[TERMS]
        expected = {"added": {TERM_KEY_1: self.term}, "common": {}, "removed": {}}
        assert actual == expected

    def test_remove_term(self):
        mdl_a = Model(handle=TEST_HANDLE)
        mdl_b = Model(handle=TEST_HANDLE)
        mdl_a.terms[TERM_KEY_1] = self.term
        diff = Diff()

        diff_entities(mdl_a=mdl_a, mdl_b=mdl_b, diff=diff)

        actual = diff.sets[TERMS]
        expected = {"added": {}, "common": {}, "removed": {TERM_KEY_1: self.term}}
        assert actual == expected


class TestDiffSimpleAtts:
    """Unit tests for changes to simple attributes of entities"""

    NODE_SIMPLE_ATTS = get_simple_atts(ent_atts=NODE_ATTS)
    EDGE_SIMPLE_ATTS = get_simple_atts(ent_atts=EDGE_ATTS)
    PROP_SIMPLE_ATTS = get_simple_atts(ent_atts=PROP_ATTS)
    TERM_SIMPLE_ATTS = get_simple_atts(ent_atts=TERM_ATTS)
    SIMP_ATT = "nanoid"
    SIMP_ATT_1 = "abc123"
    SIMP_ATT_2 = "def456"

    def test_add_nanoid_to_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1})
        b_ent = Node({"handle": NODE_HANDLE_1, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.NODE_SIMPLE_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.SIMP_ATT: {"added": self.SIMP_ATT_2, "removed": None}
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_nanoid_from_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Node({"handle": NODE_HANDLE_1})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.NODE_SIMPLE_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.SIMP_ATT: {"added": None, "removed": self.SIMP_ATT_1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_nanoid_of_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Node({"handle": NODE_HANDLE_1, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.NODE_SIMPLE_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.SIMP_ATT: {
                            "added": self.SIMP_ATT_2,
                            "removed": self.SIMP_ATT_1,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_nanoid_to_edge(self):
        diff = Diff()
        a_ent = Edge({"handle": EDGE_HANDLE})
        b_ent = Edge({"handle": EDGE_HANDLE, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.EDGE_SIMPLE_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.SIMP_ATT: {"added": self.SIMP_ATT_2, "removed": None}
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_nanoid_from_edge(self):
        diff = Diff()
        a_ent = Edge({"handle": EDGE_HANDLE, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Edge({"handle": EDGE_HANDLE})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.EDGE_SIMPLE_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.SIMP_ATT: {"added": None, "removed": self.SIMP_ATT_1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_nanoid_of_edge(self):
        diff = Diff()
        a_ent = Edge({"handle": EDGE_HANDLE, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Edge({"handle": EDGE_HANDLE, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.EDGE_SIMPLE_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.SIMP_ATT: {
                            "added": self.SIMP_ATT_2,
                            "removed": self.SIMP_ATT_1,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_nanoid_to_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE_1})
        b_ent = Property({"handle": PROP_HANDLE_1, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.PROP_SIMPLE_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.SIMP_ATT: {"added": self.SIMP_ATT_2, "removed": None}
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_nanoid_from_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE_1, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Property({"handle": PROP_HANDLE_1})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.PROP_SIMPLE_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.SIMP_ATT: {"added": None, "removed": self.SIMP_ATT_1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_nanoid_of_prop(self):
        diff = Diff()
        a_ent = Property({"handle": EDGE_HANDLE, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Property({"handle": EDGE_HANDLE, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.PROP_SIMPLE_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.SIMP_ATT: {
                            "added": self.SIMP_ATT_2,
                            "removed": self.SIMP_ATT_1,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_nanoid_to_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1})
        b_ent = Term({"value": TERM_VALUE_1, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.TERM_SIMPLE_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.SIMP_ATT: {"added": self.SIMP_ATT_2, "removed": None}
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_nanoid_from_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Term({"value": TERM_VALUE_1})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.TERM_SIMPLE_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.SIMP_ATT: {"added": None, "removed": self.SIMP_ATT_1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_nanoid_of_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Term({"value": TERM_VALUE_1, self.SIMP_ATT: self.SIMP_ATT_2})

        diff_simple_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            simple_atts=self.TERM_SIMPLE_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.SIMP_ATT: {
                            "added": self.SIMP_ATT_2,
                            "removed": self.SIMP_ATT_1,
                        }
                    }
                }
            }
        }
        assert actual == expected


class TestDiffObjectAtts:
    """Unit tests for changes to object attributes of entities"""

    NODE_OBJECT_ATTS = get_object_atts(ent_atts=NODE_ATTS)
    EDGE_OBJECT_ATTS = get_object_atts(ent_atts=EDGE_ATTS)
    PROP_OBJECT_ATTS = get_object_atts(ent_atts=PROP_ATTS)
    TERM_OBJECT_ATTS = get_object_atts(ent_atts=TERM_ATTS)
    OBJ_ATT_C = "concept"
    OBJ_ATT_C1 = Concept({"nanoid": "abc123"})
    OBJ_ATT_C2 = Concept({"nanoid": "def456"})
    OBJ_ATT_V = "value_set"
    OBJ_ATT_V1 = ValueSet({"handle": "vs252"})
    OBJ_ATT_V2 = ValueSet({"handle": "vs596"})
    TERM_1 = Term({"value": TERM_VALUE_1, "origin_name": TERM_ORIGIN_1})
    TERM_2 = Term({"value": TERM_VALUE_2, "origin_name": TERM_ORIGIN_2})
    OBJ_ATT_C1.terms[TERM_VALUE_1] = TERM_1
    OBJ_ATT_C2.terms[TERM_VALUE_2] = TERM_2
    OBJ_ATT_V1.terms[TERM_VALUE_1] = TERM_1
    OBJ_ATT_V2.terms[TERM_VALUE_2] = TERM_2

    def test_add_concept_to_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1})
        b_ent = Node({"handle": NODE_HANDLE_1, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.NODE_OBJECT_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.OBJ_ATT_C: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_concept_from_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Node({"handle": NODE_HANDLE_1})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.NODE_OBJECT_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.OBJ_ATT_C: {
                            "added": None,
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_concept_of_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Node({"handle": NODE_HANDLE_1, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.NODE_OBJECT_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.OBJ_ATT_C: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_concept_to_edge(self):
        diff = Diff()
        a_ent = Edge({"handle": EDGE_HANDLE})
        b_ent = Edge({"handle": EDGE_HANDLE, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.EDGE_OBJECT_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.OBJ_ATT_C: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_concept_from_edge(self):
        diff = Diff()
        a_ent = Edge({"handle": EDGE_HANDLE, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Edge({"handle": EDGE_HANDLE})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.EDGE_OBJECT_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.OBJ_ATT_C: {
                            "added": None,
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_concept_of_edge(self):
        diff = Diff()
        a_ent = Edge({"handle": EDGE_HANDLE, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Edge({"handle": EDGE_HANDLE, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.EDGE_OBJECT_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.OBJ_ATT_C: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_value_set_to_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE_1})
        b_ent = Property({"handle": PROP_HANDLE_1, self.OBJ_ATT_V: self.OBJ_ATT_V2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.PROP_OBJECT_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.OBJ_ATT_V: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_value_set_from_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE_1, self.OBJ_ATT_V: self.OBJ_ATT_V1})
        b_ent = Property({"handle": PROP_HANDLE_1})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.PROP_OBJECT_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.OBJ_ATT_V: {
                            "added": None,
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_value_set_of_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE_1, self.OBJ_ATT_V: self.OBJ_ATT_V1})
        b_ent = Property({"handle": PROP_HANDLE_1, self.OBJ_ATT_V: self.OBJ_ATT_V2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.PROP_OBJECT_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.OBJ_ATT_V: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_concept_to_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1})
        b_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.TERM_OBJECT_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.OBJ_ATT_C: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_concept_from_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Term({"value": TERM_VALUE_1})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.TERM_OBJECT_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.OBJ_ATT_C: {
                            "added": None,
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_concept_of_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.TERM_OBJECT_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.OBJ_ATT_C: {
                            "added": {self.TERM_2.value: self.TERM_2},
                            "removed": {self.TERM_1.value: self.TERM_1},
                        }
                    }
                }
            }
        }
        assert actual == expected


class TestDiffCollectionAtts:
    """Unit tests for changes to collection attributes of entities"""

    NODE_COLL_ATTS = get_collection_atts(ent_atts=NODE_ATTS)
    EDGE_COLL_ATTS = get_collection_atts(ent_atts=EDGE_ATTS)
    PROP_COLL_ATTS = get_collection_atts(ent_atts=PROP_ATTS)
    TERM_COLL_ATTS = get_collection_atts(ent_atts=TERM_ATTS)
    COLL_ATT_P = "props"
    COLL_ATT_P1 = Property({"handle": PROP_HANDLE_1})
    COLL_ATT_P2 = Property({"handle": PROP_HANDLE_2})
    COLL_ATT_T = "tags"
    COLL_ATT_T1 = Tag({"key": "class", "value": "primary"})
    COLL_ATT_T2 = Tag({"key": "class", "value": "secondary"})

    def test_add_prop_to_node(self):
        diff = Diff()
        a_ent = Node({"handle": NODE_HANDLE_1})
        b_ent = Node(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_P: {PROP_HANDLE_2: self.COLL_ATT_P2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.NODE_COLL_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.COLL_ATT_P: {
                            "added": {PROP_HANDLE_2: self.COLL_ATT_P2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_prop_from_node(self):
        diff = Diff()
        a_ent = Node(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_P: {PROP_HANDLE_1: self.COLL_ATT_P1},
            }
        )
        b_ent = Node({"handle": NODE_HANDLE_1})

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.NODE_COLL_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.COLL_ATT_P: {
                            "added": None,
                            "removed": {PROP_HANDLE_1: self.COLL_ATT_P1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_prop_of_node(self):
        diff = Diff()
        a_ent = Node(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_P: {PROP_HANDLE_1: self.COLL_ATT_P1},
            }
        )
        b_ent = Node(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_P: {PROP_HANDLE_2: self.COLL_ATT_P2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.NODE_COLL_ATTS,
            ent_type=NODES,
            entk=NODE_HANDLE_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            NODES: {
                "changed": {
                    NODE_HANDLE_1: {
                        self.COLL_ATT_P: {
                            "added": {PROP_HANDLE_2: self.COLL_ATT_P2},
                            "removed": {PROP_HANDLE_1: self.COLL_ATT_P1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_prop_to_edge(self):
        diff = Diff()
        a_ent = Node({"handle": EDGE_HANDLE})
        b_ent = Node(
            {
                "handle": EDGE_HANDLE,
                self.COLL_ATT_P: {PROP_HANDLE_2: self.COLL_ATT_P2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.EDGE_COLL_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.COLL_ATT_P: {
                            "added": {PROP_HANDLE_2: self.COLL_ATT_P2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_prop_from_edge(self):
        diff = Diff()
        a_ent = Node(
            {
                "handle": EDGE_HANDLE,
                self.COLL_ATT_P: {PROP_HANDLE_1: self.COLL_ATT_P1},
            }
        )
        b_ent = Node({"handle": EDGE_HANDLE})

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.EDGE_COLL_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.COLL_ATT_P: {
                            "added": None,
                            "removed": {PROP_HANDLE_1: self.COLL_ATT_P1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_prop_of_edge(self):
        diff = Diff()
        a_ent = Node(
            {
                "handle": EDGE_HANDLE,
                self.COLL_ATT_P: {PROP_HANDLE_1: self.COLL_ATT_P1},
            }
        )
        b_ent = Node(
            {
                "handle": EDGE_HANDLE,
                self.COLL_ATT_P: {PROP_HANDLE_2: self.COLL_ATT_P2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.EDGE_COLL_ATTS,
            ent_type=EDGES,
            entk=EDGE_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            EDGES: {
                "changed": {
                    EDGE_KEY: {
                        self.COLL_ATT_P: {
                            "added": {PROP_HANDLE_2: self.COLL_ATT_P2},
                            "removed": {PROP_HANDLE_1: self.COLL_ATT_P1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_tag_to_prop(self):
        diff = Diff()
        a_ent = Property({"handle": NODE_HANDLE_1})
        b_ent = Property(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.PROP_COLL_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.COLL_ATT_T: {
                            "added": {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_tag_from_prop(self):
        diff = Diff()
        a_ent = Property(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
            }
        )
        b_ent = Property({"handle": NODE_HANDLE_1})

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.PROP_COLL_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.COLL_ATT_T: {
                            "added": None,
                            "removed": {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_tag_of_prop(self):
        """tags have same key but updated value"""
        diff = Diff()
        a_ent = Property(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
            }
        )
        b_ent = Property(
            {
                "handle": NODE_HANDLE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.PROP_COLL_ATTS,
            ent_type=PROPS,
            entk=PROP_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            PROPS: {
                "changed": {
                    PROP_KEY: {
                        self.COLL_ATT_T: {
                            "added": {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
                            "removed": {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_add_tag_to_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1})
        b_ent = Term(
            {
                "value": TERM_VALUE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.TERM_COLL_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.COLL_ATT_T: {
                            "added": {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
                            "removed": None,
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_tag_from_term(self):
        diff = Diff()
        a_ent = Term(
            {
                "value": TERM_VALUE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
            }
        )
        b_ent = Term({"value": TERM_VALUE_1})

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.TERM_COLL_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.COLL_ATT_T: {
                            "added": None,
                            "removed": {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
                        }
                    }
                }
            }
        }
        assert actual == expected

    def test_change_tag_of_term(self):
        diff = Diff()
        a_ent = Term(
            {
                "value": TERM_VALUE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
            }
        )
        b_ent = Term(
            {
                "value": TERM_VALUE_1,
                self.COLL_ATT_T: {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
            }
        )

        diff_collection_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            coll_atts=self.TERM_COLL_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY_1,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY_1: {
                        self.COLL_ATT_T: {
                            "added": {self.COLL_ATT_T2.key: self.COLL_ATT_T2},
                            "removed": {self.COLL_ATT_T1.key: self.COLL_ATT_T1},
                        }
                    }
                }
            }
        }
        assert actual == expected
