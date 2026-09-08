# `TLVDS_IOBUF` on GW5AST-138C

**Adjudicated: `restored`.** The full reasoning, the vendor's own output and
the scope of the claim are in `adjudication.md`, which is the artefact `V14`
asserts for `S11`; this file is the row.

| point | primitive | level | verdict | cells / attrs / conns | decode c1 / c2 |
|---|---|---|---|---|---|
| `tlvds-iobuf` | `TLVDS_IOBUF` | `E1` | ok | 0 / 0 / 0 | ok / ok |

**1 oracle run** (`p3-tlvds-iobuf`, ledger cumulative 93/140). The open half
was rebuilt once after the chipdb fix at no run cost
(`tools/redo_open_half.py`).

The design is `diff_io_iobuf`, a one-point shape rather than a seventh point
of `diff_io`: `diff_io` must stay free of the type until the adjudication
lands, and a one-point shape is what lets the batch spend exactly one run on
the question.
