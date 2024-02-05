
comparison_true = {"eq": [1, 1]}
comparison_false = {"eq": [1, 0]}

not_op_true = {"not": {"eq": [1, 2]}}
not_op_false = {"not": {"eq": [1, 1]}}

and_true = {"and": [{"eq": [1, 1]},{"eq": [2, 2]}]}
and_false = {"and": [{"eq": [1, 2]},{"eq": [2, 2]}]}

or_true = {"or": [{"eq": [1, 1]},{"eq": [1, 2]}]}
or_false = {"or": [{"eq": [1, 2]},{"eq": [1, 2]}]}

xor_true = {"xor": [{"eq": [1, 1]},{"eq": [1, 2]}]}
xor_false1 = {"xor": [{"eq": [1, 2]},{"eq": [1, 2]}]}
xor_false2 = {"xor": [{"eq": [1, 1]},{"eq": [1, 1]}]}

nand_true = {"nand": [{"eq": [1, 2]},{"eq": [2, 2]}]}
nand_false = {"nand": [{"eq": [1, 1]},{"eq": [2, 2]}]}

nor_true = {"nor": [{"eq": [1, 2]},{"eq": [1, 2]}]}
nor_false1 = {"nor": [{"eq": [1, 1]},{"eq": [1, 2]}]}
nor_false2 = {"nor": [{"eq": [1, 1]},{"eq": [1, 1]}]}

xnor_true1 = {"xnor": [{"eq": [1, 2]},{"eq": [1, 2]}]}
xnor_true2 = {"xnor": [{"eq": [1, 1]},{"eq": [1, 1]}]}
xnor_false = {"xnor": [{"eq": [1, 1]},{"eq": [1, 2]}]}

in_true = {"in": [1, [1,2,3]]}
in_false = {"in": [1, [2,2,3]]}

nested_and_true = {
    "and": [
        {
            "and": [
                {"eq": [2, 2]},
                {"eq": [2, 2]}
            ]
        },
        {"eq": [2, 2]}
    ]
}

nested_and_false = {
    "and": [
        {
            "and": [
                {"eq": [1, 2]},
                {"eq": [2, 2]}
            ]
        },
        {"eq": [2, 2]}
    ]
}

nested_and_or_true = {
    "and": [
        {
            "or": [
                {"eq": [2, 2]},
                {"eq": [1, 2]}
            ]
        },
        {"eq": [2, 2]}
    ]
}

nested_and_or_false = {
    "and": [
        {
            "or": [
                {"eq": [1, 2]},
                {"eq": [1, 2]}
            ]
        },
        {"eq": [2, 2]}
    ]
}
