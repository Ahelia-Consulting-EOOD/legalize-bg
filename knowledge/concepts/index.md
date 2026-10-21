# Concepts

* [How the reasoning run reads and audits legal text: unit of work, model choice, checks](hub-reading-architecture.md) - Read per provision, return pointers into custom content blocks and edit operations, verify completeness by string equality, and choose the model tier by cost, since the checks bound the omission errors whatever the tier.
* [Reading architecture for the reasoning run](reading-architecture.md) - The reasoning run reads one provision at a time, returns block-index citations and edit operations, and a script assembles and checks the text; model tiers are chosen by the check's pass rate per block.

# Up

* [Bundle index](../index.md)
