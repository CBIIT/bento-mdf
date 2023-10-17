"""
Tests for bento_mdf.diff
"""
from bento_mdf.diff import (
    Diff,
    diff_collection_atts,
    diff_object_atts,
    diff_simple_atts,
    get_collection_atts,
    get_ent_atts,
    get_object_atts,
    get_simple_atts,
)
from bento_meta.model import Model
from bento_meta.objects import Concept, Edge, Node, Property, Term, ValueSet

# constants
EMPTY_DIFF = Diff()
TEST_HANDLE = "test"
NODES = "nodes"
EDGES = "edges"
PROPS = "props"
TERMS = "terms"

NODE_ATTS = get_ent_atts(ent_type=NODES, diff=EMPTY_DIFF)
EDGE_ATTS = get_ent_atts(ent_type=EDGES, diff=EMPTY_DIFF)
PROP_ATTS = get_ent_atts(ent_type=PROPS, diff=EMPTY_DIFF)
TERM_ATTS = get_ent_atts(ent_type=TERMS, diff=EMPTY_DIFF)

NODE_HANDLE_1 = "subject"
NODE_HANDLE_2 = "diagnosis"
EDGE_HANDLE = "of_subject"
EDGE_KEY = (EDGE_HANDLE, NODE_HANDLE_2, NODE_HANDLE_1)
PROP_HANDLE = "primary_disease_site"
PROP_KEY = (PROP_HANDLE, NODE_HANDLE_2)
TERM_VALUE_1 = "Lung"
TERM_ORIGIN_1 = "NCIt"
TERM_KEY = (TERM_VALUE_1, TERM_ORIGIN_1)
TERM_VALUE_2 = "Kidney"
TERM_ORIGIN_2 = "NCIm"
TERM_KEY = (TERM_VALUE_2, TERM_ORIGIN_2)


class TestDiffEntities:
    """Unit tests for added/removed entities"""

    mdl_a = Model(handle=TEST_HANDLE)
    mdl_b = Model(handle=TEST_HANDLE)

    def test_same_model(self):
        pass

    def test_add_node(self):
        pass

    def test_remove_node(self):
        pass

    def test_add_edge(self):
        pass

    def test_remove_edge(self):
        pass

    def test_add_prop(self):
        pass

    def test_remove_prop(self):
        pass

    def test_add_term(self):
        pass

    def test_remove_term(self):
        pass


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
        a_ent = Property({"handle": PROP_HANDLE})
        b_ent = Property({"handle": PROP_HANDLE, self.SIMP_ATT: self.SIMP_ATT_2})

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
        a_ent = Property({"handle": PROP_HANDLE, self.SIMP_ATT: self.SIMP_ATT_1})
        b_ent = Property({"handle": PROP_HANDLE})

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
            entk=TERM_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY: {
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
            entk=TERM_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY: {
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
            entk=TERM_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY: {
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
                        self.OBJ_ATT_C: {"added": self.OBJ_ATT_C2, "removed": None}
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
                        self.OBJ_ATT_C: {"added": None, "removed": self.OBJ_ATT_C1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_concept_terms_of_node(self):
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
                        self.OBJ_ATT_C: {"added": self.OBJ_ATT_C2, "removed": None}
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
                        self.OBJ_ATT_C: {"added": None, "removed": self.OBJ_ATT_C1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_concept_terms_of_edge(self):
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
        a_ent = Property({"handle": PROP_HANDLE})
        b_ent = Property({"handle": PROP_HANDLE, self.OBJ_ATT_V: self.OBJ_ATT_V2})

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
                        self.OBJ_ATT_V: {"added": self.OBJ_ATT_V2, "removed": None}
                    }
                }
            }
        }
        assert actual == expected

    def test_remove_value_set_from_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE, self.OBJ_ATT_V: self.OBJ_ATT_V1})
        b_ent = Property({"handle": PROP_HANDLE})

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
                        self.OBJ_ATT_V: {"added": None, "removed": self.OBJ_ATT_V1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_value_set_terms_of_prop(self):
        diff = Diff()
        a_ent = Property({"handle": PROP_HANDLE, self.OBJ_ATT_V: self.OBJ_ATT_V1})
        b_ent = Property({"handle": PROP_HANDLE, self.OBJ_ATT_V: self.OBJ_ATT_V2})

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

    # term object attrs
    def test_add_concept_to_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1})
        b_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.TERM_OBJECT_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY: {
                        self.OBJ_ATT_C: {"added": self.OBJ_ATT_C2, "removed": None}
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
            entk=TERM_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY: {
                        self.OBJ_ATT_C: {"added": None, "removed": self.OBJ_ATT_C1}
                    }
                }
            }
        }
        assert actual == expected

    def test_change_concept_terms_of_term(self):
        diff = Diff()
        a_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C1})
        b_ent = Term({"value": TERM_VALUE_1, self.OBJ_ATT_C: self.OBJ_ATT_C2})

        diff_object_atts(
            a_ent=a_ent,
            b_ent=b_ent,
            obj_atts=self.TERM_OBJECT_ATTS,
            ent_type=TERMS,
            entk=TERM_KEY,
            diff=diff,
        )
        actual = diff.result
        expected = {
            TERMS: {
                "changed": {
                    TERM_KEY: {
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

    # node collection attrs
    def test_add_prop_to_node(self):
        pass

    def test_remove_prop_from_node(self):
        pass

    def test_change_prop_of_node(self):
        pass

    def test_add_tag_to_node(self):
        pass

    def test_remove_tag_from_node(self):
        pass

    def test_change_tag_of_node(self):
        pass

    # edge collection attrs
    def test_add_prop_to_edge(self):
        pass

    def test_remove_prop_from_edge(self):
        pass

    def test_change_prop_of_edge(self):
        pass

    def test_add_tag_to_edge(self):
        pass

    def test_remove_tag_from_edge(self):
        pass

    def test_change_tag_of_edge(self):
        pass

    # prop collection attrs
    def test_add_tag_to_prop(self):
        pass

    def test_remove_tag_from_prop(self):
        pass

    def test_change_tag_of_prop(self):
        pass

    # term collection attrs
    def test_add_tag_to_term(self):
        pass

    def test_remove_tag_from_term(self):
        pass

    def test_change_tag_of_term(self):
        pass
