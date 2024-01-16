![Build Status](https://github.com/CBIIT/bento-mdf/actions/workflows/who-validates-the-validator.yml/badge.svg)

# Bento Graph Model Description Format

## Overview

The Bento graph model description format allows a user to provide a
very simple, human-readable description of an overall [property
graph](https://en.wikipedia.org/wiki/Graph_(abstract_data_type))
model. The layout of nodes, relationships, node properties, and
relationship properties are specified in data structures expressed in
YAML-formatted _model description files_.

The Bento framework is currently used in the following projects;

* The [Bento standard model](https://github.com/CBIIT/bento-model)
* The [Integrated Canine Data Commons](https://caninecommons.cancer.gov)
* The [Clinical Trials Data Commons](https://github.com/CBIIT/ctdc-model)

## Drivers and Tools

Language drivers and other tools that want to comply with the Bento
framework should observe the latest [specification](./spec).

[bento_mdf](./drivers/python/) is a reference driver that validates
and loads MDF into a [bento-meta](https://github.com/CBIIT/bento-meta)
python object model.

[make-model](./drivers/Perl/make-model/README.md) is a reference
driver and tool written in [Perl](https://www.perl.org/).

### Validator

A simple command line validator `test-mdf.py` is included in 
[bento_mdf](./drivers/python). Install it like so:

    $ pip install bento-mdf

and run:

	$ test-mdf.py [model-file.yaml] [model-props-file.yaml] ...

## Model Description Files (MDF)

The layout of nodes, relationships, node properties, and relationship
properties are specified in data structures expressed in
YAML-formatted _model description files_.

The input format follows these general conventions, which are enforced
by a [JSONSchema](https://json-schema.org/understanding-json-schema/)
[schema](./schema/mdf-schema.yaml):

* Special key names are capitalized; these are essentially MDF directives;

* Custom names, such as names of nodes and properties, are all lower
  case, with underscores replacing any spaces ("snakecase");

A graph model can be expressed in a single YAML file, or multiple YAML
files. [Compliant](./spec) drivers will merge the data structures are
merged, so that, for example, nodes and relationships can be described
in one file, and property definitions can be provided in a separate
file.

### Model Descriptors

Top level keys that describe the model itself include:

	Handle: MyModel 
	URI: "https://sts.ctos-data-team.org/model/MyModel"
    Version: v1.7.2

The `Handle` value is intended to be a short, human-readable moniker 
for the model described in the document. It should be easy to compute 
with, e.g., contain no spaces and not start with a numeral. 

The `URI` value, if present, should be a resolving URL that can 
provide further detailed information about the model described in the 
MDF instance. Ideally, it should be the base URL for a terminology 
server (like the Simple Terminology Server), that can be concatenated 
with path information in the MDF to return relevant details. 

In particular, an enumerated value set can be included "by reference"
in the MDF, using a path.  Joining the URL value and the path value 
with a backslash should create a url that can return the actual list 
of enumerated values. 

The `Version` value, if present, should be a human-readable version
string (e.g., v1.7.2) for the model described in the MDF. Best
practice is to keep it in sync with a git tag for which a GitHub
release has been made.

### Nodes

The `Nodes` top-level key points to an object containing descriptions
of each node type in the model. Node descriptions look like:

    <nodename> :
        UniqueKeys:
            - [ 'propnameA', 'propnameB', ... ]
            - [ ... ]
            - ...
        Props:
           - <propname1>
           - <propname2>
           - ...

The `UniqueKeys` key points to an array of arrays. Each bottom-level
array is a list (which can be of length 1) of node property
names. This specifies that nodes of this type that are created in the
system must be unique with respect to the set of values for the
properties indicated. For example, `['id']` here indicates that the
value for the property `id` must be unique for all nodes of the
type. `['project_id', 'submitter_id']` indicates that the submitter id
must be unique among all nodes having a given project_id value.

The `Props` key points to a simple array of property names given as
strings. The detailed definition of each property (e.g., value type or
enumeration, required status) are provided once, in a separate
top-level section, `PropDefinitions` ([see below](#Property
Definitions)).

### Relationships

The `Relationships` top-level key points to an object of descriptions
of each relationship type. Relationship descriptions look like:

    <relname>:
         Props:
             - <propname>
         Req: [ true | false ]
         Mul: [ one_to_one | many_to_one | many_to_many | one_to_many ]
         Ends:
            - Src: <nodename1>
               Dst: <nodename2>
            - Src: <nodename...>
               ...

A named relationship can have properties defined, analogous to nodes.

A named relationship can be specified as required with the `Req` key,
and its multiplicity (from source node type to destination node type)
with the `Mul` key.

A given named relationship can be formed between different source and
destination node type pairs. The `Ends` key points to an array of
`{Src:<nodename>, Dst:<nodename>}` objects that describe the allowed
pairs.

### Property Definitions

The `PropDefinitions` top-level key points to an object of
descriptions of each property. Property descriptions look like:

    <propname1>:
        Desc: "A description of the property"
        Type: <string|number|...>
        # or the following:
        # Enum:
        #    - acceptable
        #    - values
        #    - for
        #    - property
        #    - go
        #    - here
        Nul: <true|false> # is property nullable?
        Req: <true|false> # is property required?

Either the `Type` or the `Enum` key should be present. If Enum key is
present, the `Type` key will be ignored.

Where properties need to be applied to Nodes and Relationships, use a
list of propnames from those defined in PropDefinitions.

PropDefinitions are frequently kept in a separate file, like `<model>-model-props.yml`.

#### Name Collisions in Property Definitions

The definitions of property values are separated from the list of
properties provided in Node and Relationship specs. This is in order
to make the model easier to read by humans. However, since there is
nothing to prevent two different nodes from having properties with the
same name or handle (nor should there be), the PropDefintions section
needs to be able to disambiguate this situation.

To refer to a property in a specific node in a PropDefinitions key,
use a dotted notation for the key `<node_name>.<property_name>`:

    PropDefinitions:
		diagnosis.best_response:
			...
		enrollment.best_response:
			...

#### Property Data Types

Properties are "slots" which can contain data. A property definition
requires a Type specification for that data. MDF recognizes the following types:

| Data Type | value of Type: key | Description |
|---|---|---|
| Simple scalar   | `number`, `integer`, `string`, `datetime`, `url`, `boolean`, `TBD` | Single value data. `TBD` is a placeholder |
| Number with units | `{ "value_type":<integer\|number>, "units": [ <string>, ... ]` | Units is an array of acceptable unit abbreviations (e.g. `["ul","nl"]`) |
| Pattern match | `{ "pattern":<regexp> }` | Acceptable data is a string matching the `pattern` regular expression |
| Acceptable value list | `[ <string>, ... ]` | List of acceptable string values (see below) |
| Union | `[ <typespec>, ... ]` | List of type specs; data should match at least one |
| List | `{ "value_type":"list", "item_type":<typespec> }` | Acceptable data is an array or list of items of specified type |


#### Acceptable Value Lists

The `Enum` key in a property definition may be followed by a list of
acceptable values, or a single list value containing a fully qualified
URI, or a URI path that can be concatenated to the model URI. In
either case, the resulting URI should resolve and should return a list
of acceptable values for the property:

	<propname2>:
	    ...
		Enum:
		    - https://sts.ctos-data-team.org/model/MyModel/property/<propname2>/list

### Terms

The `Terms` top-level key, if present, should contain descriptions of
terms used in the model. Terms relate string descriptors in the model
(such as the handles of nodes and relationships, or values within
enumerated acceptable value lists) to semantic concepts indexed in
formal or informal terminologies. The keys in the Terms object refer
to the term description, but they themselves need not be the string
representation of the term in data. The primary "code", or string
representation, is the term's "value" in the MDF. The term
specification can include an origin or terminology authority, that
authority's code or identifier for the term or concept, and a
definition that describes what the term signifies.

It is probably most convenient to keep the Terms key/value in a
separate file, like PropDefinitions, e.g. `<model>-model-terms.yml`.

    Terms:
		...
		<term_handle>:
			Value: <term_instance_string|"code">
			Origin: <authority name|abbrev|identifier>
			Code: <authority term id>
			Version: <authority term version>
			Defintion: |
				(authority's) text definition of term's concept 

#### Terms for Entities

Nodes, Relationships, or Properties themselves may in some contexts
have an external semantic representation in some framework. For
example, a `participant` Node may need to be associated with a precise
definition of "participant" as a person who is receiving medical care
(e.g., NCIt Patient concept [C16960](
https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&version=22.03d&ns=ncit&code=C16960&key=n93267819&b=1&n=null)). 
To record this, any Node, Relationship, or PropDefinition specification may
also include a `Term` key, with subkeys `Value`, `Origin`, etc.,
as in the previous paragraph.

### Universal Properties

In some use cases, it is desirable for every node (or relationship) to
possess a certain property or set of properties. For example, every
node may be expected to have a unique ID, regardless of its type.

The `UniversalNodeProperties` and 
`UniversalRelationshipProperties`
top-level keys provide a means to specify these properties. The subkey
`mustHave` should contain an array of property names for required
universal properties. The subkey `mayHave` can contain an array of
property names that are univerally allowable for all nodes or
relationships.

    UniversalNodeProperties:
      mustHave:
        - id
      mayHave:
        - transaction_id

### Multiple input YAML files and "overlays"

The [specification](./spec) allows graphs to be defined over multiple
input YAML files. The structured information in the files are merged
together to produce one input structure internally. This allows a user
to, for example, keep Node definitions in one file, Relationships in
another, and Property definitions in yet another. Each of these
objects has a separate top-level key, and will be merged into the
single internal object without any "collisions".

[Compliant](./spec) drivers and tools enable merging YAML files into a
single object according to specific rules. These allow the user to
"overlay" desired changes onto a base model file, without having to
resort to multiple versions of a base model. The first pair of files
is merged, the next file is merged into that result, and so on to the
end of the input files.  For example, using
[./drivers/Perl/make-model](model-tool):

    model-tool -g graph.svg icdc-model.yml temp-changes.yml

would create a graphic of nodes and edges defined in `icdc-model.yml`,
as modified by changes specified in `temp-changes.yml`.

#### Adding elements

As indicated above, if independent sets of keys at a given level of
the YAML structure are present in the input files, the merged
structure will possess all the keys and their contents:

File 1:

    Nodes:
      original_node:
        Props:
	      - old_prop

File 2:

    Nodes:
      original_node:
        Props:
          - new_prop
      addtional_node:
        Props:
          - new_prop

yields

    Nodes:
      original_node:
        Props:
          - old_prop
          - new_prop
      additional_node:
        Props:
          - new_prop

Note that by default, the overlay keys and values are added; original
array elements are not replaced. Array elements remain unique: if both
files have an element named `foo`, only one `foo` element will be
present in the merged array.

#### Deleting/replacing elements

To indicate that an overlay should remove a key and its contents, or
an array element, that are present in an earlier file, prefix the
key/element with a forward slash `/`

File 1:

    Nodes:
      original_node:
        Props:
          - unwanted_prop
          - a_prop
      unwanted_node:
        Props:
          - a_prop

File 2:

    Nodes:
      original_node:
        Props:
          - /unwanted_prop
          - new_prop
      /unwanted_node:
        Props:
          - whatever_prop

yields

    Nodes:
      original_node:
        Props:
          - a_prop
      - new_prop

#### Tagging Entities

A `Tags` entry can be added to any object (i.e., thing that accepts
key:value pairs), except a `Tags` entry, in the MDF. This is a way to
associate metainformation with an entity that can be read later by a
downstream custom processor. A `Tags` entry value is a json object
(dictionary, hash) containing a set of keys with _scalar_ values.

For example, one may markup a set of nodes to be rendered in a certain
color:

    dog:
      Props:
        - breed
      Tags:
        color: red
    cat:
      Props:
        - breed
      Tags:
        color: blue

## Model Description Format - Mappings

MDF-Map is an extension of MDF that allows a user to provide a simple,
human-readable description of cross-model mappings between two or more
models.

	Source: MyModel 
	URI: "https://sts.ctos-data-team.org/model/MyModel"

### Source

The `Source` value is intended to be a short, human-readable name that
represents the entity performing or asserting the cross-model mappings
such as the CRDC Data Standards Service (DSS) or Cancer Data
Aggregator (CDA).

    Source: MappingSource

### Models

The `Models` top-level key points to an object containing descriptions
of each target model that the source maps to such as Integrated Canine
Data Commons (ICDC). Model descriptions look like:

    <targetmodel1> :
        Version: <string|number|...>
        VersionDate: <date>
        URI: <string>


The `Version` key refers to the version of the model being mapped to.

The `VersionDate` key refers to the date of the model.

The `URI` key refers to a resolving URL that can provide more
information about the model being mapped. If the model is stored in
MDF, this could reference a GitHub release or commit for the mapped
version of the model.

At least one of these keys should be present for each model.

### Props

The `Props` top-level key refers to mappings between source and target
property names/handles given as strings. Property mappings look like:

    <sourcenode1> :
        <sourceprop1> :
            <targetmodel1> :
                - <targetprop1> :
                    Parents: <string>
                - <targetprop2> :
                    Constant: <true|false>

The mapping source properties are grouped by source
node/endpoint/domain. Each property then has an object where the keys
are target model handles (e.g. ICDC) and the values are arrays of the
target model's properties that map to that source property.

The `Parents` key refers to a node or series of nodes that the target
property is a child of. Multiple nodes may be provided in a dot
notation such as `parentnode1.parentnode2.childprop` to indicate a
nested structure. If the target property is a root-level property,
`Parents` is omitted.

The `Constant` key is a boolean value that indicates the source
property maps to a single constant value in the target model. For
example, a property with the handle "File Format" might always map to
the constant "DICOM" in the Imaging Data Commons. The default value is
false.
