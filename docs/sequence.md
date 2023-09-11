# Writing a Sequence

Coming soon...


## A basic sequence

```json
{
    "toolkits": [
        "foobar_stk", // toolkits that provide methods called here
        "barbaz_stk",
    ],
    "include": {
        "nested_seq1": "file:/foo/bar.json5", // load other sequences called here
        "nested_seq2": "file:/foo/baz.json5",
    },
    "run": [
        1, // puts 1 on the stack
        2, // puts 2 on the stack
        "+", // + method adds the two items at the top of stack
        3,
        "nested_seq1", // calls "nested_seq1"

    ]
}
```
