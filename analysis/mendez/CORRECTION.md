# Correction to Finding 2 (hay coverage) — verified by the parent session

## What the finding claimed

> "Ranked by farms, hay is #1: 612,946 farms (32.3% of all US farms), 47.2M acres —
> **zero published chemical-use values in 36 years**."

## What is actually in the record

That is wrong as literally stated, and the error is a join artifact of exactly the
kind this project keeps hitting. The Census of Agriculture names the commodity
`HAY` (and `HAYLAGE` separately); the Agricultural Chemical Use Program names it
**`HAY & HAYLAGE`**. Matching `COMMODITY_DESC` exactly across the two products
finds no counterpart and reads as total absence.

`HAY & HAYLAGE` does appear in the chemical-use record:

- **302 rows** under `DOMAIN_DESC = CHEMICAL`
- in **3 years of 36** — 2013, 2018, 2023
- `STATISTICCAT_DESC` is **`TREATED` only** — acres and operations

## The corrected claim, which is stronger

Every one of those 302 rows carries `DOMAINCAT_DESC = "CHEMICAL: (TOTAL)"`.
**Not one names an active ingredient.** There is no compound, no application
rate, no applications-per-season — only "this many acres were treated with
something," three times in thirty-six years.

So the precise statement is:

> The most widely grown crop in the United States by farm count — hay, on
> 612,946 farms, 32.3% of all US farms — has **never had a single named
> pesticide measured on it** by the federal chemical-use programme. It has
> aggregate acres-treated in 3 of 36 years and nothing else.

This is not unique to hay. Of the 102 commodities with any chemical-use record,
**94 have at least one named active ingredient and 8 never do**:

`HAY & HAYLAGE`, `PASTURELAND`, `ORCHARDS`, `BERRY TOTALS`, `VEGETABLE TOTALS`,
`HORTICULTURE TOTALS`, `SMALL GRAINS`, `CROPS, OTHER`.

The pattern is legible: the aggregate-only commodities are the **catch-all and
perennial/forage categories** — the ones that do not decompose into a single
surveyed crop with a single rate table. The instrument resolves row-crop
monoculture and treats everything else as a residual bucket. That reading
supports the finding's own inverted-U result (coverage peaks at the corn–soybean
rotation) more directly than the original absence claim did.

## Method note for anyone re-running this

Do not join NASS products on `COMMODITY_DESC` string equality across programmes.
The Census and the Chemical Use Program use overlapping but non-identical
commodity vocabularies, and a miss reads as a zero rather than as a missing key.
Check `DOMAINCAT_DESC` too: an aggregate `(TOTAL)` row is presence in the table
but absence of measurement, and collapsing the two loses the distinction that
matters here.
